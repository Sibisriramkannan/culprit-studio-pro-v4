from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CharacterProfile(BaseModel):
    id: str
    name: str
    description: str = ""
    appearance: str = ""
    personality: str = ""
    style: str = ""
    reference_images: list[str] = Field(default_factory=list)
    negative_prompt: str = "blurry, extra limbs, watermark, text overlay, distorted face"
    voice_id: Optional[str] = None


class Scene(BaseModel):
    number: int = 1
    duration: float = 5.0
    narration: str
    visual_prompt: str = ""
    motion_prompt: str = ""
    camera: str = "gentle push-in, eye-level"
    foreground_text: str = ""
    subtitle: str = ""
    music_mood: str = "auto"
    sfx: str = ""
    caption_style: Optional[str] = None

    @field_validator("narration")
    @classmethod
    def _narration_ok(cls, v: str) -> str:
        t = (v or "").strip()
        if not t:
            raise ValueError("scene narration is required")
        return t


class Story(BaseModel):
    title: str
    language: str = "en"
    genre: str = "kids"
    target_duration: int = 30
    description: str = ""
    hashtags: list[str] = Field(default_factory=list)
    character_bible: str = ""
    scenes: list[Scene]

    @field_validator("title")
    @classmethod
    def _title_ok(cls, v: str) -> str:
        t = (v or "").strip()
        if not t:
            raise ValueError("title is required")
        return t[:120]

    @field_validator("scenes")
    @classmethod
    def _scenes_ok(cls, v: list[Scene]) -> list[Scene]:
        if not v:
            raise ValueError("at least one scene is required")
        return v


class ImagePrompt(BaseModel):
    prompt: str
    negative_prompt: str = ""


class VideoPrompt(BaseModel):
    prompt: str
    negative_prompt: str = ""


class MotionPrompt(BaseModel):
    prompt: str
