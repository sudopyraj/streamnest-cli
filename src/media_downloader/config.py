"""Configuration management.

The configuration lives at ``~/.config/media-downloader/config.toml``
(overridable via the ``MEDIA_DOWNLOADER_CONFIG_DIR`` environment variable —
mostly useful for tests). Reading uses Python's built-in ``tomllib``; writing
uses a small purpose-built emitter so no extra dependency is needed.
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .security import SecurityError, validate_output_template

log = logging.getLogger("media_downloader.config")

APP_NAME = "media-downloader"

VIDEO_QUALITIES = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p"]
AUDIO_QUALITIES = ["best", "320", "256", "192", "128"]
AUDIO_FORMATS = ["mp3", "m4a", "opus", "original"]
VIDEO_FORMATS = ["mp4", "webm", "original"]
THEMES = ["dark", "light", "mono"]
MAX_CONCURRENT_LIMIT = 8


class ConfigError(Exception):
    """Raised for invalid configuration values."""


@dataclass
class Config:
    download_directory: str = "~/Downloads"
    default_video_quality: str = "1080p"
    default_audio_quality: str = "192"
    default_audio_format: str = "mp3"
    default_video_format: str = "mp4"
    max_concurrent_downloads: int = 3
    overwrite_existing_files: bool = False
    filename_template: str = "%(title)s [%(id)s].%(ext)s"
    theme: str = "dark"

    # ------------------------------------------------------------------
    def validate(self) -> "Config":
        if self.default_video_quality not in VIDEO_QUALITIES:
            raise ConfigError(
                f"default_video_quality must be one of {VIDEO_QUALITIES}"
            )
        if self.default_audio_quality not in AUDIO_QUALITIES:
            raise ConfigError(
                f"default_audio_quality must be one of {AUDIO_QUALITIES}"
            )
        if self.default_audio_format not in AUDIO_FORMATS:
            raise ConfigError(
                f"default_audio_format must be one of {AUDIO_FORMATS}"
            )
        if self.default_video_format not in VIDEO_FORMATS:
            raise ConfigError(
                f"default_video_format must be one of {VIDEO_FORMATS}"
            )
        if self.theme not in THEMES:
            raise ConfigError(f"theme must be one of {THEMES}")
        try:
            self.max_concurrent_downloads = int(self.max_concurrent_downloads)
        except (TypeError, ValueError) as exc:
            raise ConfigError("max_concurrent_downloads must be a number") from exc
        if not 1 <= self.max_concurrent_downloads <= MAX_CONCURRENT_LIMIT:
            raise ConfigError(
                f"max_concurrent_downloads must be between 1 and {MAX_CONCURRENT_LIMIT}"
            )
        if not isinstance(self.overwrite_existing_files, bool):
            self.overwrite_existing_files = str(self.overwrite_existing_files).lower() in (
                "1", "true", "yes",
            )
        try:
            validate_output_template(self.filename_template)
        except SecurityError as exc:
            raise ConfigError(f"Invalid filename_template: {exc}") from exc
        return self

    def resolved_download_dir(self) -> Path:
        path = Path(self.download_directory).expanduser()
        if not path.is_absolute():
            path = Path.home() / path
        return path

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def known_keys(self) -> list[str]:
        return [f.name for f in fields(self)]


def config_dir() -> Path:
    override = os.environ.get("MEDIA_DOWNLOADER_CONFIG_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.toml"


def load_config(create_if_missing: bool = True) -> Config:
    """Load configuration, falling back to defaults for missing keys."""
    path = config_path()
    data: dict[str, Any] = {}
    if path.exists():
        try:
            with open(path, "rb") as fh:
                data = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(
                f"Could not parse {path}: {exc}\n"
                "Fix or delete the file, or start the app and choose "
                "Settings > Reset to defaults."
            ) from exc
    cfg = Config()
    for key in cfg.known_keys():
        if key in data:
            setattr(cfg, key, data[key])
    cfg.validate()
    if create_if_missing and not path.exists():
        save_config(cfg)
    return cfg


def save_config(cfg: Config) -> None:
    cfg.validate()
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_toml(cfg.as_dict()), encoding="utf-8")
    log.debug("Saved configuration to %s", path)


def _dump_toml(data: dict[str, Any]) -> str:
    """Serialise a flat dict of str/int/bool/float into TOML text."""
    lines = [
        "# media-downloader configuration",
        "# Docs: see README.md — all keys are optional; missing keys use defaults.",
        "",
    ]
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
        else:
            escaped = (
                str(value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            lines.append(f'{key} = "{escaped}"')
    return "\n".join(lines) + "\n"


THEME_STYLES: dict[str, dict[str, str]] = {
    "dark": {
        "primary": "bold cyan",
        "accent": "bold magenta",
        "success": "bold green",
        "error": "bold red",
        "warning": "bold yellow",
        "dim": "dim",
        "banner": "bold cyan on default",
    },
    "light": {
        "primary": "bold blue",
        "accent": "bold magenta",
        "success": "bold green",
        "error": "bold red",
        "warning": "bold dark_orange",
        "dim": "dim",
        "banner": "bold blue on default",
    },
    "mono": {
        "primary": "bold",
        "accent": "bold",
        "success": "bold",
        "error": "bold",
        "warning": "bold",
        "dim": "dim",
        "banner": "bold",
    },
}


def theme_styles(theme: str) -> dict[str, str]:
    return THEME_STYLES.get(theme, THEME_STYLES["dark"])
