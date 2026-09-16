"""Interactive terminal UI and compatibility command interface.

The interactive application is the primary user experience. The existing
one-shot options remain available for scripts and experienced users.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from . import formats as fmt
from .config import (
    AUDIO_FORMATS,
    Config,
    ConfigError,
    config_path,
    load_config,
    save_config,
)
from .database import HistoryDB, data_dir
from .downloader import DownloadError, MediaDownloader, is_playlist
from .ffmpeg import find_ffmpeg, install_guidance
from .history import history_menu, render_history_table
from .platforms import detect_platform
from .platforms.youtube import subtitle_languages
from .security import (
    InvalidURLError,
    SecurityError,
    UnsupportedPlatformError,
)
from .utils import (
    human_duration,
    human_size,
    parse_index_list,
    parse_quality,
    parse_size_mb,
)

log = logging.getLogger("media_downloader.cli")

BANNER = """╔══════════════════════════════════════════════╗
║          YT-INSTA DOWNLOADER                 ║
║          Python Media Downloader             ║
╚══════════════════════════════════════════════╝"""

HELP_TEXT = f"""[bold]media-dl[/] — YouTube & Instagram media downloader (v{__version__})

[bold]Interactive mode[/]
  media-dl

[bold]Download media[/]
  media-dl "URL"
  media-dl "URL" --quality 1080p
  media-dl "URL" --mode best|balanced|small
  media-dl "URL" --audio
  media-dl "URL" --audio --format mp3
  media-dl "URL" --max-size 50
  media-dl "URL" --playlist-items 1-5,7
  media-dl "URL" --subtitles en --embed-subs
  media-dl "URL" --output ~/Downloads

[bold]Information[/]
  media-dl "URL" --list-formats
  media-dl history [--search QUERY] [--clear]
  media-dl config [--show] [--path] [--set key=value] [--reset]

[bold]Global options[/]
  --debug    Show detailed error output and enable debug logging

[bold]Where things live[/]
  Configuration: {config_path()}
  History DB:    {data_dir() / "history.sqlite3"}
  Logs:          {data_dir() / "logs"}

