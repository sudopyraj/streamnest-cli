"""FFmpeg detection and safe execution.

FFmpeg is only ever invoked through yt-dlp or via subprocess argument lists —
never through a shell, and never by concatenating user input into a command
string.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

log = logging.getLogger("media_downloader.ffmpeg")

_EXTRA_LOCATIONS = [
    "/usr/local/bin/ffmpeg",
    "/usr/bin/ffmpeg",
    "/opt/homebrew/bin/ffmpeg",
    "/snap/bin/ffmpeg",
]


def find_ffmpeg() -> Optional[str]:
    """Locate an ffmpeg executable, or return None."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in _EXTRA_LOCATIONS:
        if Path(candidate).exists() and Path(candidate).is_file():
            return candidate
    return None


def find_ffprobe() -> Optional[str]:
    found = shutil.which("ffprobe")
    if not found:
        ffmpeg = find_ffmpeg()
        if ffmpeg:
            sibling = Path(ffmpeg).parent / "ffprobe"
            if sibling.exists():
                return str(sibling)
    return found


INSTALL_GUIDANCE = {
    "linux": (
        "  Debian/Ubuntu:  sudo apt install ffmpeg\n"
        "  Fedora:         sudo dnf install ffmpeg\n"
        "  Arch:           sudo pacman -S ffmpeg"
    ),
    "macos": (
        "  Homebrew:  brew install ffmpeg\n"
        "  MacPorts:  sudo port install ffmpeg"
    ),
    "windows": (
        "  winget install Gyan.FFmpeg\n"
        "  or download from https://ffmpeg.org/download.html and add it to PATH"
    ),
}


def install_guidance(platform_name: str) -> str:
    return INSTALL_GUIDANCE.get(platform_name, INSTALL_GUIDANCE["linux"])


def run_ffmpeg(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    """Run ffmpeg with an argument list (no shell, no string concatenation)."""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed.")
    cmd = [ffmpeg, *args]
    log.debug("Running: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
