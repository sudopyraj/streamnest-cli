"""Security helpers: URL allow-listing, filename sanitisation and path safety.

Every URL is validated against an explicit allow-list of supported platforms
before anything is fetched. Filenames coming from remote metadata are treated
as untrusted input: they are sanitised and every final path is checked to be
inside the configured download directory.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

MAX_URL_LENGTH = 2048
MAX_FILENAME_LENGTH = 180

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

INSTAGRAM_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "m.instagram.com",
    "instagr.am",
    "www.instagr.am",
}

PLATFORM_YOUTUBE = "YouTube"
PLATFORM_INSTAGRAM = "Instagram"

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{6,16}$")


class SecurityError(Exception):
    """Base class for URL/filename safety violations."""


class InvalidURLError(SecurityError):
    """The URL is malformed."""


class UnsupportedPlatformError(SecurityError):
    """The URL points to a platform or resource we do not support."""


class UnsafePathError(SecurityError):
    """A filename/path would escape the download directory."""


def validate_url(raw_url: str) -> tuple[str, str]:
    """Validate a user-supplied URL.

    Returns ``(platform, normalized_url)``. Raises :class:`InvalidURLError` or
    :class:`UnsupportedPlatformError` for anything not on the allow-list.

    Only exact hostnames are accepted (no suffix tricks such as
    ``evil-youtube.com`` or ``youtube.com.evil.net``), which blocks SSRF via
    hostname confusion and arbitrary URL fetching.
    """
    if not raw_url or not raw_url.strip():
        raise InvalidURLError("Empty URL.")
    url = raw_url.strip()
    if len(url) > MAX_URL_LENGTH:
        raise InvalidURLError("URL is too long.")

    try:
        parts = urlsplit(url)
    except ValueError as exc:  # malformed percent-encodings etc.
        raise InvalidURLError(f"Malformed URL: {exc}") from exc

    if parts.scheme not in ("http", "https"):
        raise InvalidURLError("URL must start with http:// or https://")

    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise InvalidURLError("URL has no hostname.")
    if not parts.netloc and not host:
        raise InvalidURLError("URL has no hostname.")

    # Reject userinfo tricks like http://youtube.com@evil.example/
    if "@" in (parts.netloc or ""):
        raise InvalidURLError("URLs with embedded credentials are not accepted.")
    # IP-literal hosts are never supported platforms (blocks SSRF to
    # link-local metadata services, localhost, etc.)
    if host.startswith("[") or _is_ip_literal(host):
        raise UnsupportedPlatformError(
            "Only youtube.com and instagram.com URLs are supported."
        )

    path = parts.path or "/"

    if host in YOUTUBE_HOSTS:
        return PLATFORM_YOUTUBE, _validate_youtube_path(host, path, parts)
    if host in INSTAGRAM_HOSTS:
        return PLATFORM_INSTAGRAM, _validate_instagram_path(host, path, parts)

    raise UnsupportedPlatformError(
        "Only youtube.com and instagram.com URLs are supported."
    )


def _is_ip_literal(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host))


def _validate_youtube_path(host: str, path: str, parts) -> str:
    segments = [seg for seg in path.split("/") if seg]

    if host.endswith("youtu.be"):
        if len(segments) == 1 and _VIDEO_ID.match(segments[0]):
            return _normalize("https://youtu.be/" + segments[0])
        raise InvalidURLError("Expected a youtu.be/<video-id> URL.")

    if not segments:
        # bare domain — not a media URL
        raise InvalidURLError(
            "Please provide a full YouTube video, Shorts or playlist URL."
        )
    head = segments[0]
    if head == "watch":
        query = parts.query or ""
        if "v=" not in query:
            raise InvalidURLError("YouTube watch URL is missing its video ID (?v=...).")
        return _normalize(f"https://www.youtube.com/watch?{query}")
    if head in ("shorts", "embed", "live", "v") and len(segments) >= 2:
        if not _VIDEO_ID.match(segments[1]):
            raise InvalidURLError("YouTube URL contains an invalid video ID.")
        if head == "shorts":
            return _normalize(f"https://www.youtube.com/shorts/{segments[1]}")
        return _normalize(f"https://www.youtube.com/watch?v={segments[1]}")
    if head == "playlist":
        query = parts.query or ""
        if "list=" not in query:
            raise InvalidURLError("Playlist URL is missing its list ID (?list=...).")
        return _normalize(f"https://www.youtube.com/playlist?{query}")

    raise InvalidURLError(
        "Unsupported YouTube URL. Use a /watch, /shorts, /playlist or youtu.be link."
    )


def _validate_instagram_path(host: str, path: str, parts) -> str:
    segments = [seg for seg in path.split("/") if seg]
    if not segments:
        raise InvalidURLError("Please provide a full Instagram post, reel or TV URL.")
    head = segments[0]
    if head in ("p", "reel", "reels", "tv"):
        if len(segments) < 2 or not re.fullmatch(r"[A-Za-z0-9_-]{5,20}", segments[1]):
            raise InvalidURLError("Instagram URL contains an invalid media code.")
        kind = "reel" if head in ("reel", "reels") else head
        return _normalize(f"https://www.instagram.com/{kind}/{segments[1]}/")
    if head == "stories":
        raise UnsupportedPlatformError(
            "Instagram Stories require an authenticated session and are not supported."
        )
    if head.startswith("?") or head in ("explore", "accounts", "login", "direct"):
        raise UnsupportedPlatformError(
            "Only public Instagram posts, reels and IGTV URLs are supported."
        )
    raise InvalidURLError(
        "Unsupported Instagram URL. Use /p/<code>, /reel/<code> or /tv/<code>."
    )


def _normalize(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, parts.query, ""))


# --------------------------------------------------------------------------
# Filename sanitisation
# --------------------------------------------------------------------------

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """Return a filename safe on Linux, macOS and Windows.

    Removes characters that are invalid on any of the three platforms, control
    characters, leading dots (hidden files), ``..`` traversal fragments and
    Windows reserved device names. The result is truncated to a safe length
    while preserving the extension.
    """
    if not name or not name.strip():
        return "download"

    name = unicodedata.normalize("NFKC", name)
    name = _ILLEGAL_CHARS.sub(" ", name)
    # Drop traversal fragments and dot-runs that survive char removal.
    name = re.sub(r"\.{2,}", ".", name)
    # Collapse whitespace runs.
    name = re.sub(r"\s+", " ", name).strip(" .\t")
    if not name:
        return "download"

    # Windows reserved device names (with or without an extension).
    stem = name.split(".", 1)[0]
    if stem.upper() in _WINDOWS_RESERVED:
        name = "_" + name

    if len(name) <= max_length:
        return name

    # Truncate, but keep the extension intact.
    ext = ""
    if "." in name:
        name, ext = name.rsplit(".", 1)
        ext = "." + ext
    keep = max(1, max_length - len(ext))
    return name[:keep].rstrip(" .\t") + ext


def safe_join(base_dir: str | Path, filename: str) -> Path:
    """Join ``filename`` onto ``base_dir`` and verify the result stays inside it.

    Rejects path traversal (``../..``), absolute-path injection and any
    component that would escape the base directory, rather than silently
    rewriting it. Raises :class:`UnsafePathError` on any violation.
    """
    raw = str(filename).strip()
    if not raw:
        raise UnsafePathError("Empty filename.")
    if raw.startswith(("/", "\\")) or Path(raw).is_absolute() or raw.startswith("~"):
        raise UnsafePathError(
            f"Absolute paths are not allowed as filenames: {filename!r}"
        )
    parts = raw.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise UnsafePathError(
            f"Path traversal is not allowed: {filename!r}"
        )
    base = Path(base_dir).expanduser().resolve()
    clean = sanitize_filename(Path(raw).name)
    if not clean or clean in (".", ".."):
        raise UnsafePathError(f"Unsafe filename rejected: {filename!r}")
    target = (base / clean).resolve()
    if target != base and not target.is_relative_to(base):
        raise UnsafePathError(
            f"Path escapes the download directory: {filename!r}"
        )
    return target


def validate_output_template(template: str) -> str:
    """Validate a yt-dlp output filename template for path safety.

    Rejects path separators, ``..`` segments and absolute paths, while allowing
    yt-dlp field placeholders such as ``%(title)s.%(ext)s``.
    """
    if not template or not template.strip():
        raise SecurityError("Filename template is empty.")
    if len(template) > 300:
        raise SecurityError("Filename template is too long.")
    if "\\" in template or "/" in template:
        raise SecurityError(
            "Filename template must not contain path separators (/, \\)."
        )
    if ".." in template:
        raise SecurityError("Filename template must not contain '..'.")
    if template.strip().startswith("~"):
        raise SecurityError(
            "Filename template must be a bare filename pattern, not a path."
        )
    return template.strip()
