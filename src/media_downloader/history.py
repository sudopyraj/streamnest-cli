"""Download history views: interactive menu and rich table rendering."""

from __future__ import annotations

from typing import Callable, Optional

from rich.console import Console
from rich.table import Table

from .database import HistoryDB
from .utils import human_size


def render_history_table(rows, console: Console, title: str) -> None:
    table = Table(title=title, show_lines=False, expand=True)
    table.add_column("#", style="dim", justify="right")
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Platform", style="magenta")
    table.add_column("Title", overflow="fold")
    table.add_column("Format", no_wrap=True)
    table.add_column("Size", justify="right", no_wrap=True)

    for row in rows:
        downloaded_at = (row["downloaded_at"] or "")[:16].replace("T", " ")
        table.add_row(
            str(row["id"]),
            downloaded_at,
            row["platform"] or "—",
            row["title"] or "(untitled)",
            row["format"] or "—",
            human_size(row["file_size"]),
        )
    console.print(table)


def history_menu(
    console: Console,
    db: HistoryDB,
    select: Callable[..., str],
    confirm: Callable[..., bool],
    prompt: Callable[..., str],
) -> None:
    """Interactive history menu.

    ``select``/``confirm``/``prompt`` are injected so the CLI can use
    questionary when attached to a TTY and a plain fallback otherwise.
    """
    while True:
        choice = select(
            "History",
            ["View history", "Search history", "Clear history", "Back"],
        )
        if choice == "Back":
            return
        elif choice == "View history":
            _view(console, db)
        elif choice == "Search history":
            query = prompt("Search (title / URL / platform):")
            if query:
                _view(console, db, query.strip())
        elif choice == "Clear history":
            count = db.count()
            if count == 0:
                console.print("[dim]History is already empty.[/]")
                continue
            if confirm(f"Delete all {count} history entries?"):
                removed = db.clear()
                console.print(f"[green]✓ Removed {removed} entries.[/]")
            else:
                console.print("[dim]Cancelled.[/]")


def _view(console: Console, db: HistoryDB, query: Optional[str] = None) -> None:
    rows = db.search(query) if query else db.recent()
    if not rows:
        console.print("[yellow]No history entries found.[/]")
        return
    title = f"Search results: “{query}”" if query else "Download history"
    render_history_table(rows, console, title)
    console.print(
        f"[dim]{len(rows)} entries · {human_size(db.total_bytes())} total "
        "downloaded (recorded).[/]"
    )
