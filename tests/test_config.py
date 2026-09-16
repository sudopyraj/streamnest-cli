"""Tests for configuration loading, validation and persistence."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_downloader.config import Config, ConfigError, load_config, save_config


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDIA_DOWNLOADER_CONFIG_DIR", str(tmp_path))
    return tmp_path


def test_defaults_load_and_create(temp_config_dir):
    cfg = load_config()
    assert cfg.default_video_quality == "1080p"
    assert cfg.theme == "dark"
    assert cfg.max_concurrent_downloads == 3
    # config file auto-created on first load
    assert (temp_config_dir / "config.toml").exists()


def test_roundtrip_save_load(temp_config_dir):
    cfg = load_config()
    cfg.download_directory = "~/Videos/yt"
    cfg.theme = "light"
    cfg.max_concurrent_downloads = 5
    save_config(cfg)

    loaded = load_config()
    assert loaded.download_directory == "~/Videos/yt"
    assert loaded.theme == "light"
    assert loaded.max_concurrent_downloads == 5


def test_partial_file_uses_defaults(temp_config_dir):
    (temp_config_dir / "config.toml").write_text(
        'download_directory = "/tmp/x"\ntheme = "mono"\n', encoding="utf-8"
    )
    cfg = load_config()
    assert cfg.download_directory == "/tmp/x"
    assert cfg.theme == "mono"
    # missing keys fall back
    assert cfg.default_video_quality == "1080p"


def test_invalid_values_rejected(temp_config_dir):
    cfg = Config()
    with pytest.raises(ConfigError):
        cfg.default_video_quality = "4320p Ultra"
        cfg.validate()
    with pytest.raises(ConfigError):
        cfg.max_concurrent_downloads = 99
        cfg.validate()
    with pytest.raises(ConfigError):
        cfg.theme = "solarized"
        cfg.validate()
    with pytest.raises(ConfigError):
        cfg.filename_template = "../../etc/%(title)s"
        cfg.validate()


def test_toml_dump_escapes_strings(temp_config_dir):
    cfg = Config()
    cfg.filename_template = 'weird "quoted" name.%(ext)s'
    save_config(cfg)
    loaded = load_config()
    assert loaded.filename_template == cfg.filename_template


def test_corrupt_toml_raises_configerror(temp_config_dir):
    (temp_config_dir / "config.toml").write_text(
        "this is = = not valid [ toml", encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_config()


def test_resolved_download_dir_expands_home(temp_config_dir):
    cfg = Config(download_directory="~/Downloads")
    resolved = cfg.resolved_download_dir()
    assert str(resolved).startswith(str(Path.home()))
    assert not str(resolved).startswith("~")
