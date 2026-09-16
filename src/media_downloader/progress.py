"""Rich-powered progress reporting for downloads and post-processing stages."""

from __future__ import annotations

import re
import threading
from typing import Any, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

_STREAM_ID = re.compile(r"\.f(\d+)\.(?:mp4|webm|m4a|opus|mkv|mp3)$")

POSTPROCESSOR_LABELS = {
    "Merger": "Merging streams",
    "ExtractAudio": "Converting audio",
    "VideoRemuxer": "Remuxing container",
    "FFmpegEmbedSubtitle": "Embedding subtitles",
    "MoveFiles": "Finalising files",
}


class ProgressReporter:
    """One Rich ``Progress`` instance managing several concurrent download tasks.

    A task is created per downloaded file/stream (keyed by filename), which
    naturally renders one bar for the video stream, another for audio, etc.
    Rich's ``Progress`` is thread-safe, so concurrent playlist downloads can
    all update the same display.
    """

    def __init__(self, console: Console, style: Optional[dict] = None):
        style = style or {}
        self._progress = Progress(
            SpinnerColumn(style=style.get("spinner", "dots")),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, style=style.get("bar", "blue")),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(compact=True),
            console=console,
            transient=False,
        )
        self._lock = threading.Lock()
        self._tasks: dict[str, TaskID] = {}
        self._overall: Optional[TaskID] = None

    # -- lifecycle ----------------------------------------------------
    def __enter__(self) -> "ProgressReporter":
        self._progress.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._progress.stop()

    def stop(self) -> None:
        self._progress.stop()

    # -- overall (playlist) progress ------------------------------------
    def add_overall(self, description: str, total: int) -> None:
        with self._lock:
            if self._overall is None:
                self._overall = self._progress.add_task(
                    f"[bold]{description}[/]", total=total
                )
            else:
                self._progress.update(self._overall, total=total, completed=0)

    def advance_overall(self, description: Optional[str] = None) -> None:
        with self._lock:
            if self._overall is not None:
                if description:
                    self._progress.update(self._overall, description=description)
                self._progress.advance(self._overall, 1)

    # -- per-stream progress -------------------------------------------
    def hook(self, description: str = "Downloading"):
        """Return a yt-dlp progress hook bound to this reporter."""

        def _hook(data: dict[str, Any]) -> None:
            status = data.get("status")
            filename = data.get("filename") or "media"
            with self._lock:
                if status == "downloading":
                    task_id = self._tasks.get(filename)
                    if task_id is None:
                        task_id = self._progress.add_task(
                            description, total=None, visible=True
                        )
                        self._tasks[filename] = task_id
                    total = (
                        data.get("total_bytes")
                        or data.get("total_bytes_estimate")
                        or 0
                    )
                    done = data.get("downloaded_bytes") or 0
                    if total:
                        self._progress.update(
                            task_id, total=float(total), completed=float(done)
                        )
                    else:
                        self._progress.update(
                            task_id, completed=float(done), total=None
                        )
                    # playlist-level bookkeeping
                    info = data.get("info_dict") or {}
                    if info.get("playlist_index") and self._overall is not None:
                        self._progress.update(
                            self._overall,
                            description=f"[bold]Playlist: {info['playlist_index']} / "
                            f"{info.get('n_entries', '?')}[/]",
                        )
                elif status == "finished":
                    task_id = self._tasks.get(filename)
                    if task_id is not None:
                        total = data.get("total_bytes") or data.get(
                            "downloaded_bytes"
                        )
                        self._progress.update(
                            task_id,
                            completed=float(total or 1),
                            total=float(total or 1),
                        )

        return _hook

    def make_postprocessor_hook(self, console: Console, success_style: str = "bold green"):
        """Return a yt-dlp postprocessor hook that renders stage checkmarks."""

        def _hook(data: dict[str, Any]) -> None:
            if data.get("status") != "finished":
                return
            name = data.get("postprocessor") or ""
            label = POSTPROCESSOR_LABELS.get(name)
            if label:
                console.print(f"  [{success_style}]✓[/] {label}")

        return _hook


def stream_kind_label(filename: str, formats_by_id: dict[str, Any]) -> str:
    """Best-effort label ('video' / 'audio') for a downloaded stream file."""
    match = _STREAM_ID.search(filename)
    if match:
        fmt = formats_by_id.get(match.group(1))
        if fmt is not None:
            return "audio" if fmt.media_type == "audio" else "video"
    return "media"
