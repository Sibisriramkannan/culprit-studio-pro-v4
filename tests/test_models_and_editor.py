"""Tests for VideoConfig model, canvas_size, font resolution, and logging."""
from __future__ import annotations

import pytest
from pathlib import Path

from app.models import VideoConfig
from app.video_editor import canvas_size, RATIO_SIZES, CAPTION_PRESETS, _resolve_font
from app.log import get_logger, redact


class TestVideoConfig:
    def test_defaults(self):
        cfg = VideoConfig(story="A test story")
        assert cfg.language == "en"
        assert cfg.aspect_ratio == "9:16"
        assert cfg.duration_seconds == 30
        assert cfg.video_type == "short"
        assert cfg.character_id == "zuzu"
        assert cfg.image_provider == "huggingface"
        assert cfg.subtitle_enabled is True

    def test_1_1_ratio(self):
        cfg = VideoConfig(story="Test", aspect_ratio="1:1")
        assert cfg.aspect_ratio == "1:1"

    def test_16_9_ratio(self):
        cfg = VideoConfig(story="Test", aspect_ratio="16:9")
        assert cfg.aspect_ratio == "16:9"

    def test_font_fields(self):
        cfg = VideoConfig(
            story="Test",
            font_family="C:/Windows/Fonts/arial.ttf",
            font_style="bold",
            font_size=72,
        )
        assert cfg.font_family == "C:/Windows/Fonts/arial.ttf"
        assert cfg.font_style == "bold"
        assert cfg.font_size == 72

    def test_video_types(self):
        for vt in ["short", "story", "rhyme", "educational"]:
            cfg = VideoConfig(story="Test", video_type=vt)
            assert cfg.video_type == vt

    def test_invalid_video_type_rejected(self):
        with pytest.raises(Exception):
            VideoConfig(story="Test", video_type="invalid")

    def test_invalid_ratio_rejected(self):
        with pytest.raises(Exception):
            VideoConfig(story="Test", aspect_ratio="4:3")

    def test_duration_bounds(self):
        cfg = VideoConfig(story="Test", duration_seconds=10)
        assert cfg.duration_seconds == 10
        with pytest.raises(Exception):
            VideoConfig(story="Test", duration_seconds=5)
        with pytest.raises(Exception):
            VideoConfig(story="Test", duration_seconds=500)

    def test_music_volume(self):
        cfg = VideoConfig(story="Test", music_volume=0.25)
        assert cfg.music_volume == 0.25

    def test_youtube_schedule_fields(self):
        cfg = VideoConfig(
            story="Test",
            youtube_schedule_publish=True,
            youtube_publish_time="2026-01-15T18:00:00",
        )
        assert cfg.youtube_schedule_publish is True
        assert cfg.youtube_publish_time == "2026-01-15T18:00:00"


class TestCanvasSize:
    def test_9_16(self):
        assert canvas_size("9:16") == (1080, 1920)

    def test_16_9(self):
        assert canvas_size("16:9") == (1920, 1080)

    def test_1_1(self):
        assert canvas_size("1:1") == (1080, 1080)

    def test_unknown_defaults_to_9_16(self):
        assert canvas_size("unknown") == (1080, 1920)


class TestCaptionPresets:
    def test_all_presets_have_required_keys(self):
        required = {"size", "stroke", "bg", "font", "fill", "shadow", "y"}
        for name, cfg in CAPTION_PRESETS.items():
            for key in required:
                assert key in cfg, f"Preset '{name}' missing key '{key}'"

    def test_y_positions_valid(self):
        for name, cfg in CAPTION_PRESETS.items():
            assert 0.0 <= cfg["y"] <= 1.0, f"Preset '{name}' has invalid y={cfg['y']}"


class TestResolveFont:
    def test_returns_font_object(self):
        font = _resolve_font("heavy", 48, "en")
        assert font is not None

    def test_tamil_returns_font(self):
        font = _resolve_font("heavy", 48, "ta")
        assert font is not None

    def test_hindi_returns_font(self):
        font = _resolve_font("clean", 48, "hi")
        assert font is not None

    def test_explicit_path_fallback(self):
        # Non-existent path should fall back to auto-detect
        font = _resolve_font("heavy", 48, "en", font_family="/nonexistent/font.ttf")
        assert font is not None


class TestLogging:
    def test_get_logger(self):
        log = get_logger("Test")
        assert log is not None

    def test_redact_secrets(self):
        assert "nvapi-" not in redact("Bearer nvapi-abc123")
        assert "AIza" not in redact("key=AIzaSyAbcDefGhiJklMnoPqrStuVwXyZ")
        assert "sk-" not in redact("Authorization: Bearer sk-abc1234567890")

    def test_redact_empty(self):
        assert redact("") == ""
        assert redact(None) == ""
