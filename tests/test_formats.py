"""Tests for format discovery, labelling and selection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_downloader import formats as fmt


def make_info():
    """A realistic yt-dlp-style info dict with merged (DASH) formats."""
    return {
        "id": "abc123",
        "title": "Example Video",
        "duration": 522,
        "formats": [
            # storyboards must be skipped
            {"format_id": "sb0", "ext": "mhtml", "vcodec": "none", "acodec": "none"},
            {"format_id": "sb1", "ext": "mhtml", "vcodec": "none", "acodec": "none"},
            # video-only streams
            {"format_id": "137", "ext": "mp4", "height": 1080, "fps": 30,
             "vcodec": "avc1.640028", "acodec": "none", "filesize": 61_000_000,
             "tbr": 2000},
            {"format_id": "136", "ext": "mp4", "height": 720, "fps": 30,
             "vcodec": "avc1.64001f", "acodec": "none", "filesize": 35_000_000,
             "tbr": 1200},
            {"format_id": "135", "ext": "mp4", "height": 480, "fps": 30,
             "vcodec": "avc1.4d401f", "acodec": "none", "filesize": 21_000_000,
             "tbr": 700},
            {"format_id": "313", "ext": "webm", "height": 2160, "fps": 60,
             "vcodec": "vp09.00.50.08", "acodec": "none", "filesize": 185_000_000,
             "tbr": 8000},
            # audio-only streams
            {"format_id": "140", "ext": "m4a", "vcodec": "none",
             "acodec": "mp4a.40.2", "abr": 128, "tbr": 129,
             "filesize": 8_000_000},
            {"format_id": "251", "ext": "webm", "vcodec": "none",
             "acodec": "opus", "abr": 160, "tbr": 160,
             "filesize": 7_000_000},
            # progressive (video+audio) legacy format
            {"format_id": "18", "ext": "mp4", "height": 360, "fps": 25,
             "vcodec": "avc1.42001E", "acodec": "mp4a.40.2",
             "filesize": 13_000_000, "tbr": 500, "abr": 96},
        ],
    }


def test_storyboards_excluded():
    fmts = fmt.build_format_list(make_info())
    assert all(f.format_id != "sb0" for f in fmts)


def test_classification():
    fmts = fmt.build_format_list(make_info())
    by_id = {f.format_id: f for f in fmts}
    assert by_id["137"].media_type == "video"
    assert not by_id["137"].has_audio
    assert by_id["140"].media_type == "audio"
    assert by_id["18"].media_type == "video"
    assert by_id["18"].has_audio  # progressive carries its own audio


def test_videos_sorted_best_first():
    fmts = fmt.build_format_list(make_info())
    heights = [f.height for f in fmts if f.media_type == "video"]
    assert heights[:3] == [2160, 1080, 720]


def test_audio_sorted_best_first():
    fmts = fmt.build_format_list(make_info())
    audios = [f for f in fmts if f.media_type == "audio"]
    assert audios[0].format_id == "251"  # 160 kbps > 128 kbps


def test_size_labels():
    fmts = fmt.build_format_list(make_info())
    by_id = {f.format_id: f for f in fmts}
    # 61_000_000 bytes = 58.2 MiB (binary units)
    assert by_id["137"].size_label() == "58.2 MB"
    # tbr-based estimate when no filesize
    estimated = fmt.FormatInfo(format_id="x", media_type="video", tbr=1000, duration=100)
    assert estimated.size_bytes() == 1000 * 1000 * 100 / 8
    assert estimated.size_label().startswith("~")


def test_pretty_codec():
    assert fmt.pretty_codec("avc1.640028") == "H.264"
    assert fmt.pretty_codec("vp09.00.50.08") == "VP9"
    assert fmt.pretty_codec("mp4a.40.2") == "AAC"
    assert fmt.pretty_codec("opus") == "Opus"
    assert fmt.pretty_codec(None) == "—"


def test_best_audio_bitrate():
    fmts = fmt.build_format_list(make_info())
    assert fmt.best_audio_bitrate(fmts) == 160


def test_video_selector_by_container():
    mp4 = fmt.video_selector(1080, "mp4")
    assert "avc1" in mp4 and "height<=1080" in mp4
    webm = fmt.video_selector(720, "webm")
    assert "vp9" in webm and "height<=720" in webm
    original = fmt.video_selector(None, "original")
    assert original == "bestvideo+bestaudio/best"
    fps = fmt.video_selector(1080, "original", fps=30)
    assert "[fps<=30]" in fps


def test_audio_selector():
    assert fmt.audio_selector(None) == "bestaudio/best"
    assert fmt.audio_selector(192) == "bestaudio[abr<=192]/bestaudio/best"


def test_smart_selector_modes():
    assert fmt.smart_selector("best", "original") == "bestvideo+bestaudio/best"
    assert "height<=1080" in fmt.smart_selector("balanced", "mp4")
    assert "height<=480" in fmt.smart_selector("small", "original")
    with pytest.raises(ValueError):
        fmt.smart_selector("ultra", "original")


def test_formats_under_limit():
    fmts = fmt.build_format_list(make_info())
    # 720p is 35 MB video + 8 MB audio (best) = 43 MB → fits in 50 MB
    fitting = fmt.formats_under_limit(fmts, 50)
    ids = [f.format_id for f, _total in fitting]
    assert "136" in ids and "137" not in ids
    totals = {f.format_id: total for f, total in fitting}
    assert totals["136"] == 35_000_000 + 7_000_000  # + best audio (251: 7 MB)


def test_formats_under_limit_tight():
    fmts = fmt.build_format_list(make_info())
    assert fmt.formats_under_limit(fmts, 10) == []  # nothing that small


def test_resolution_and_fps_choices():
    fmts = fmt.build_format_list(make_info())
    assert fmt.resolution_choices(fmts) == [2160, 1080, 720, 480, 360]
    assert 60.0 in fmt.fps_choices(fmts)


def test_image_formats_supported():
    info = {
        "title": "Insta post",
        "formats": [
            {"format_id": "img1", "ext": "jpg", "vcodec": "none",
             "acodec": "none", "filesize": 500_000, "height": 1080},
        ],
    }
    fmts = fmt.build_format_list(info)
    assert len(fmts) == 1
    assert fmts[0].media_type == "image"
    assert fmts[0].size_bytes() == 500_000


def test_single_format_info_without_formats_key():
    info = {"format_id": "18", "ext": "mp4", "height": 360, "duration": 100,
            "vcodec": "avc1", "acodec": "mp4a"}
    fmts = fmt.build_format_list(info)
    assert len(fmts) == 1
    assert fmts[0].has_video and fmts[0].has_audio
