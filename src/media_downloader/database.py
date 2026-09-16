"""SQLite-backed download history.

Only non-sensitive metadata is stored: URL, title, platform, timestamp,
chosen format, resolution, file path and size. No cookies, tokens or
credentials are ever persisted (they are never even read).
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional

log = logging.getLogger("media_downloader.database")

APP_NAME = "media-downloader"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT NOT NULL,
    title         TEXT,
    platform      TEXT,
    downloaded_at TEXT NOT NULL,
    format        TEXT,
    resolution    TEXT,
    file_path     TEXT,
    file_size     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(downloaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_downloads_title ON downloads(title);
"""


def data_dir() -> Path:
    override = os.environ.get("MEDIA_DOWNLOADER_DATA_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_NAME


def default_db_path() -> Path:
    return data_dir() / "history.sqlite3"


class HistoryDB:
    """Small thread-safe wrapper around SQLite for download records."""

    def __init__(self, db_path: Optional[Path] = None):
        self._path = Path(db_path) if db_path else default_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    # ------------------------------------------------------------------
    def add(
        self,
        *,
        url: str,
        title: str,
        platform: str,
        format_desc: str = "",
        resolution: str = "",
        file_path: str = "",
        file_size: Optional[int] = None,
    ) -> int:
        from .utils import now_iso

        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO downloads
                    (url, title, platform, downloaded_at, format, resolution, file_path, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url,
                    title,
                    platform,
                    now_iso(),
                    format_desc,
                    resolution,
                    file_path,
                    file_size,
                ),
            )
            self._conn.commit()
            return int(cursor.lastrowid or 0)

    def recent(self, limit: int = 50, offset: int = 0) -> list[sqlite3.Row]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM downloads ORDER BY id DESC LIMIT ? OFFSET ?",
                (int(limit), int(offset)),
            ).fetchall()
        return list(rows)

    def search(self, query: str, limit: int = 50) -> list[sqlite3.Row]:
        like = f"%{query.strip()}%"
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM downloads
                WHERE title LIKE ? OR url LIKE ? OR platform LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (like, like, like, int(limit)),
            ).fetchall()
        return list(rows)

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM downloads").fetchone()
        return int(row["n"]) if row else 0

    def clear(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM downloads").fetchone()
            removed = int(row["n"]) if row else 0
            self._conn.execute("DELETE FROM downloads")
            self._conn.commit()
        return removed

    def total_bytes(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(file_size), 0) AS n FROM downloads"
            ).fetchone()
        return int(row["n"] or 0)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "HistoryDB":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
