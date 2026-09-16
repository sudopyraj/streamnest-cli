"""Integration-style tests for the download engine using a stubbed extractor.

These verify *our* wiring — progress hooks, postprocessor hooks, result
collection, history recording, FFmpeg requirement checks — without hitting
the network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yt_dlp
from rich.console import Console

from media_downloader.config import Config
from media_downloader.database import HistoryDB
from media_downloader.downloader import (
    DownloadError,
    MediaDownloader,
    is_playlist,
)


class FakeYoutubeDL:
    """Stands in for yt_dlp.YoutubeDL, replaying a canned media response."""

    last_opts: dict[str, Any] = {}
    response: dict[str, Any] = {}
    error: Exception | None = None

    def __init__(self, opts: dict[str, Any]):
        self.opts = opts
        FakeYoutubeDL.last_opts = opts
        self._progress_hooks = opts.get("progress_hooks", [])
        self._pp_hooks = opts.get("postprocessor_hooks", [])

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url: str, download: bool = False):
        if FakeYoutubeDL.error:
            raise yt_dlp.utils.DownloadError(str(FakeYoutubeDL.error))
        info = dict(FakeYoutubeDL.response)
        info.setdefault("id", "abc123")
        info.setdefault("title", "Fake Video")
        info.setdefault("_platform", "YouTube")

        # Replay a realistic progress + postprocessor sequence.
        if download:
            for hook in self._progress_hooks:
                hook(
                    {
                        "status": "downloading",
                        "filename": "Fake Video [abc123].f137.mp4",
                        "downloaded_bytes": 1000,
                        "total_bytes": 2000,
                        "speed": 500_000,
                        "eta": 2,
                        "info_dict": info,
                    }
                )
                hook(
                    {
                        "status": "finished",
                        "filename": "Fake Video [abc123].f137.mp4",
                        "total_bytes": 2000,
                    }
                )
            for pp in self._pp_hooks:
                pp({"status": "finished", "postprocessor": "Merger",
                    "info_dict": info})
        return info


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDIA_DOWNLOADER_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        "media_downloader.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL
    )
    cfg = Config(download_directory=str(tmp_path / "downloads"))
    with HistoryDB(tmp_path / "h.sqlite3") as db:
        dl = MediaDownloader(cfg, Console(), db=db)
        # pretend ffmpeg exists so merge/conversion guards pass; the stubbed
        # extractor never shells out to it
        if dl.ffmpeg_path is None:
            dl.ffmpeg_path = "/usr/bin/ffmpeg"
        yield dl, db, tmp_path


def test_analyze_uses_stub(engine):
    dl, _db, _tmp = engine
    FakeYoutubeDL.response = {
        "title": "Fake Video",
        "duration": 100,
        "uploader": "Fake Uploader",
        "formats": [],
    }
    info = dl.analyze("https://www.youtube.com/watch?v=abcdefghijk")
    assert info["title"] == "Fake Video" or info["title"] == "Fake Video"
    assert FakeYoutubeDL.last_opts["skip_download"] is True


def test_analyze_rejects_unsupported_url(engine):
    dl, _db, _tmp = engine
    with pytest.raises(Exception):
        dl.analyze("https://example.com/watch")


def test_download_media_records_history(engine):
    dl, db, tmp = engine
    FakeYoutubeDL.response = {
        "_type": "video",
        "title": "Fake Video",
        "duration": 100,
        "uploader": "Fake Uploader",
        "requested_downloads": [
            {"filepath": str(tmp / "downloads" / "Fake Video [abc123].mp4")}
        ],
    }
    (tmp / "downloads").mkdir(exist_ok=True)
    target = tmp / "downloads" / "Fake Video [abc123].mp4"
    target.write_bytes(b"\x00" * 1234)

    result = dl.download_media(
        "https://www.youtube.com/watch?v=abcdefghijk",
        selector="bestvideo+bestaudio/best",
    )
    assert result.title == "Fake Video"
    assert result.platform == "YouTube"
    assert result.file_size == 1234
    rows = db.recent()
    assert len(rows) == 1
    assert rows[0]["title"] == "Fake Video"
    assert rows[0]["file_size"] == 1234


def test_download_media_requires_ffmpeg_for_merge(engine, monkeypatch):
    dl, _db, _tmp = engine
    monkeypatch.setattr(dl, "ffmpeg_path", None)
    FakeYoutubeDL.response = {"title": "x"}
    with pytest.raises(DownloadError) as excinfo:
        dl.download_media(
            "https://www.youtube.com/watch?v=abcdefghijk",
            selector="bestvideo+bestaudio/best",
        )
    assert "FFmpeg" in excinfo.value.message


def test_download_audio_requires_ffmpeg_for_conversion(engine, monkeypatch):
    dl, _db, _tmp = engine
    monkeypatch.setattr(dl, "ffmpeg_path", None)
    with pytest.raises(DownloadError) as excinfo:
        dl.download_audio(
            "https://www.youtube.com/watch?v=abcdefghijk", codec="mp3"
        )
    assert "FFmpeg" in excinfo.value.message


def test_audio_options_passed_to_engine(engine):
    dl, _db, _tmp = engine
    FakeYoutubeDL.response = {
        "_type": "video",
        "title": "Fake Video",
        "requested_downloads": [{"filepath": "/tmp/fake.mp3"}],
    }
    dl.download_audio(
        "https://www.youtube.com/watch?v=abcdefghijk",
        max_bitrate=192,
        codec="mp3",
        quality="192",
    )
    opts = FakeYoutubeDL.last_opts
    assert opts["format"].startswith("bestaudio[abr<=192]")
    assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
    assert opts["postprocessors"][0]["preferredquality"] == "192"


def test_disk_space_guard(engine, monkeypatch):
    dl, _db, _tmp = engine

    class TinyDisk:
        free = 0
        def _usage(self):
            return self

    import shutil as _shutil

    def fake_usage(path):
        return TinyDisk()

    monkeypatch.setattr(_shutil, "disk_usage", fake_usage)
    FakeYoutubeDL.response = {
        "_type": "video",
        "title": "Big Video",
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "height": 1080,
                "vcodec": "avc1",
                "acodec": "none",
                "filesize": 2_000_000_000,
            }
        ],
    }
    with pytest.raises(DownloadError) as excinfo:
        dl.download_media("https://www.youtube.com/watch?v=abcdefghijk")
    assert "disk space" in excinfo.value.message.lower()


def test_playlist_detection():
    assert is_playlist({"_type": "playlist", "entries": [{}]})
    assert not is_playlist({"_type": "video", "title": "x"})


def test_error_translation_reachability(engine):
    dl, _db, _tmp = engine
    FakeYoutubeDL.error = Exception(
        "HTTP Error 429: Too Many Requests"
    )
    with pytest.raises(DownloadError) as excinfo:
        dl.analyze("https://www.youtube.com/watch?v=abcdefghijk")
    assert "Rate" in excinfo.value.message
    FakeYoutubeDL.error = None
