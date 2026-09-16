"""Core download engine.

Wraps yt-dlp with: friendly error translation, Rich progress, FFmpeg-aware
merging, audio extraction, subtitle download/embed, bounded concurrency for
playlists, disk-space guards and history recording.
"""

from __future__ import annotations

import glob as _glob
import logging
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

import yt_dlp
from rich.console import Console

from . import formats as fmt
from .config import Config
from .database import HistoryDB
from .ffmpeg import find_ffmpeg, install_guidance
from .platforms import detect_platform
from .platforms import instagram as insta
from .platforms.youtube import entry_url as yt_entry_url
from .progress import ProgressReporter
from .utils import clamp, human_size

log = logging.getLogger("media_downloader.downloader")


# ----------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------

class DownloadError(Exception):
    """A user-facing download failure with a readable reason and next step."""

    def __init__(self, message: str, reason: str = "", hint: str = ""):
        super().__init__(message)
        self.message = message
        self.reason = reason
        self.hint = hint

    def render(self, console: Console) -> None:
        console.print(f"[bold red]✗ {self.message}[/]")
        if self.reason:
            console.print(f"\n[bold]Reason:[/]\n{self.reason}")
        if self.hint:
            console.print(f"\n[bold]Try:[/]\n{self.hint}")


_ERROR_PATTERNS: list[tuple[str, str, str, str]] = [
    (
        r"is private|private video|private account|requested resource could not be found",
        "Private media",
        "This content is private or requires an authenticated session, which this "
        "tool does not perform.",
        "Only publicly accessible media can be downloaded.",
    ),
    (
        r"login|sign in|log in|cookies|authentication|not logged in|rate.?browse",
        "Login required",
        "The platform requires an account for this content.",
        "Private or login-gated content is not supported by design.",
    ),
    (
        r"429|too many requests|rate.?limit",
        "Rate limited",
        "The platform is temporarily refusing requests from this network.",
        "Wait a few minutes, then try again.",
    ),
    (
        r"video (?:is )?unavailable|unavailable|has been removed|removed by|404|"
        r"does not exist|no longer",
        "Media unavailable",
        "The media was removed, is region-blocked, or never existed.",
        "Double-check the URL, or try another one.",
    ),
    (
        r"unsupported url",
        "Unsupported URL",
        "The URL points to something the extraction engine cannot handle.",
        "Use a YouTube video, Shorts, playlist, or a public Instagram "
        "post/reel URL.",
    ),
    (
        r"no video formats|requested format is not available|format .*not available|"
        r"no formats found",
        "Format unavailable",
        "The requested format is no longer available for this media.",
        'media-dl "URL" --list-formats',
    ),
    (
        r"unable to download|connection|timed out|network|temporary failure|"
        r"name or service not known|getaddrinfo",
        "Network error",
        "The request could not reach the platform, or the connection was "
        "interrupted.",
        "Check your internet connection and try again.",
    ),
    (
        r"ffmpeg|ffprobe",
        "FFmpeg missing",
        "Merging or converting media requires FFmpeg, which was not found.",
        "Install FFmpeg (see the guidance below), then retry.",
    ),
]


def _translate_error(
    exc: BaseException, url: str, platform: str
) -> DownloadError:
    original = str(exc)
    log.debug("Extraction error: %s", original)

    if platform == "Instagram":
        insta_error = insta.interpret_error(original)
        return DownloadError(
            "Instagram download failed",
            str(insta_error),
            "Only public posts, reels and IGTV content can be downloaded.",
        )

    for pattern, message, reason, hint in _ERROR_PATTERNS:
        if re.search(pattern, original, re.IGNORECASE):
            return DownloadError(message, reason, hint)

    if "postprocessing" in original.lower():
        return DownloadError(
            "Post-processing failed",
            "FFmpeg reported an error while merging or converting.",
            "Install or update FFmpeg, then retry the download.",
        )
    return DownloadError(
        "Download failed",
        original[:400] or "The download engine reported an unknown error.",
        "Run with --debug for the full technical details.",
    )


def _translate_oserror(exc: OSError) -> DownloadError:
    text = str(exc).lower()
    if "no space" in text:
        return DownloadError(
            "Disk full",
            "There is not enough free space to complete the download.",
            "Free up disk space or choose a smaller format.",
        )
    if "permission" in text or "read-only" in text:
        return DownloadError(
            "Permission denied",
            f"The download directory is not writable: {exc}",
            "Choose another directory with --output, or fix the permissions.",
        )
    return DownloadError("File system error", str(exc), "")


# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------

@dataclass
class DownloadResult:
    url: str
    title: str
    platform: str
    format_desc: str = ""
    resolution: str = ""
    filepath: str = ""
    file_size: Optional[int] = None


