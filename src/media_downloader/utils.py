"""Small shared helpers: human-readable sizes, durations and misc utilities."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def human_size(num_bytes: Optional[int | float]) -> str:
    """Format a byte count as a human-readable string. Never raises."""
    if num_bytes is None:
        return "—"
    try:
        size = float(num_bytes)
    except (TypeError, ValueError):
        return "—"
    if size < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def human_duration(seconds: Optional[int | float]) -> str:
    """Format seconds as H:MM:SS / MM:SS. Returns '—' when unknown."""
    if seconds is None:
        return "—"
    try:
        secs = int(seconds)
    except (TypeError, ValueError):
        return "—"
    if secs < 0:
        return "—"
    hours, remainder = divmod(secs, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_size_mb(value: str | float | int) -> float:
    """Parse a user-supplied megabyte value ('50', '50MB', 1.5) into a float."""
    if isinstance(value, (int, float)):
        mb = float(value)
    else:
        cleaned = str(value).strip().upper().replace(" ", "")
        match = re.fullmatch(r"([0-9]*\.?[0-9]+)(MB|MIB)?", cleaned)
        if not match:
            raise ValueError(f"Not a valid size: {value!r}")
        mb = float(match.group(1))
    if mb <= 0:
        raise ValueError("Size must be greater than zero")
    if mb > 1024 * 1024:  # 1 PB sanity cap
        raise ValueError("Size is unreasonably large")
    return mb


def parse_quality(value: str | int | None) -> Optional[int]:
    """Turn '1080p', '1080', 720 or 'best' into a pixel height (or None for best)."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("", "best", "max"):
        return None
    match = re.fullmatch(r"(\d{3,4})p?", text)
    if not match:
        raise ValueError(
            f"Unknown quality {value!r}. Use e.g. 720p, 1080p or 'best'."
        )
    height = int(match.group(1))
    if height < 120 or height > 4320:
        raise ValueError(f"Quality {value!r} is out of the supported range.")
    return height


def parse_index_list(text: str, maximum: int) -> list[int]:
    """Parse a selection like '1-5,7,10-12' into 1-based unique sorted indexes."""
    selected: set[int] = set()
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", chunk)
        if not match:
            raise ValueError(f"Invalid selection part: {chunk!r}")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if start < 1 or end < start:
            raise ValueError(f"Invalid range: {chunk!r}")
        if end > maximum:
            raise ValueError(f"Index {end} is out of range (1–{maximum}).")
        selected.update(range(start, end + 1))
    if not selected:
        raise ValueError("Nothing selected.")
    return sorted(selected)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