Only publicly accessible content is supported. Private or login-gated media
is deliberately out of scope.
"""

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    context_settings={"allow_interspersed_args": True},
    help="YouTube & Instagram media downloader with a polished terminal UI.",
)

_RESERVED = {"history", "config"}

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------


def setup_logging(debug: bool) -> None:
    """File-only logging. Never logs credentials — none are ever used."""
    try:
        log_dir = data_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_dir / "media-downloader.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        logging.basicConfig(
            handlers=[handler],
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        )
    except OSError:  # pragma: no cover - unwritable home
        pass


# ----------------------------------------------------------------------
# Prompt helpers (questionary with a plain fallback for non-TTY use)
# ----------------------------------------------------------------------


class MenuCancelled(Exception):
    """User cancelled the current menu (Ctrl-C / EOF)."""


def _interactive_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def ask_select(message: str, choices: list[Any]) -> Any:
    """choices: list of str, or (label, value) tuples."""
    pairs = [c if isinstance(c, tuple) else (c, c) for c in choices]
    if _interactive_tty():
        import questionary
        from questionary import Choice

        qchoices = [
            Choice(title=f"[{index}] {label}", value=value)
            for index, (label, value) in enumerate(pairs, 1)
        ]
        answer = questionary.select(message, choices=qchoices).ask()
        if answer is None:
            raise MenuCancelled
        return answer
    # Plain fallback
    print(f"\n{message}")
    for i, (label, _value) in enumerate(pairs, 1):
        print(f"  [{i}] {label}")
    while True:
        try:
            raw = input("Select: ").strip()
        except EOFError:
            raise MenuCancelled
        if raw in ("0", "b", "back"):
            return None
        try:
            idx = int(raw)
            if 1 <= idx <= len(pairs):
                return pairs[idx - 1][1]
        except ValueError:
            for label, value in pairs:
                if label.lower() == raw.lower():
                    return value
        print(f"  ✗ Invalid choice: {raw}")


def ask_text(message: str) -> str:
    if _interactive_tty():
        import questionary

        answer = questionary.text(message).ask()
        if answer is None:
            raise MenuCancelled
        return answer.strip()
    try:
        return input(f"{message}\n> ").strip()
    except EOFError:
        raise MenuCancelled


def ask_confirm(message: str, default: bool = True) -> bool:
    if _interactive_tty():
        import questionary

        answer = questionary.confirm(message, default=default).ask()
        if answer is None:
            raise MenuCancelled
        return answer
    try:
        raw = input(f"{message} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    except EOFError:
        raise MenuCancelled
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


def ask_float(message: str) -> float:
    while True:
        raw = ask_text(message)
        try:
            return parse_size_mb(raw)
        except ValueError as exc:
            print(f"  ✗ {exc}")


# ----------------------------------------------------------------------
# Small view helpers
# ----------------------------------------------------------------------


def make_console(cfg: Config) -> Console:
    return Console(highlight=False)


def ffmpeg_warning(console: Console) -> None:
    if not find_ffmpeg():
        console.print(
            "[bold yellow]⚠ FFmpeg was not found.[/]\n\n"
            "FFmpeg is required for merging or converting some media formats.\n"
            f"{install_guidance(_host_platform())}\n"
        )


def _host_platform() -> str:
    return "macos" if sys.platform == "darwin" else sys.platform


def print_media_info(console: Console, info: dict[str, Any], platform: str) -> None:
    console.print(f"[bold cyan]Platform:[/] {platform}")
    console.print(f"[bold cyan]Title:[/]    {info.get('title') or '(untitled)'}")
    console.print(f"[bold cyan]Duration:[/] {human_duration(info.get('duration'))}")
    console.print(
        f"[bold cyan]Uploader:[/] {info.get('uploader') or info.get('channel') or '—'}"
    )
    console.print()


# ----------------------------------------------------------------------
# Format menus
# ----------------------------------------------------------------------


def render_format_table(console: Console, fmts: list[fmt.FormatInfo]) -> None:
    table = Table(title="Available Formats", expand=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("TYPE", no_wrap=True)
    table.add_column("RESOLUTION", no_wrap=True)
    table.add_column("FPS", no_wrap=True)
    table.add_column("CODEC", no_wrap=True)
    table.add_column("EXT", no_wrap=True)
    table.add_column("SIZE", justify="right", no_wrap=True)

    for f in fmts:
        kind = f.media_type.upper()
        if f.has_video and f.has_audio:
            kind = "VIDEO+AUDIO"
        if f.media_type == "video":
            table.add_row(
                f.format_id, kind, f.resolution_label(), f.fps_label(),
                f.codec_label(), f.ext, f.size_label(),
            )
        elif f.media_type == "audio":
            table.add_row(
                f.format_id, kind, "—", "—", f.codec_label(), f.ext, f.size_label(),
            )
        else:  # image
            table.add_row(
                f.format_id, kind,
                f"{f.height}p" if f.height else "—", "—",
                "image", f.ext, f.size_label(),
            )
    console.print(table)


def choose_video_format(
    console: Console, fmts: list[fmt.FormatInfo]
) -> Optional[str]:
    """Interactive per-stream picker. Returns a yt-dlp selector or None."""
    videos = [f for f in fmts if f.media_type == "video"]
    audios = [f for f in fmts if f.media_type == "audio"]
    images = [f for f in fmts if f.media_type == "image"]
    if not videos and not audios and not images:
        console.print("[yellow]No downloadable formats reported for this media.[/]")
        return None

    choices: list[tuple[str, Any]] = []
    if videos:
        console.print("[bold]Video:[/]")
        for f in videos:
            tag = (
                f"{f.resolution_label():<12}{f.fps_label():<9}"
                f"{f.codec_label():<7}{f.size_label():>9}"
            )
            console.print(f"  [{len(choices) + 1}] {tag}")
            choices.append((f"Video {tag}", ("video", f)))
    if audios:
        console.print("[bold]Audio:[/]")
        for f in audios:
            tag = f"{f.codec_label():<12}{f.size_label():>9}"
            console.print(f"  [{len(choices) + 1}] {f.audio_bitrate_label():<12}{tag}")
            label = f"Audio {f.audio_bitrate_label()} {f.codec_label()} {f.size_label()}"
            choices.append((label, ("audio", f)))
    if images:
        console.print("[bold]Image:[/]")
        for f in images:
            tag = f"{f.height}p".ljust(12) if f.height else "—"
            console.print(f"  [{len(choices) + 1}] {tag}{f.ext:<6}{f.size_label():>9}")
            choices.append((f"Image {f.ext} {f.size_label()}", ("image", f)))
    console.print("  [0] Back")

    label = ask_select("Select:", [c[0] for c in choices] + ["Back"])
    if label == "Back":
        return None
    selected = next(v for name, v in choices if name == label)
    kind, chosen = selected

    if kind == "audio":
        console.print(
            "[dim]This is an audio-only stream — switching to audio download.[/]"
        )
        return "__audio__"
    if kind == "image" or chosen.has_audio:
        return chosen.format_id
    if any(a.has_audio for a in audios) or any(v.has_audio for v in videos):
        return f"{chosen.format_id}+bestaudio"
    return chosen.format_id


def choose_custom(
    console: Console, fmts: list[fmt.FormatInfo], container: str
) -> Optional[str]:
    heights = fmt.resolution_choices(fmts)
    if not heights:
        console.print("[yellow]No video resolutions reported; using best available.[/]")
        return fmt.video_selector(None, container)
    height_labels = [f"{h}p" for h in heights]
    label = ask_select("Resolution", height_labels + ["Best available"])
    height = None if label == "Best available" else int(label.rstrip("p"))

    fps_values = fmt.fps_choices(fmts)
    fps = None
    if fps_values:
        fps_label = ask_select(
            "FPS",
            [f"{int(f)} FPS" for f in fps_values] + ["Any"],
        )
        if fps_label != "Any":
            fps = int(fps_label.split()[0])

    return fmt.video_selector(height, container, fps)


def choose_container(console: Console) -> Optional[str]:
    """Ask the user for the desired output container."""
    return ask_select(
        "Container",
        [
            ("MP4 (most compatible)", "mp4"),
            ("WebM (efficient, open)", "webm"),
            ("Original (no re-mux)", "original"),
        ],
    )


def choose_under_size(
    console: Console, fmts: list[fmt.FormatInfo], container: str
) -> Optional[tuple[str, str]]:
    limit = ask_float("Maximum file size (MB):")
    fitting = fmt.formats_under_limit(fmts, limit)
    if not fitting:
        console.print(
            f"[yellow]No formats found under {limit:g} MB "
            "(sizes may be unknown for this media).[/]"
        )
        return None
    console.print(f"[bold]Formats under {limit:g} MB:[/]\n")
    choices: list[tuple[str, Any]] = []
    for f, total in fitting:
        approx = "~" if f.is_estimate() else ""
        label = f"{f.resolution_label():<10}{approx}{human_size(total):>10}"
        console.print(f"  [{len(choices) + 1}] {label}")
        choices.append((label, (f, total)))
    console.print("  [0] Back")

    label = ask_select("Select:", [c[0] for c in choices] + ["Back"])
    if label == "Back":
        return None
    chosen, _total = next(v for name, v in choices if name == label)
    if chosen.has_audio or any(v.has_audio for v in fmts if v.media_type == "video"):
        selector = f"{chosen.format_id}+bestaudio"
    else:
        selector = chosen.format_id
    return selector, container


# ----------------------------------------------------------------------
# Subtitle menus
# ----------------------------------------------------------------------


def choose_subtitles(
    console: Console, info: dict[str, Any], platform: str
) -> tuple[list[str], bool]:
    """Returns (languages, embed). Empty list = no subtitles."""
    if platform != "YouTube":
        return [], False
    languages = subtitle_languages(info)
    if not languages:
        return [], False
    console.print("[bold]Available subtitles:[/]")
    choices: list[tuple[str, Any]] = []
    for i, (lang, auto) in enumerate(languages, 1):
        label = f"{lang}{' (auto-generated)' if auto else ''}"
        console.print(f"  [{i}] {label}")
        choices.append((label, lang))
    console.print("  [0] None")

    label = ask_select("Select:", [c[0] for c in choices] + ["None"])
    if label == "None":
        return [], False
    lang = next(v for name, v in choices if name == label)
    embed = ask_confirm("Embed subtitles into the video file?", default=False)
    return [lang], embed


# ----------------------------------------------------------------------
# Interactive flows
# ----------------------------------------------------------------------


def flow_url(console: Console, dl: MediaDownloader) -> Optional[dict[str, Any]]:
    """Ask for + validate a URL. Returns (info, platform, url) or None."""
    while True:
        raw = ask_text("Enter YouTube or Instagram URL:")
        if not raw:
            continue
        try:
            platform, url = detect_platform(raw)
        except InvalidURLError as exc:
            console.print(f"[bold red]✗ Invalid or unsupported URL.[/] [dim]({exc})[/]\n")
            continue
        except UnsupportedPlatformError as exc:
            console.print(f"[bold red]✗ {exc}[/]\n")
            continue
        console.print("[dim]Analyzing…[/]")
        try:
            info = dl.analyze(url)
        except DownloadError as exc:
            exc.render(console)
            console.print()
            return None
        return {"info": info, "platform": platform, "url": url}


def _resume_prompt(
    console: Console, dl: MediaDownloader, info: dict[str, Any], out_dir: Path
) -> None:
    """Detect interrupted downloads and offer to resume or restart."""
    title = info.get("title") or ""
    partials = dl.find_partials(out_dir, title)
    if not partials:
        return
    done, total = dl.partial_progress(partials)
    if total:
        console.print("\n[yellow]Previous download detected.[/]")
        console.print(f"File:   {title}")
        console.print(f"Downloaded: {human_size(done)} / {human_size(max(total, done))}")
        if ask_confirm("Resume download?"):
            console.print("[dim]Resuming…[/]")
        else:
            dl.remove_partials(partials)
            console.print("[dim]Starting a fresh download.[/]")


def menu_download(
    cfg: Config,
    dl: MediaDownloader,
    console: Console,
    audio_only: bool = False,
) -> None:
    ctx = flow_url(console, dl)
    if ctx is None:
        return
    info, platform, url = ctx["info"], ctx["platform"], ctx["url"]

    if is_playlist(info):
        console.print("[yellow]Playlist detected — opening the playlist flow.[/]\n")
        menu_playlist(cfg, dl, console, preloaded=(info, url))
        return

    print_media_info(console, info, platform)
    out_dir = cfg.resolved_download_dir()
    _resume_prompt(console, dl, info, out_dir)

    if audio_only:
        _flow_audio(cfg, dl, console, info, url)
        return

    mode = ask_select(
        "Download mode",
        [
            ("Best Quality (highest available)", "best"),
            ("Balanced (up to 1080p)", "balanced"),
            ("Small File (up to 480p, mobile-friendly)", "small"),
            ("Custom (resolution, FPS, container)", "custom"),
            ("Maximum file size…", "size"),
            ("Choose from format list…", "list"),
            ("Back", "back"),
        ],
    )
    if mode == "back":
        return

    fmts = fmt.build_format_list(info)
    selector: Optional[str]
    container = "original"

    if mode == "list":
        selector = choose_video_format(console, fmts)
        if selector == "__audio__":
            _flow_audio(cfg, dl, console, info, url)
            return
        container = "original"
    else:
        container = choose_container(console) or "original"
        if mode in ("best", "balanced", "small"):
            selector = fmt.smart_selector(mode, container)
        elif mode == "custom":
            selector = choose_custom(console, fmts, container)
        elif mode == "size":
            result = choose_under_size(console, fmts, container)
            if not result:
                return
            selector = result[0]
    if not selector:
        return

    subtitles, embed = [], False
    if mode != "list" and info.get("duration"):
        try:
            subtitles, embed = choose_subtitles(console, info, platform)
        except MenuCancelled:
            subtitles, embed = [], False

    try:
        result = dl.download_media(
            url,
            info=info,
            selector=selector,
            container=container,
            subtitles=subtitles,
            embed_subtitles=embed,
        )
    except DownloadError as exc:
        exc.render(console)
        return
    _print_result(console, result)


def _flow_audio(
    cfg: Config,
    dl: MediaDownloader,
    console: Console,
    info: dict[str, Any],
    url: str,
) -> None:
    fmts = fmt.build_format_list(info)
    source = fmt.best_audio_bitrate(fmts)

    console.print("[bold]Audio Download[/]\n")
    quality_labels = ["Best available", "320 kbps", "256 kbps", "192 kbps", "128 kbps"]
    caps: list[Optional[int]] = [None, 320, 256, 192, 128]
    shown = []
    for label, cap in zip(quality_labels, caps):
        note = ""
        if source and cap and cap > source:
            note = f"  (source is ~{source} kbps — no quality gain)"
        shown.append(label + note)
    console.print(
        "\n".join(f"  [{i}] {label}" for i, label in enumerate(shown, 1))
    )
    choice = ask_select("Quality:", shown)
    max_bitrate = caps[shown.index(choice)]

    console.print("\n[bold]Format:[/]")
    codecs = [
        ("MP3", "mp3"), ("M4A", "m4a"), ("Opus", "opus"),
        ("Original (no conversion)", "original"),
    ]
    for i, (label, _v) in enumerate(codecs, 1):
        console.print(f"  [{i}] {label}")
    codec = ask_select("Select:", codecs)

    if codec == "original":
        quality = None
    elif max_bitrate:
        quality = str(max_bitrate)
    else:
        quality = cfg.default_audio_quality

    if codec != "original" and source and max_bitrate and max_bitrate > source:
        console.print(
            f"[yellow]Source: {source} kbps → Output: {codec.upper()} "
            f"{max_bitrate} kbps. Re-encoding will not add quality.[/]"
        )
    elif codec != "original":
        console.print(f"[dim]Source: {source or 'unknown'} kbps → Output: {codec.upper()}[/]")

    try:
        result = dl.download_audio(
            url,
            info=info,
            max_bitrate=max_bitrate,
            codec=codec,
            quality=quality,
        )
    except DownloadError as exc:
        exc.render(console)
        return
    _print_result(console, result)


def _print_result(console: Console, result) -> None:
    console.print()
    if result.filepath:
        console.print("[bold green]✓ Download complete![/]")
        console.print(f"[dim]Saved to:[/] {result.filepath}")
        if result.file_size:
            console.print(f"[dim]Size:[/] {human_size(result.file_size)}")
    else:
        console.print("[yellow]✓ Finished, but the output file could not be located.[/]")
    console.print()


def menu_playlist(
    cfg: Config,
    dl: MediaDownloader,
    console: Console,
    preloaded: Optional[tuple[dict[str, Any], str]] = None,
) -> None:
    if preloaded:
        info, url = preloaded
    else:
        ctx = flow_url(console, dl)
        if ctx is None:
            return
        info, url = ctx["info"], ctx["url"]

    if not is_playlist(info):
        console.print(
            "[yellow]This URL is a single media item — opening the media flow.[/]\n"
        )
        menu_download(cfg, dl, console)
        return

    entries = [e for e in (info.get("entries") or []) if e]
    console.print(f"[bold cyan]Playlist detected:[/] {info.get('title') or '(untitled)'}")
    console.print(f"Videos: {len(entries)}\n")

    choice = ask_select(
        "Playlist options",
        ["Download all", "Select videos", "Cancel"],
    )
    if choice == "Cancel":
        return

    playlist_items: Optional[list[int]] = None
    if choice == "Select videos":
        console.print(
            "[dim]Enter video numbers, ranges or both (e.g. 1-5,7,10-12).[/]"
        )
        while True:
            raw = ask_text("Videos:")
            try:
                playlist_items = parse_index_list(raw, len(entries))
                break
            except ValueError as exc:
                console.print(f"[red]✗ {exc}[/]")
        titles = [
            entries[i - 1].get("title") or f"Video {i}" for i in playlist_items
        ]
        console.print(f"[dim]Selected {len(titles)} videos: "
                      + ", ".join(titles[:5]) + ("…" if len(titles) > 5 else "") + "[/]")

    mode = ask_select(
        "Apply quality to all videos",
        [
            ("Best Quality", "best"),
            ("Balanced (≤1080p)", "balanced"),
            ("Small File (≤480p)", "small"),
            ("Custom…", "custom"),
            ("Cancel", "back"),
        ],
    )
    if mode == "back":
        return
    container = choose_container(console) or "original"
    if mode == "custom":
        probe_fmts = fmt.build_format_list(info)
        selector = choose_custom(console, probe_fmts, container)
        if not selector:
            return
    else:
        selector = fmt.smart_selector(mode, container)

    try:
        results = dl.download_playlist(
            url,
            selector=selector,
            container=container,
            playlist_items=playlist_items,
        )
    except DownloadError as exc:
        exc.render(console)
        return
    total_size = sum(r.file_size or 0 for r in results)
    console.print(
        f"\n[bold green]✓ Playlist finished:[/] {len(results)} videos, "
        f"{human_size(total_size)} total."
    )


# ----------------------------------------------------------------------
# Settings & help
# ----------------------------------------------------------------------

_EDITABLE = {
    "download_directory": "Download directory",
    "default_video_quality": "Default video quality (best/2160p…/240p)",
    "default_audio_quality": "Default audio quality (best/320/256/192/128)",
    "default_audio_format": "Default audio format (mp3/m4a/opus/original)",
    "default_video_format": "Default video format (mp4/webm/original)",
    "max_concurrent_downloads": "Max concurrent downloads (1–8)",
    "overwrite_existing_files": "Overwrite existing files",
    "filename_template": "Filename template",
    "theme": "Theme (dark/light/mono)",
}


def menu_settings(cfg: Config, console: Console) -> None:
    while True:
        table = Table(title="Settings", show_header=False, expand=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", overflow="fold")
        for key, label in _EDITABLE.items():
            table.add_row(label, str(getattr(cfg, key)))
        console.print(table)
        console.print(f"[dim]Config file: {config_path()}[/]\n")

        choice = ask_select(
            "Settings",
            ["Edit a setting", "Reset to defaults", "Back"],
        )
        if choice == "Back":
            return
        if choice == "Reset to defaults":
            if ask_confirm(
                "Reset all settings to their original defaults?",
                default=False,
            ):
                try:
                    defaults = Config()
                    save_config(defaults)
                    for key in cfg.known_keys():
                        setattr(cfg, key, getattr(defaults, key))
                    console.print("[green]✓ Settings reset to defaults.[/]")
                except (ConfigError, OSError) as exc:
                    console.print(f"[red]✗ Could not reset settings: {exc}[/]")
            else:
                console.print("[dim]Reset cancelled.[/]")
            continue
        label = ask_select("Which setting?", [
            (lbl, key) for key, lbl in _EDITABLE.items()
        ])
        current = getattr(cfg, label)
        new_value = ask_text(f"New value for {label} [{current}]:")
        if not new_value:
            continue
        if isinstance(current, bool):
            new_value = new_value.strip().lower() in ("1", "true", "yes", "y")
        elif isinstance(current, int):
            try:
                new_value = int(new_value)
            except ValueError:
                console.print("[red]✗ Must be a whole number.[/]")
                continue
        try:
            setattr(cfg, label, new_value)
            cfg.validate()
            save_config(cfg)
            console.print("[green]✓ Saved.[/]")
        except (ConfigError, ValueError) as exc:
            console.print(f"[red]✗ {exc}[/]")
            setattr(cfg, label, current)


def menu_help(console: Console) -> None:
    console.print(HELP_TEXT)


# ----------------------------------------------------------------------
# Interactive main loop
# ----------------------------------------------------------------------


def interactive_main(cfg: Config, console: Console) -> None:
    console.print(BANNER, style="bold cyan")
    console.print(f"[dim]v{__version__} — downloads to {cfg.resolved_download_dir()}[/]\n")
    ffmpeg_warning(console)

    db = HistoryDB()
    try:
        dl = MediaDownloader(cfg, console, db=db)
        while True:
            try:
                choice = ask_select(
                    "Select an option:",
                    [
                        "Download Media",
                        "Audio Only",
                        "Download Playlist",
                        "Download History",
                        "Settings",
                        "Help",
                        "Exit",
                    ],
                )
            except (MenuCancelled, KeyboardInterrupt):
                break
            if choice == "Exit":
                break
            try:
                if choice == "Download Media":
                    menu_download(cfg, dl, console)
                elif choice == "Audio Only":
                    menu_download(cfg, dl, console, audio_only=True)
                elif choice == "Download Playlist":
                    menu_playlist(cfg, dl, console)
                elif choice == "Download History":
                    history_menu(console, db, ask_select, ask_confirm, ask_text)
                elif choice == "Settings":
                    menu_settings(cfg, console)
                elif choice == "Help":
                    menu_help(console)
            except MenuCancelled:
                continue
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted — partial files kept for resume.[/]")
            console.print()
    finally:
        db.close()
    console.print("[dim]Goodbye![/]")


# ----------------------------------------------------------------------
# Non-interactive commands
# ----------------------------------------------------------------------


def cmd_history(cfg: Config, console: Console, search: Optional[str], clear: bool) -> None:
    with HistoryDB() as db:
        if clear:
            removed = db.clear()
            console.print(f"[green]✓ Removed {removed} history entries.[/]")
            return
        rows = db.search(search) if search else db.recent()
        if not rows:
            console.print("[yellow]No history entries.[/]")
            return
        render_history_table(rows, console, "Download history")


def cmd_config(
    cfg: Config,
    console: Console,
    show: bool,
    path: bool,
    set_pair: Optional[str],
    reset: bool,
) -> None:
    if path:
        console.print(str(config_path()))
        return
    if reset:
        if ask_confirm("Reset configuration to defaults?", default=False):
            save_config(Config())
            console.print("[green]✓ Configuration reset.[/]")
        return
    if set_pair:
        if "=" not in set_pair:
            console.print("[red]✗ Use --set key=value[/]")
            raise typer.Exit(2)
        key, _, value = set_pair.partition("=")
        key = key.strip()
        if key not in cfg.known_keys():
            console.print(
                f"[red]✗ Unknown setting {key!r}. Known: {', '.join(cfg.known_keys())}[/]"
            )
            raise typer.Exit(2)
        current = getattr(cfg, key)
        if isinstance(current, bool):
            value = value.strip().lower() in ("1", "true", "yes", "y")
        elif isinstance(current, int):
            try:
                value = int(value)
            except ValueError:
                console.print(f"[red]✗ {key} must be a number.[/]")
                raise typer.Exit(2)
        try:
            setattr(cfg, key, value)
            cfg.validate()
            save_config(cfg)
            console.print(f"[green]✓ {key} = {value}[/]")
        except (ConfigError, ValueError) as exc:
            console.print(f"[red]✗ {exc}[/]")
            raise typer.Exit(2)
        return

    table = Table(title="Configuration", show_header=False, expand=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", overflow="fold")
    for key in cfg.known_keys():
        table.add_row(key, str(getattr(cfg, key)))
    console.print(table)
    console.print(f"[dim]Config file: {config_path()}[/]")


def cmd_list_formats(cfg: Config, console: Console, url: str) -> None:
    dl = MediaDownloader(cfg, console)
    try:
        platform, url = detect_platform(url)
    except SecurityError as exc:
        console.print(f"[bold red]✗ {exc}[/]")
        raise typer.Exit(2)
    try:
        info = dl.analyze(url)
    except DownloadError as exc:
        exc.render(console)
        raise typer.Exit(1)
    if is_playlist(info):
        console.print("[yellow]Playlists do not expose a single format list; "
                      "formats are per-video.[/]")
        raise typer.Exit(0)
    render_format_table(console, fmt.build_format_list(info))


def run_direct(
    cfg: Config,
    console: Console,
    url: str,
    quality: Optional[str],
    audio: bool,
    audio_format: Optional[str],
    output: Optional[Path],
    max_size: Optional[float],
    mode: Optional[str],
    subtitles: Optional[str],
    embed_subs: bool,
    playlist_items: Optional[str],
) -> None:
    out_dir = str(output.expanduser()) if output else None
    db = HistoryDB()
    dl = MediaDownloader(cfg, console, db=db)
    try:
        if quality and mode:
            console.print("[red]✗ Use either --quality or --mode, not both.[/]")
            raise typer.Exit(2)
        if audio:
            caps = {"best": None, "320": 320, "256": 256, "192": 192, "128": 128}
            max_bitrate = caps.get((quality or "best").lower())
            if quality and max_bitrate is None and quality.lower() != "best":
                raise typer.Exit(_bad_quality(console, quality))
            codec = (audio_format or cfg.default_audio_format).lower()
            if codec not in AUDIO_FORMATS:
                console.print(
                    f"[red]✗ Audio format must be one of {AUDIO_FORMATS}[/]"
                )
                raise typer.Exit(2)
            result = dl.download_audio(
                url, max_bitrate=max_bitrate, codec=codec,
                quality=str(max_bitrate) if max_bitrate else None,
                out_dir=out_dir,
            )
            _print_result(console, result)
            return

        container = cfg.default_video_format
        if mode:
            if mode not in ("best", "balanced", "small"):
                console.print("[red]✗ --mode must be best, balanced or small.[/]")
                raise typer.Exit(2)
            selector = fmt.smart_selector(mode, container)
        elif quality:
            try:
                height = parse_quality(quality)
            except ValueError:
                raise typer.Exit(_bad_quality(console, quality))
            selector = fmt.video_selector(height, container)
        else:
            selector = fmt.smart_selector("balanced", container)

        if playlist_items:
            info = dl.analyze(url)
            if not is_playlist(info):
                console.print("[red]✗ --playlist-items only applies to playlists.[/]")
                raise typer.Exit(2)
            count = len([e for e in (info.get("entries") or []) if e])
            try:
                items = parse_index_list(playlist_items, count)
            except ValueError as exc:
                console.print(f"[red]✗ {exc}[/]")
                raise typer.Exit(2)
            results = dl.download_playlist(
                url, selector=selector, container=container,
                playlist_items=items, out_dir=out_dir,
            )
            console.print(
                f"[bold green]✓ Playlist finished:[/] {len(results)} videos."
            )
            return

        result = dl.download_media(
            url,
            selector=selector,
            container=container,
            max_size_mb=max_size,
            out_dir=out_dir,
            subtitles=[s.strip() for s in subtitles.split(",")] if subtitles else None,
            embed_subtitles=embed_subs,
        )
        _print_result(console, result)
    except DownloadError as exc:
        exc.render(console)
        raise typer.Exit(1)
    finally:
        db.close()


def _bad_quality(console: Console, quality: str) -> int:
    console.print(
        f"[red]✗ Unknown quality {quality!r}. "
        "Use 240p…2160p, 'best', or an audio bitrate (320/256/192/128).[/]"
    )
    return 2


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    target: Optional[str] = typer.Argument(
        None,
        help="A YouTube/Instagram URL, or one of the commands: history, config.",
    ),
    quality: Optional[str] = typer.Option(
        None, "--quality", "-q", help="Video resolution (1080p) or audio bitrate (320)."
    ),
    audio: bool = typer.Option(False, "--audio", "-a", help="Audio-only download."),
    audio_format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Audio format: mp3, m4a, opus, original."
    ),
    list_formats: bool = typer.Option(
        False, "--list-formats", help="List all available formats for the URL."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Download directory."
    ),
    max_size: Optional[float] = typer.Option(
        None, "--max-size", help="Maximum file size in MB."
    ),
    mode: Optional[str] = typer.Option(
        None, "--mode", help="Smart mode: best, balanced or small."
    ),
    subtitles: Optional[str] = typer.Option(
        None, "--subtitles", "-s", help="Subtitle language(s), comma separated."
    ),
    embed_subs: bool = typer.Option(
        False, "--embed-subs", help="Embed subtitles into the video file."
    ),
    playlist_items: Optional[str] = typer.Option(
        None, "--playlist-items", help="Playlist selection, e.g. 1-5,7."
    ),
    debug: bool = typer.Option(False, "--debug", help="Verbose error output."),
    # history / config command options (used when the first word is a command)
    history_search: Optional[str] = typer.Option(
        None, "--search", help="(history) search entries by title/URL/platform."
    ),
    history_clear: bool = typer.Option(
        False, "--clear", help="(history) remove all history entries."
    ),
    config_set: Optional[str] = typer.Option(
        None, "--set", help="(config) set a key=value pair, e.g. --set theme=light."
    ),
    config_path_flag: bool = typer.Option(
        False, "--path", help="(config) print the configuration file path."
    ),
    config_reset: bool = typer.Option(
        False, "--reset", help="(config) reset configuration to defaults."
    ),
) -> None:
    """YouTube & Instagram media downloader."""
    setup_logging(debug)
    try:
        cfg = load_config()
    except ConfigError as exc:
        typer.secho(f"✗ {exc}", fg="red", err=True)
        raise typer.Exit(1)

    console = Console(highlight=False)

    if target is None:
        exit_code = 0
        try:
            interactive_main(cfg, console)
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye![/]")
        except Exception as exc:
            log.exception("Unexpected interactive application error")
            exit_code = 1
            console.print(
                "[bold red]✗ The application encountered an unexpected error.[/]\n"
                "[dim]Your settings and download history were not changed. "
                "Check the log file for technical details.[/]"
            )
        raise typer.Exit(exit_code)

    if target in _RESERVED:
        if target == "history":
            cmd_history(
                cfg, console,
                search=history_search,
                clear=history_clear,
            )
        else:
            cmd_config(
                cfg, console,
                show=True,
                path=config_path_flag,
                set_pair=config_set,
                reset=config_reset,
            )
        raise typer.Exit(0)

    if not target.startswith(("http://", "https://")):
        console.print(
            f"[bold red]✗ Unknown command or invalid URL: {target}[/]\n\n"
            "Try:\n  media-dl --help"
        )
        raise typer.Exit(2)

    if list_formats:
        cmd_list_formats(cfg, console, target)
        raise typer.Exit(0)

    try:
        run_direct(
            cfg,
            console,
            target,
            quality,
            audio,
            audio_format,
            output,
            max_size,
            mode,
            subtitles,
            embed_subs,
            playlist_items,
        )
    except SecurityError as exc:
        console.print(f"[bold red]✗ Invalid or unsupported URL.[/] [dim]({exc})[/]")
        raise typer.Exit(2)


if __name__ == "__main__":  # pragma: no cover
    app()
