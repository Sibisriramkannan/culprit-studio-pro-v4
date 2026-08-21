"""Tests for pipeline state: JobStage, PROGRESS, JobEvent."""
from __future__ import annotations

import pytest
from app.pipeline_state import JobStage, PROGRESS, JobEvent


class TestJobStage:
    def test_all_stages_exist(self):
        expected = [
            "QUEUED", "STORY_GENERATION", "SCENE_PLANNING",
            "IMAGE_GENERATION", "VIDEO_GENERATION", "TTS_GENERATION",
            "MUSIC_GENERATION", "SUBTITLE_GENERATION", "COMPOSITING",
            "THUMBNAIL", "YOUTUBE_UPLOAD", "COMPLETED", "FAILED",
            "RETRYING", "FALLBACK_PROVIDER",
        ]
        for name in expected:
            assert hasattr(JobStage, name)

    def test_stage_values_are_strings(self):
        for stage in JobStage:
            assert isinstance(stage.value, str)


class TestProgress:
    def test_queued_is_zero(self):
        assert PROGRESS[JobStage.QUEUED] == 0

    def test_completed_is_100(self):
        assert PROGRESS[JobStage.COMPLETED] == 100

    def test_failed_is_100(self):
        assert PROGRESS[JobStage.FAILED] == 100

    def test_monotonic(self):
        """Progress should generally increase through stages."""
        stages = [
            JobStage.QUEUED,
            JobStage.STORY_GENERATION,
            JobStage.SCENE_PLANNING,
            JobStage.TTS_GENERATION,
            JobStage.IMAGE_GENERATION,
            JobStage.VIDEO_GENERATION,
            JobStage.MUSIC_GENERATION,
            JobStage.SUBTITLE_GENERATION,
            JobStage.COMPOSITING,
            JobStage.THUMBNAIL,
            JobStage.YOUTUBE_UPLOAD,
            JobStage.COMPLETED,
        ]
        for i in range(1, len(stages)):
            assert PROGRESS[stages[i]] >= PROGRESS[stages[i - 1]]


class TestJobEvent:
    def test_basic_event(self):
        ev = JobEvent("VIDEO_GENERATION", "Trying NVIDIA")
        assert ev.stage == "VIDEO_GENERATION"
        assert ev.message == "Trying NVIDIA"
        assert ev.provider == ""

    def test_with_provider(self):
        ev = JobEvent("VIDEO_GENERATION", "Success", provider="pixverse")
        assert ev.provider == "pixverse"

    def test_error_event(self):
        ev = JobEvent(
            "VIDEO_GENERATION", "Auth failed",
            provider="nvidia", error_type="AUTH", retryable=False,
        )
        assert ev.error_type == "AUTH"
        assert ev.retryable is False

    def test_to_dict(self):
        ev = JobEvent(
            "COMPOSITING", "Starting composition",
            provider="ffmpeg",
        )
        d = ev.to_dict()
        assert d["stage"] == "COMPOSITING"
        assert d["message"] == "Starting composition"
        assert d["provider"] == "ffmpeg"
        assert d["error_type"] == ""
        assert d["retryable"] is False
