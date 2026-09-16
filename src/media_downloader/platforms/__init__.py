"""Platform detection helpers shared by the CLI and the download engine."""

from __future__ import annotations

from ..security import (
    PLATFORM_INSTAGRAM,
    PLATFORM_YOUTUBE,
    UnsupportedPlatformError,
    validate_url,
)

__all__ = [
    "detect_platform",
    "PLATFORM_YOUTUBE",
    "PLATFORM_INSTAGRAM",
    "UnsupportedPlatformError",
]


def detect_platform(url: str) -> tuple[str, str]:
    """Validate a URL and return ``(platform, normalized_url)``."""
    return validate_url(url)
