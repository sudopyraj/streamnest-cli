"""Tests for URL validation and filename sanitisation (security)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_downloader.security import (
    SecurityError,
    UnsafePathError,
    safe_join,
    sanitize_filename,
    validate_output_template,
    validate_url,
)

# ----------------------------------------------------------------------
# URL validation
# ----------------------------------------------------------------------

GOOD_YOUTUBE = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "http://youtube.com/watch?v=abcdefghijk",
    "https://m.youtube.com/watch?v=abcdefghijk&t=30",
    "https://youtu.be/abcdefghijk",
    "https://www.youtube.com/shorts/abcdefghijk",
    "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx",
    "https://music.youtube.com/watch?v=abcdefghijk",
    "https://www.youtube.com/embed/abcdefghijk",
]

GOOD_INSTAGRAM = [
    "https://www.instagram.com/p/CxYzAbCdEfG/",
    "https://instagram.com/reel/CxYzAbCdEfG/",
    "https://www.instagram.com/reels/CxYzAbCdEfG/",
    "https://m.instagram.com/tv/CxYzAbCdEfG/",
    "https://instagr.am/p/CxYzAbCdEfG/",
]


@pytest.mark.parametrize("url", GOOD_YOUTUBE)
def test_valid_youtube_urls(url):
    platform, normalized = validate_url(url)
    assert platform == "YouTube"
    assert normalized.startswith("https://")


@pytest.mark.parametrize("url", GOOD_INSTAGRAM)
def test_valid_instagram_urls(url):
    platform, normalized = validate_url(url)
    assert platform == "Instagram"
    assert normalized.startswith("https://")


BAD_URLS = [
    "",
    "not a url at all",
    "ftp://youtube.com/watch?v=abcdefghijk",
    "http://169.254.169.254/latest/meta-data",           # SSRF: cloud metadata
    "http://localhost:8080/watch?v=abcdefghijk",         # SSRF: localhost
    "http://2130706433/watch?v=abcdefghijk",             # IP as integer
    "https://evil.com/youtube.com/watch?v=abcdefghijk",   # not a yt host
    "https://youtube.com.evil.net/watch?v=abcdefghijk",   # suffix trick
    "https://fake-youtube.com/watch?v=abcdefghijk",
    "https://www.youtube.com/",                           # bare domain
    "https://www.youtube.com/watch",                      # no v= param
    "https://www.youtube.com/playlist",                   # no list= param
    "https://youtu.be/",                                  # no video id
    "https://www.youtube.com/shorts/",                    # no shorts id
    "https://www.instagram.com/",                         # bare domain
    "https://www.instagram.com/stories/user/123/",        # stories need auth
    "https://www.instagram.com/explore/tags/cats/",
    "http://youtube.com@evil.example/watch?v=abcdefghijk", # userinfo trick
    "https://example.com",
    "https://tiktok.com/@user/video/123",
]


@pytest.mark.parametrize("url", BAD_URLS)
def test_invalid_urls_rejected(url):
    with pytest.raises(SecurityError):
        validate_url(url)


def test_url_length_cap():
    with pytest.raises(SecurityError):
        validate_url("https://www.youtube.com/watch?v=abcdefghijk&" + "x" * 3000)


# ----------------------------------------------------------------------
# Filename sanitisation
# ----------------------------------------------------------------------

def test_sanitize_removes_path_characters():
    assert "/" not in sanitize_filename('video/name<>:"|?*.mp4')
    assert "\\" not in sanitize_filename("back\\slash.mp4")


def test_sanitize_blocks_traversal():
    for name in ["../../etc/passwd", "..\\..\\windows\\system32", "..."]:
        clean = sanitize_filename(name)
        assert ".." not in clean
        assert not clean.startswith(("/", "\\"))


def test_sanitize_reserved_windows_names():
    for reserved in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT9"):
        clean = sanitize_filename(f"{reserved}.mp4")
        assert clean.startswith("_")


def test_sanitize_control_chars_and_unicode():
    assert "\x00" not in sanitize_filename("bad\x00name.mp4")
    assert "\x1b" not in sanitize_filename("esc\x1bname.mp4")


def test_sanitize_truncates_long_names():
    clean = sanitize_filename("x" * 500 + ".mp4", max_length=180)
    assert len(clean) <= 180
    assert clean.endswith(".mp4")


def test_sanitize_empty_falls_back():
    assert sanitize_filename("") == "download"
    assert sanitize_filename("   ") == "download"


def test_sanitize_collapses_whitespace():
    assert sanitize_filename("my   great    video.mp4") == "my great video.mp4"


def test_sanitize_normal_name_untouched():
    assert sanitize_filename("Creator Name - Video Title.mp4") == (
        "Creator Name - Video Title.mp4"
    )


# ----------------------------------------------------------------------
# Path safety
# ----------------------------------------------------------------------

def test_safe_join_contains_path():
    target = safe_join("/tmp/downloads", "video.mp4")
    assert str(target).startswith(str(Path("/tmp/downloads").resolve()))


def test_safe_join_rejects_traversal():
    with pytest.raises(UnsafePathError):
        safe_join("/tmp/downloads", "../../etc/passwd")


def test_safe_join_rejects_absolute_injection():
    with pytest.raises(UnsafePathError):
        safe_join("/tmp/downloads", "/etc/passwd")


# ----------------------------------------------------------------------
# Output template validation
# ----------------------------------------------------------------------

def test_template_accepts_standard():
    assert validate_output_template("%(title)s - %(creator)s.%(ext)s")


def test_template_rejects_separators_and_traversal():
    for bad in ["%(title)s/%(ext)s", "..\\%(title)s", "../../x", "~/Videos/%(ext)s"]:
        with pytest.raises(SecurityError):
            validate_output_template(bad)
