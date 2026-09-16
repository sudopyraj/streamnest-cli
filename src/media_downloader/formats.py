"""Format discovery, labelling and selection.

Everything in this module derives from the *actual* metadata returned by the
extraction engine — we never invent or assume qualities that a source does not
offer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .utils import human_size

# yt-dlp reports codecs as e.g. "avc1.640028" / "mp4a.40.2" / "vp9" / "opus".
_PRETTY_CODECS = {
    "avc": "H.264",
    "h264": "H.264",
    "hevc": "H.265",
    "h265": "H.265",
    "vp9": "VP9",
    "vp09": "VP9",
    "vp8": "VP8",
    "av01": "AV1",
    "mp4a": "AAC",
    "opus": "Opus",
    "vorbis": "Vorbis",
    "ec3": "EAC3",
    "ac3": "AC3",
    "flac": "FLAC",
}


def pretty_codec(codec: Optional[str]) -> str:
    if not codec or codec == "none":
        return "—"
    head = codec.split(".")[0].lower()
    if head in _PRETTY_CODECS:
        return _PRETTY_CODECS[head]
    # codec tags arrive as e.g. "avc1", "vp09" — match by prefix
    for key, label in _PRETTY_CODECS.items():
        if head.startswith(key):
            return label
    return codec.split(".")[0].upper()


@dataclass
class FormatInfo:
    """A single downloadable stream from the source."""

    format_id: str
    media_type: str  # "video" (may include audio) or "audio"
    ext: str = "unknown"
    height: Optional[int] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    abr: Optional[float] = None
    duration: Optional[float] = None
    format_note: str = ""

    # ------------------------------------------------------------------
    @property
    def has_video(self) -> bool:
        return bool(self.vcodec and self.vcodec != "none")

    @property
    def has_audio(self) -> bool:
        return bool(self.acodec and self.acodec != "none")

    def size_bytes(self) -> Optional[int]:
        """Best-known size, or a bandwidth-based estimate when exact is absent."""
        if self.filesize:
            return int(self.filesize)
        if self.filesize_approx:
            return int(self.filesize_approx)
        if self.tbr and self.duration:
            return int(self.tbr * 1000 * self.duration / 8)
        return None

    def is_estimate(self) -> bool:
        return not (self.filesize or self.filesize_approx)

    def size_label(self) -> str:
        size = self.size_bytes()
        if size is None:
            return "unknown"
        prefix = "~" if self.is_estimate() else ""
        return prefix + human_size(size)

    def resolution_label(self) -> str:
        if self.height:
            tag = " 4K" if self.height == 2160 else ""
            return f"{self.height}p{tag}"
        return "—"

    def fps_label(self) -> str:
        if self.fps:
            return f"{int(round(self.fps))} FPS"
        return "—"

    def codec_label(self) -> str:
        if self.media_type == "audio":
            return pretty_codec(self.acodec)
        if self.has_video and self.has_audio:
            return f"{pretty_codec(self.vcodec)}+{pretty_codec(self.acodec)}"
        return pretty_codec(self.vcodec)

    def audio_bitrate_label(self) -> str:
        rate = self.abr or (self.tbr if self.media_type == "audio" else None)
        return f"~{int(round(rate))} kbps" if rate else "unknown"


_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}


def _storyboard(f: dict[str, Any]) -> bool:
    if f.get("ext") in ("mhtml", "mhtml_v2"):
        return True
    note = (f.get("format_note") or "").lower()
    return "storyboard" in note or "sb" in note.split()


def build_format_list(info: dict[str, Any]) -> list[FormatInfo]:
    """Build a deduplicated, sorted list of streams from extracted metadata."""
    raw_formats = info.get("formats") or []
    if not raw_formats:
        # Single-format media: synthesise one entry from the top-level info.
        raw_formats = [info]

    result: list[FormatInfo] = []
    seen: set[str] = set()
    duration = info.get("duration")

    for f in raw_formats:
        if not isinstance(f, dict) or _storyboard(f):
            continue
        vcodec = f.get("vcodec") or "none"
        acodec = f.get("acodec") or "none"
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        ext = str(f.get("ext") or "unknown").lower()
        is_image = not has_video and not has_audio and ext in _IMAGE_EXTS
        if not has_video and not has_audio and not is_image:
            continue

        fid = str(f.get("format_id") or f.get("id") or "")
        if not fid or fid in seen:
            continue
        seen.add(fid)

        height = f.get("height")
        fps = f.get("fps")
        try:
            height = int(height) if height else None
            fps = float(fps) if fps else None
        except (TypeError, ValueError):
            height, fps = None, None

        result.append(
            FormatInfo(
                format_id=fid,
                media_type="image" if is_image else ("video" if has_video else "audio"),
                ext=str(f.get("ext") or "unknown"),
                height=height,
                fps=fps,
                vcodec=vcodec,
                acodec=acodec,
                filesize=f.get("filesize"),
                filesize_approx=f.get("filesize_approx"),
                tbr=f.get("tbr"),
                abr=f.get("abr"),
                duration=duration if not f.get("duration") else f.get("duration"),
                format_note=str(f.get("format_note") or ""),
            )
        )

    videos = [f for f in result if f.media_type == "video"]
    audios = [f for f in result if f.media_type == "audio"]
    images = [f for f in result if f.media_type == "image"]
    videos.sort(key=lambda f: ((f.height or 0), (f.fps or 0), (f.tbr or 0)), reverse=True)
    audios.sort(key=lambda f: (f.abr or f.tbr or 0), reverse=True)
    return videos + audios + images


def best_audio(formats: list[FormatInfo]) -> Optional[FormatInfo]:
    audios = [f for f in formats if f.media_type == "audio" and f.has_audio]
    if not audios:
        for f in formats:  # progressive formats that carry audio
            if f.has_audio:
                audios.append(f)
    return audios[0] if audios else None


def best_audio_bitrate(formats: list[FormatInfo]) -> Optional[int]:
    best = best_audio(formats)
    if not best:
        return None
    rate = best.abr or best.tbr
    return int(round(rate)) if rate else None


# ----------------------------------------------------------------------
# yt-dlp format selectors
# ----------------------------------------------------------------------

RESOLUTIONS = [2160, 1440, 1080, 720, 480, 360, 240]


def video_selector(
    height: Optional[int],
    container: str = "original",
    fps: Optional[float] = None,
) -> str:
    """Build a yt-dlp format selector honouring resolution, FPS and container.

    For MP4/WebM we prefer codec families that can be *remuxed* into the
    target container without re-encoding, and fall back to whatever exists.
    """
    h = f"[height<={height}]" if height else ""
    f = f"[fps<={int(fps)}]" if fps else ""
    if container == "mp4":
        return (
            f"bestvideo[vcodec^=avc1]{h}{f}+bestaudio[acodec^=mp4a]/"
            f"bestvideo{h}{f}+bestaudio/best{h}{f}"
        )
    if container == "webm":
        return (
            f"bestvideo[vcodec^=vp9]{h}{f}+bestaudio[acodec^=opus]/"
            f"bestvideo{h}{f}+bestaudio/best{h}{f}"
        )
    return f"bestvideo{h}{f}+bestaudio/best{h}{f}"


def audio_selector(max_bitrate: Optional[int]) -> str:
    if not max_bitrate:
        return "bestaudio/best"
    return f"bestaudio[abr<={max_bitrate}]/bestaudio/best"


SMART_MODES = {
    "best": lambda container: video_selector(None, container),
    "balanced": lambda container: video_selector(1080, container),
    "small": lambda container: video_selector(480, container),
}


def smart_selector(mode: str, container: str = "original") -> str:
    try:
        return SMART_MODES[mode](container)
    except KeyError:
        raise ValueError(
            f"Unknown mode {mode!r}. Use one of: best, balanced, small, custom."
        )


def formats_under_limit(
    formats: list[FormatInfo], limit_mb: float
) -> list[tuple[FormatInfo, int]]:
    """Return (video_format, estimated_total_bytes) pairs that fit a size cap.

    Size figures are estimates whenever the source does not publish exact
    numbers — the caller is expected to mark them as such.
    """
    limit_bytes = int(limit_mb * 1024 * 1024)
    best_snd = best_audio(formats)
    audio_size = (best_snd.size_bytes() if best_snd else None) or 0

    fitting: list[tuple[FormatInfo, int]] = []
    for fmt in formats:
        if not fmt.has_video:
            continue
        size = fmt.size_bytes()
        if size is None:
            continue  # do not guess when we have nothing to go on
        total = size + audio_size
        if total <= limit_bytes:
            fitting.append((fmt, total))
    return fitting


def resolution_choices(formats: list[FormatInfo]) -> list[int]:
    """Resolutions that actually exist in the source, highest first."""
    heights = sorted({f.height for f in formats if f.has_video and f.height}, reverse=True)
    return heights


def fps_choices(formats: list[FormatInfo]) -> list[float]:
    fps = sorted({f.fps for f in formats if f.has_video and f.fps}, reverse=True)
    return fps
