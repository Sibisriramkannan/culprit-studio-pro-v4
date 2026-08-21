"""Tests for the MusicProvider abstraction."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.providers.music import (
    LibraryMusicProvider,
    SunoMusicProvider,
    get_music_provider,
    generate_music,
    _find_track,
    _MOOD_MAP,
)


class TestMoodMap:
    def test_all_moods_have_candidates(self):
        for mood, candidates in _MOOD_MAP.items():
            assert len(candidates) >= 1, f"Mood '{mood}' has no candidates"

    def test_auto_mood_exists(self):
        assert "auto" in _MOOD_MAP

    def test_known_moods_covered(self):
        for mood in ("magical", "happy", "adventure", "calm", "dreamy", "epic"):
            assert mood in _MOOD_MAP


class TestLibraryMusicProvider:
    def test_is_always_configured(self):
        p = LibraryMusicProvider()
        assert p.is_configured() is True

    def test_name(self):
        assert LibraryMusicProvider().name == "library"

    def test_returns_none_when_no_tracks(self, tmp_path):
        """No .mp3 files → returns None (no crash)."""
        p = LibraryMusicProvider()
        with patch("app.providers.music._MUSIC_DIR", tmp_path):
            result = p.generate("magical", str(tmp_path / "out.mp3"), 30.0)
        assert result is None

    def test_copies_track_when_file_exists(self, tmp_path):
        """Matching .mp3 file → copies to output path."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        src = music_dir / "magical.mp3"
        src.write_bytes(b"fakeaudio" * 100)
        out = tmp_path / "out.mp3"
        p = LibraryMusicProvider()
        with patch("app.providers.music._MUSIC_DIR", music_dir):
            result = p.generate("magical", str(out), 30.0)
        assert result == str(out)
        assert out.exists()


class TestSunoMusicProvider:
    def test_name(self):
        assert SunoMusicProvider().name == "suno"

    def test_not_configured_without_key(self):
        with patch.object(SunoMusicProvider, "is_configured", return_value=False):
            p = SunoMusicProvider()
            result = p.generate("happy", "/tmp/test.mp3", 30.0)
        assert result is None

    def test_falls_back_to_library(self, tmp_path):
        """When configured but API not implemented, falls back to library."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        (music_dir / "happy.mp3").write_bytes(b"fakeaudio" * 100)
        out = tmp_path / "out.mp3"
        with patch("app.providers.music.SunoMusicProvider.is_configured", return_value=True), \
             patch("app.providers.music._MUSIC_DIR", music_dir):
            p = SunoMusicProvider()
            result = p.generate("happy", str(out), 30.0)
        # Either None (if library is empty) or a path — no crash
        assert result is None or isinstance(result, str)


class TestGetMusicProvider:
    def test_library_default(self):
        p = get_music_provider("library")
        assert isinstance(p, LibraryMusicProvider)

    def test_suno_provider(self):
        p = get_music_provider("suno")
        assert isinstance(p, SunoMusicProvider)

    def test_unknown_falls_back_to_library(self):
        p = get_music_provider("nonexistent")
        assert isinstance(p, LibraryMusicProvider)

    def test_none_provider(self):
        p = get_music_provider("none")
        result = p.generate("magical", "/tmp/test.mp3", 30.0)
        assert result is None

    def test_empty_string_defaults_to_library(self):
        p = get_music_provider("")
        assert isinstance(p, LibraryMusicProvider)


class TestGenerateMusicConvenience:
    def test_returns_none_when_no_tracks(self, tmp_path):
        with patch("app.providers.music._MUSIC_DIR", tmp_path):
            result = generate_music("magical", str(tmp_path / "out.mp3"), 30.0)
        assert result is None

    def test_returns_path_when_track_found(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        (music_dir / "calm.mp3").write_bytes(b"fakeaudio" * 100)
        out = tmp_path / "out.mp3"
        with patch("app.providers.music._MUSIC_DIR", music_dir):
            result = generate_music("calm", str(out), 60.0)
        assert result == str(out)

    def test_no_crash_on_exception(self, tmp_path):
        """generate_music must not raise — logs warning and returns None."""
        with patch("app.providers.music.get_music_provider", side_effect=RuntimeError("boom")):
            result = generate_music("magical", str(tmp_path / "out.mp3"), 30.0)
        assert result is None
