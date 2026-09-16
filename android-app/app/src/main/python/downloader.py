import json
from pathlib import Path

import yt_dlp


def resolve(url: str, quality: str) -> str:
    height = {"best": None, "1080p": 1080, "720p": 720, "480p": 480}.get(quality)
    video = "bestvideo[ext=mp4]"
    audio = "bestaudio[ext=m4a]"
    if height:
        video += f"[height<={height}]"
    options = {"quiet": True, "no_warnings": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist" or info.get("entries"):
        raise ValueError("Playlists are not supported in standalone Android mode yet.")
    requested = info.get("requested_formats") or []
    if not requested:
        selector = f"{video}+{audio}/{video}/best"
        with yt_dlp.YoutubeDL({**options, "format": selector}) as ydl:
            info = ydl.extract_info(url, download=False)
        requested = info.get("requested_formats") or []
    if requested:
        streams = [{"url": item["url"], "kind": "video" if item.get("vcodec") != "none" else "audio"}
                   for item in requested if item.get("url")]
    elif info.get("url"):
        streams = [{"url": info["url"], "kind": "video"}]
    else:
        raise ValueError("No downloadable public format was found.")
    return json.dumps({
        "title": info.get("title") or "streamnest-download",
        "streams": streams,
    })
