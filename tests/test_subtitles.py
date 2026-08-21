"""Tests for subtitle generation: SRT, ASS, Tamil Unicode, timing."""
from __future__ import annotations

import pytest
from pathlib import Path

from app.subtitles import (
    _fmt_srt, _fmt_ass, _split_into_captions,
    _compute_scene_times, generate_srt, generate_ass,
)


class TestFmtSrt:
    def test_zero(self):
        assert _fmt_srt(0) == "00:00:00,000"

    def test_simple(self):
        assert _fmt_srt(65.5) == "00:01:05,500"

    def test_hours(self):
        assert _fmt_srt(3661.123) == "01:01:01,123"


class TestFmtAss:
    def test_zero(self):
        assert _fmt_ass(0) == "0:00:00.00"

    def test_simple(self):
        assert _fmt_ass(65.5) == "0:01:05.50"

    def test_hours(self):
        result = _fmt_ass(3661.12)
        # Allow floating-point tolerance in centiseconds
        assert result.startswith("1:01:01.")
        assert result.endswith(".12") or result.endswith(".11")


class TestSplitIntoCaptions:
    def test_short_text(self):
        result = _split_into_captions("Hello world", 0.0, 5.0)
        assert len(result) == 1
        assert result[0][2] == "Hello world"

    def test_long_text_splits(self):
        text = "This is a longer sentence that should be split into multiple caption segments for readability"
        result = _split_into_captions(text, 0.0, 10.0, max_chars=30)
        assert len(result) > 1
        for start, end, chunk in result:
            assert len(chunk) <= 30 or " " not in chunk

    def test_timing_proportional(self):
        text = "Short text here and this is a longer text segment"
        result = _split_into_captions(text, 0.0, 10.0, max_chars=20)
        # Each segment should have positive duration
        for start, end, chunk in result:
            assert end > start

    def test_empty_text(self):
        result = _split_into_captions("", 0.0, 5.0)
        assert len(result) == 1  # returns the empty string as one segment


class TestComputeSceneTimes:
    def test_equal_scenes(self):
        scenes = [
            {"narration": "abc"},
            {"narration": "def"},
        ]
        times = _compute_scene_times(scenes, 10.0)
        assert len(times) == 2
        # Equal length narrations → equal time allocation
        assert abs(times[0][1] - times[0][0] - 5.0) < 0.01

    def test_proportional_timing(self):
        scenes = [
            {"narration": "short"},
            {"narration": "this is a much longer narration text"},
        ]
        times = _compute_scene_times(scenes, 10.0)
        dur_0 = times[0][1] - times[0][0]
        dur_1 = times[1][1] - times[1][0]
        # Second scene should get more time
        assert dur_1 > dur_0


class TestGenerateSrt:
    def test_basic_srt(self, tmp_path):
        scenes = [
            {"narration": "Hello world"},
            {"narration": "Goodbye world"},
        ]
        out = str(tmp_path / "test.srt")
        generate_srt(scenes, out, total_duration=10.0)
        content = Path(out).read_text(encoding="utf-8")
        assert "1\n" in content
        assert "2\n" in content
        assert "-->" in content
        assert "Hello world" in content

    def test_tamil_srt(self, tmp_path, tamil_scenes):
        out = str(tmp_path / "tamil.srt")
        generate_srt(tamil_scenes, out, total_duration=10.0)
        content = Path(out).read_text(encoding="utf-8")
        assert "வணக்கம்" in content
        assert "பாண்டா" in content

    def test_empty_narration_skipped(self, tmp_path):
        scenes = [
            {"narration": ""},
            {"narration": "Valid scene"},
        ]
        out = str(tmp_path / "empty.srt")
        generate_srt(scenes, out, total_duration=10.0)
        content = Path(out).read_text(encoding="utf-8")
        assert "Valid scene" in content


class TestGenerateAss:
    def test_basic_ass(self, tmp_path):
        scenes = [
            {"narration": "Hello world"},
        ]
        out = str(tmp_path / "test.ass")
        generate_ass(scenes, out, total_duration=5.0, style="bold-stroke")
        content = Path(out).read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Dialogue:" in content
        assert "Hello world" in content

    def test_tamil_ass_uses_unicode_font(self, tmp_path, tamil_scenes):
        out = str(tmp_path / "tamil.ass")
        generate_ass(tamil_scenes, out, total_duration=10.0, language="ta")
        content = Path(out).read_text(encoding="utf-8")
        assert "Nirmala UI" in content
        assert "வணக்கம்" in content

    def test_style_variants(self, tmp_path):
        scenes = [{"narration": "Test"}]
        for style in ["bold-stroke", "sleek", "karaoke", "minimal"]:
            out = str(tmp_path / f"{style}.ass")
            generate_ass(scenes, out, total_duration=5.0, style=style)
            assert Path(out).exists()
