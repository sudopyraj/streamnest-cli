"""Tests for the SQLite history database and the download error translation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_downloader.database import HistoryDB
from media_downloader.downloader import DownloadError, _translate_error


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDIA_DOWNLOADER_DATA_DIR", str(tmp_path))
    with HistoryDB(tmp_path / "history.sqlite3") as database:
        yield database


def test_add_and_recent(db):
    db.add(url="https://youtu.be/abc", title="Cat Video", platform="YouTube",
           format_desc="audio/mp3 192kbps", resolution="audio",
           file_path="/tmp/Cat Video.mp3", file_size=4_000_000)
    rows = db.recent()
    assert len(rows) == 1
    row = rows[0]
    assert row["title"] == "Cat Video"
    assert row["platform"] == "YouTube"
    assert row["file_size"] == 4_000_000
    assert row["downloaded_at"]


def test_search(db):
    db.add(url="https://youtu.be/a", title="Cat Video", platform="YouTube")
    db.add(url="https://www.instagram.com/reel/x/", title="Dog Reel",
           platform="Instagram")
    assert len(db.search("cat")) == 1
    assert len(db.search("instagram")) == 1
    assert len(db.search("zzz")) == 0


def test_clear_and_count(db):
    db.add(url="u1", title="a", platform="YouTube")
    db.add(url="u2", title="b", platform="Instagram")
    assert db.count() == 2
    assert db.clear() == 2
    assert db.count() == 0


def test_total_bytes(db):
    db.add(url="u1", title="a", platform="YouTube", file_size=100)
    db.add(url="u2", title="b", platform="Instagram", file_size=50)
    assert db.total_bytes() == 150


def test_error_translation_private():
    err = _translate_error(
        Exception("This video is private"), "https://youtu.be/x", "YouTube"
    )
    assert isinstance(err, DownloadError)
    assert "Private" in err.message
    assert err.reason


def test_error_translation_rate_limit():
    err = _translate_error(Exception("HTTP Error 429: Too Many Requests"),
                           "u", "YouTube")
    assert "Rate" in err.message


def test_error_translation_unavailable():
    err = _translate_error(
        Exception("Video unavailable"), "u", "YouTube"
    )
    assert "unavailable" in err.message


def test_error_translation_format_hint():
    err = _translate_error(
        Exception("Requested format is not available"), "u", "YouTube"
    )
    assert "--list-formats" in err.hint


def test_error_translation_instagram_private():
    err = _translate_error(
        Exception("Instagram user is not logged in"), "u", "Instagram"
    )
    assert "not be bypassed" in err.reason or "private" in err.reason.lower()


def test_error_translation_unknown_keeps_detail():
    err = _translate_error(Exception("Something exotic"), "u", "YouTube")
    assert err.message == "Download failed"
    assert "exotic" in err.reason