def is_playlist(info: dict[str, Any]) -> bool:
    return info.get("_type") == "playlist" or bool(info.get("entries"))


class _YtdlpLogger:
    """Route yt-dlp output into our logging instead of raw stdout."""

    def debug(self, msg: str, *args) -> None:
        if msg.startswith("[debug]") or log.isEnabledFor(logging.DEBUG):
            log.debug(msg % args if args else msg)

    def info(self, msg: str, *args) -> None:
        log.info(msg % args if args else msg)

    def warning(self, msg: str, *args) -> None:
        log.warning(msg % args if args else msg)

    def error(self, msg: str, *args) -> None:
        log.error(msg % args if args else msg)


# ----------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------

class MediaDownloader:
    def __init__(
        self,
        config: Config,
        console: Console,
        db: Optional[HistoryDB] = None,
        debug: bool = False,
    ):
        self.config = config
        self.console = console
        self.db = db
        self.debug = debug
        self.ffmpeg_path = find_ffmpeg()

    # ------------------------------------------------------------------
    @property
    def ffmpeg_available(self) -> bool:
        return self.ffmpeg_path is not None

    def _out_dir(self, override: Optional[str] = None) -> Path:
        if override:
            path = Path(override).expanduser()
            if not path.is_absolute():
                path = Path.cwd() / path
        else:
            path = self.config.resolved_download_dir()
        return path

    def _base_opts(self, out_dir: Path) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "logger": _YtdlpLogger(),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "outtmpl": {"default": self.config.filename_template},
            "paths": {"home": str(out_dir)},
            "windowsfilenames": True,
            "continuedl": True,  # resume .part files
            "retries": 3,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": clamp(
                self.config.max_concurrent_downloads, 1, 8
            ),
            "overwrites": bool(self.config.overwrite_existing_files),
        }
        if self.ffmpeg_path:
            opts["ffmpeg_location"] = self.ffmpeg_path
        return opts

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze(self, url: str) -> dict[str, Any]:
        """Fetch metadata (flat for playlists) without downloading."""
        platform, url = detect_platform(url)
        opts = self._base_opts(self._out_dir())
        opts.update({"skip_download": True, "extract_flat": "in_playlist"})
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            raise _translate_error(exc, url, platform) from exc
        except OSError as exc:
            raise _translate_oserror(exc) from exc
        if not info:
            raise DownloadError(
                "Could not retrieve media information",
                "The extraction engine returned no data for this URL.",
                "Verify the URL and your internet connection.",
            )
        info["_platform"] = platform
        return info

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------
    def download_media(
        self,
        url: str,
        *,
        info: Optional[dict[str, Any]] = None,
        selector: str = "bestvideo+bestaudio/best",
        container: Optional[str] = None,
        max_size_mb: Optional[float] = None,
        out_dir: Optional[str] = None,
        subtitles: Optional[Sequence[str]] = None,
        embed_subtitles: bool = False,
        reporter: Optional[ProgressReporter] = None,
        show_stages: bool = True,
    ) -> DownloadResult:
        """Download a single video/media item."""
        platform, url = detect_platform(url)
        out = self._out_dir(out_dir)

        if info is None or is_playlist(info):
            info = self.analyze(url)
        if is_playlist(info):
            raise DownloadError(
                "This is a playlist",
                "Use the playlist download flow for playlists.",
                'media-dl "PLAYLIST_URL"',
            )

        if "+" in selector and not self.ffmpeg_available:
            raise DownloadError(
                "FFmpeg was not found",
                "Merging separate video and audio streams requires FFmpeg.",
                install_guidance(_host_platform()),
            )

        fmt_list = fmt.build_format_list(info)
        self._check_disk_space(out, self._estimate_size(fmt_list))

        opts = self._base_opts(out)
        opts.update(
            {
                "noplaylist": True,
                "format": selector,
                "ignoreerrors": False,
            }
        )
        if container in ("mp4", "webm"):
            opts["merge_output_format"] = container
        if max_size_mb:
            opts["max_filesize"] = int(max_size_mb * 1024 * 1024)
        if subtitles:
            opts.update(
                {
                    "writesubtitles": True,
                    "subtitleslangs": list(subtitles),
                    "subtitlesformat": "srt/best",
                }
            )
        postprocessors: list[dict[str, Any]] = []
        if embed_subtitles and subtitles:
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})
        if postprocessors:
            opts["postprocessors"] = postprocessors

        return self._run_download(
            url,
            opts,
            platform=platform,
            out_dir=out,
            reporter=reporter,
            show_stages=show_stages,
            format_desc=container or "original",
        )

    def download_audio(
        self,
        url: str,
        *,
        info: Optional[dict[str, Any]] = None,
        max_bitrate: Optional[int] = None,
        codec: str = "original",
        quality: Optional[str] = None,
        out_dir: Optional[str] = None,
        reporter: Optional[ProgressReporter] = None,
        show_stages: bool = True,
    ) -> DownloadResult:
        """Download audio only, optionally converting to mp3/m4a/opus."""
        platform, url = detect_platform(url)
        out = self._out_dir(out_dir)

        if codec not in ("original", "mp3", "m4a", "opus"):
            raise DownloadError(
                "Unsupported audio format",
                f"{codec!r} is not one of mp3, m4a, opus, original.",
                "Choose mp3, m4a, opus or original.",
            )
        if codec != "original" and not self.ffmpeg_available:
            raise DownloadError(
                "FFmpeg was not found",
                f"Converting audio to {codec.upper()} requires FFmpeg.",
                install_guidance(_host_platform()),
            )

        if info is None or is_playlist(info):
            info = self.analyze(url)
        if is_playlist(info):
            raise DownloadError(
                "This is a playlist",
                "Use the playlist download flow for playlists.",
                'media-dl "PLAYLIST_URL"',
            )

        fmt_list = fmt.build_format_list(info)
        self._check_disk_space(out, self._estimate_size(fmt_list))

        opts = self._base_opts(out)
        opts.update(
            {
                "noplaylist": True,
                "format": fmt.audio_selector(max_bitrate),
                "ignoreerrors": False,
            }
        )
        if codec != "original":
            pp: dict[str, Any] = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
            }
            if quality:
                pp["preferredquality"] = quality
            opts["postprocessors"] = [pp]

        return self._run_download(
            url,
            opts,
            platform=platform,
            out_dir=out,
            reporter=reporter,
            show_stages=show_stages,
            format_desc=f"audio/{codec}" + (f" {quality}kbps" if quality else ""),
        )

    def download_playlist(
        self,
        url: str,
        *,
        selector: str = "bestvideo+bestaudio/best",
        container: Optional[str] = None,
        playlist_items: Optional[Sequence[int]] = None,
        out_dir: Optional[str] = None,
    ) -> list[DownloadResult]:
        """Download a playlist (all items, or a 1-based selection)."""
        platform, url = detect_platform(url)

        info = self.analyze(url)
        if not is_playlist(info):
            # Single media: just download it.
            result = self.download_media(
                url, selector=selector, container=container, out_dir=out_dir
            )
            return [result]

        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise DownloadError(
                "Empty playlist",
                "The playlist contains no downloadable entries.",
            )

        if playlist_items:
            wanted = sorted({i for i in playlist_items if 1 <= i <= len(entries)})
            selected = [entries[i - 1] for i in wanted]
        else:
            selected = entries

        jobs: list[tuple[str, str]] = []
        for idx, entry in enumerate(selected, start=1):
            link = yt_entry_url(entry) or entry.get("url")
            if not link:
                self.console.print(
                    f"[yellow]⚠ Skipping entry {idx}: no resolvable URL[/]"
                )
                continue
            jobs.append((link, entry.get("title") or f"Item {idx}"))

        workers = clamp(self.config.max_concurrent_downloads, 1, len(jobs) or 1)
        results: list[DownloadResult] = []
        failures: list[tuple[str, DownloadError]] = []

        with ProgressReporter(self.console) as rep:
            rep.add_overall(f"Playlist: 0 / {len(jobs)}", len(jobs))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(
                        self.download_media,
                        link,
                        selector=selector,
                        container=container,
                        out_dir=out_dir,
                        reporter=rep,
                        show_stages=False,
                    ): (link, title)
                    for link, title in jobs
                }
                for future in as_completed(futures):
                    link, title = futures[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            self.console.print(
                                f"[green]✓[/] {result.title or title}"
                            )
                    except DownloadError as exc:
                        failures.append((link, exc))
                    finally:
                        rep.advance_overall(
                            f"Playlist: {len(results) + len(failures)} / {len(jobs)}"
                        )

        self.console.print(
            f"\n[bold]Playlist complete:[/] {len(results)} / {len(jobs)} "
            f"downloaded"
            + (f", [red]{len(failures)} failed[/]" if failures else "")
        )
        for link, exc in failures[:5]:
            self.console.print(f"  [red]✗[/] {exc.message}: {link}")
        if len(failures) > 5:
            self.console.print(f"  [dim]… and {len(failures) - 5} more failures[/]")
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _run_download(
        self,
        url: str,
        opts: dict[str, Any],
        *,
        platform: str,
        out_dir: Path,
        reporter: Optional[ProgressReporter],
        show_stages: bool,
        format_desc: str,
    ) -> DownloadResult:
        own_reporter = reporter is None
        rep = reporter or ProgressReporter(self.console)
        if own_reporter:
            rep.__enter__()
        try:
            opts["progress_hooks"] = [rep.hook("Downloading")]
            if show_stages:
                opts["postprocessor_hooks"] = [
                    rep.make_postprocessor_hook(self.console)
                ]
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                except yt_dlp.utils.DownloadError as exc:
                    raise _translate_error(exc, url, platform) from exc
                except OSError as exc:
                    raise _translate_oserror(exc) from exc
                if info is None:
                    raise DownloadError(
                        "Download failed",
                        "The extraction engine returned no data.",
                        "Run with --debug for details.",
                    )
                return self._collect_result(
                    info, url, platform, format_desc, out_dir
                )
        finally:
            if own_reporter:
                rep.__exit__()

    def _collect_result(
        self,
        info: dict[str, Any],
        url: str,
        platform: str,
        format_desc: str,
        out_dir: Path,
    ) -> DownloadResult:
        title = info.get("title") or "unknown title"
        filepath = ""
        size: Optional[int] = None
        requested = info.get("requested_downloads") or []
        if requested:
            filepath = requested[0].get("filepath") or ""
            if filepath and os.path.exists(filepath):
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    size = None
        if not filepath:
            filepath = self._locate_file(out_dir, info)

        resolution = ""
        if info.get("height"):
            resolution = f"{info['height']}p"
        elif format_desc.startswith("audio"):
            resolution = "audio"

        if self.db is not None and filepath:
            self.db.add(
                url=url,
                title=title,
                platform=platform,
                format_desc=format_desc,
                resolution=resolution,
                file_path=filepath,
                file_size=size,
            )
        return DownloadResult(
            url=url,
            title=title,
            platform=platform,
            format_desc=format_desc,
            resolution=resolution,
            filepath=filepath,
            file_size=size,
        )

    def _locate_file(self, out_dir: Path, info: dict[str, Any]) -> str:
        """Fallback: find the newest media file written for this download."""
        title = info.get("title") or ""
        patterns = [
            f"{_glob.escape(title[:40])}*.*",
        ]
        media_exts = {
            ".mp4", ".mkv", ".webm", ".m4a", ".mp3", ".opus", ".ogg", ".srt",
            ".jpg", ".jpeg", ".png", ".webp", ".vtt",
        }
        candidates: list[Path] = []
        for pattern in patterns:
            for path in out_dir.glob(pattern):
                if path.suffix.lower() in media_exts and not path.name.endswith(
                    (".part", ".ytdl", ".temp")
                ):
                    candidates.append(path)
        if not candidates:
            return ""
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        return str(newest)

    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_size(fmt_list: list[fmt.FormatInfo]) -> Optional[int]:
        """Conservative size estimate for a disk-space guard."""
        video = [f for f in fmt_list if f.has_video]
        audio = fmt.best_audio(fmt_list)
        total = 0
        if video:
            biggest = max(f.size_bytes() or 0 for f in video)
            total += biggest
        elif audio and audio.size_bytes():
            total += audio.size_bytes()
        else:
            return 50 * 1024 * 1024  # assume at least 50 MB when unknown
        if audio and audio.size_bytes() and video:
            total += audio.size_bytes()
        return total or (50 * 1024 * 1024)

    def _check_disk_space(self, out_dir: Path, needed: Optional[int]) -> None:
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise _translate_oserror(exc) from exc
        try:
            free = shutil.disk_usage(out_dir).free
        except OSError:
            return
        if needed and free < needed:
            raise DownloadError(
                "Not enough disk space",
                f"{human_size(free)} free, but this download needs roughly "
                f"{human_size(needed)}.",
                "Free up disk space or choose a smaller format.",
            )

    # ------------------------------------------------------------------
    # Resume support
    # ------------------------------------------------------------------
    @staticmethod
    def find_partials(out_dir: Path, title: str) -> list[Path]:
        """Find interrupted partial downloads (.part/.ytdl) for a title."""
        if not title:
            return []
        prefix = _glob.escape(title[:40])
        found: list[Path] = []
        for path in out_dir.glob(f"{prefix}*"):
            if path.name.endswith((".part", ".ytdl", ".part-Frag*")) or ".part" in path.name:
                found.append(path)
        return sorted(found)

    @staticmethod
    def partial_progress(partials: list[Path]) -> tuple[int, int]:
        """Rough (downloaded_bytes, total_bytes) across partial files."""
        done = 0
        total = 0
        for path in partials:
            done += path.stat().st_size
            stem = path.name[: -len(".part")] if path.name.endswith(".part") else path.name
            sibling = path.with_name(stem)
            if sibling.exists() and sibling.is_file():
                total += sibling.stat().st_size
        return done, total

    @staticmethod
    def remove_partials(partials: list[Path]) -> None:
        for path in partials:
            try:
                path.unlink()
            except OSError:
                log.debug("Could not remove partial file %s", path)


def _host_platform() -> str:
    return sys.platform if sys.platform != "darwin" else "macos"
