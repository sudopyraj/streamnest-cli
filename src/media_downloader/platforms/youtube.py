"""YouTube platform specifics: URL shaping, playlist entry handling, subtitles."""

from __future__ import annotations

from typing import Any, Optional

WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
SHORTS_URL = "https://www.youtube.com/shorts/{video_id}"


def entry_url(entry: dict[str, Any]) -> Optional[str]:
    """Normalise a flat playlist entry into a canonical video URL."""
    url = entry.get("url") or entry.get("webpage_url")
    if url and url.startswith("http"):
        return url
    video_id = entry.get("id")
    if video_id and str(video_id).startswith(("http", "yt")):
        return str(video_id) if str(video_id).startswith("http") else None
    if video_id:
        return WATCH_URL.format(video_id=video_id)
    return None


def subtitle_languages(info: dict[str, Any]) -> list[tuple[str, bool]]:
    """Return available subtitle languages as (language, is_automatic)."""
    languages: list[tuple[str, bool]] = []
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    for lang in manual:
        if manual.get(lang):
            languages.append((lang, False))
    for lang in auto:
        if auto.get(lang) and not manual.get(lang):
            languages.append((lang, True))
    # English first, then alphabetical — a stable, sensible ordering.
    languages.sort(key=lambda item: (item[0] != "en", item[0]))
    return languages
