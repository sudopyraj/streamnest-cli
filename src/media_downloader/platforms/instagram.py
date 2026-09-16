"""Instagram platform specifics.

Only publicly accessible content is supported. Extraction goes through yt-dlp,
and any indication that content is private, login-gated or age-restricted is
translated into a clear, honest message — never a bypass.
"""

from __future__ import annotations

import re

# Substrings of yt-dlp/Instagram error text mapped to friendly explanations.
_PRIVATE_MARKERS = (
    "login",
    "private",
    "requested resource could not be found",
    "not authorized",
)
_RATE_LIMIT_MARKERS = ("429", "too many requests", "please wait")


class InstagramContentError(Exception):
    """Raised when Instagram content cannot be accessed legally/technically."""

    def __init__(self, message: str, *, private: bool = False, rate_limited: bool = False):
        super().__init__(message)
        self.private = private
        self.rate_limited = rate_limited


def interpret_error(original: str) -> InstagramContentError:
    """Turn a raw extractor error into an honest, actionable message."""
    lowered = original.lower()
    if any(marker in lowered for marker in _RATE_LIMIT_MARKERS):
        return InstagramContentError(
            "Instagram is rate-limiting requests from this network. "
            "Wait a few minutes and try again.",
            rate_limited=True,
        )
    if any(marker in lowered for marker in _PRIVATE_MARKERS):
        return InstagramContentError(
            "This Instagram content is private or requires login. "
            "Private content is not supported and will not be bypassed.",
            private=True,
        )
    if "not found" in lowered or "404" in lowered:
        return InstagramContentError(
            "This Instagram post no longer exists or has been removed."
        )
    return InstagramContentError(
        "Instagram could not serve this content. It may be private, "
        "removed, or region-restricted."
    )


def is_supported_media(url: str) -> bool:
    """Whether the URL points at a public post/reel/IGTV media page."""
    return bool(re.search(r"instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+", url))
