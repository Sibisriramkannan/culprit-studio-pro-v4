from __future__ import annotations

from enum import Enum


class JobStage(str, Enum):
    QUEUED = "QUEUED"
    STORY_GENERATION = "STORY_GENERATION"
    SCENE_PLANNING = "SCENE_PLANNING"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    TTS_GENERATION = "TTS_GENERATION"
    MUSIC_GENERATION = "MUSIC_GENERATION"
    SUBTITLE_GENERATION = "SUBTITLE_GENERATION"
    COMPOSITING = "COMPOSITING"
    THUMBNAIL = "THUMBNAIL"
    YOUTUBE_UPLOAD = "YOUTUBE_UPLOAD"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    # Retry / fallback states
    RETRYING = "RETRYING"
    FALLBACK_PROVIDER = "FALLBACK_PROVIDER"


PROGRESS = {
    JobStage.QUEUED: 0,
    JobStage.STORY_GENERATION: 5,
    JobStage.SCENE_PLANNING: 10,
    JobStage.TTS_GENERATION: 18,
    JobStage.IMAGE_GENERATION: 28,
    JobStage.VIDEO_GENERATION: 55,
    JobStage.MUSIC_GENERATION: 70,
    JobStage.SUBTITLE_GENERATION: 78,
    JobStage.COMPOSITING: 86,
    JobStage.THUMBNAIL: 92,
    JobStage.YOUTUBE_UPLOAD: 96,
    JobStage.COMPLETED: 100,
    JobStage.FAILED: 100,
}


class JobEvent:
    """Lightweight event attached to a job for observability."""

    def __init__(self, stage: str, message: str, *, provider: str = "",
                 error_type: str = "", retryable: bool = False) -> None:
        self.stage = stage
        self.message = message
        self.provider = provider
        self.error_type = error_type
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "message": self.message,
            "provider": self.provider,
            "error_type": self.error_type,
            "retryable": self.retryable,
        }
