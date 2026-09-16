"""Tests for utils: sizes, durations, quality and selection parsing."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_downloader import utils


def test_human_size():
    assert utils.human_size(None) == "—"
    assert utils.human_size(0) == "0 B"
    assert utils.human_size(1024) == "1.0 KB"
    assert utils.human_size(1536) == "1.5 KB"
    assert utils.human_size(10 * 1024 * 1024) == "10.0 MB"
    assert utils.human_size(-5) == "—"


def test_human_duration():
    assert utils.human_duration(None) == "—"
    assert utils.human_duration(0) == "00:00"
    assert utils.human_duration(42) == "00:42"
    assert utils.human_duration(522) == "08:42"
    assert utils.human_duration(3671) == "1:01:11"


def test_parse_size_mb():
    assert utils.parse_size_mb("50") == 50.0
    assert utils.parse_size_mb("50MB") == 50.0
    assert utils.parse_size_mb("1.5") == 1.5
    assert utils.parse_size_mb(100) == 100.0
    with pytest.raises(ValueError):
        utils.parse_size_mb("banana")
    with pytest.raises(ValueError):
        utils.parse_size_mb("-4")


def test_parse_quality():
    assert utils.parse_quality("1080p") == 1080
    assert utils.parse_quality("720") == 720
    assert utils.parse_quality("best") is None
    assert utils.parse_quality(None) is None
    with pytest.raises(ValueError):
        utils.parse_quality("1080p Ultra HD")
    with pytest.raises(ValueError):
        utils.parse_quality("12p")


def test_parse_index_list():
    assert utils.parse_index_list("1-3,5", 10) == [1, 2, 3, 5]
    assert utils.parse_index_list("7", 10) == [7]
    assert utils.parse_index_list("2 - 4", 10) == [2, 3, 4]
    with pytest.raises(ValueError):
        utils.parse_index_list("0-2", 10)     # 1-based indexing
    with pytest.raises(ValueError):
        utils.parse_index_list("1-99", 10)    # out of range
    with pytest.raises(ValueError):
        utils.parse_index_list("x,y", 10)
    with pytest.raises(ValueError):
        utils.parse_index_list("", 10)


def test_clamp():
    assert utils.clamp(10, 1, 8) == 8
    assert utils.clamp(0, 1, 8) == 1
    assert utils.clamp(4, 1, 8) == 4
