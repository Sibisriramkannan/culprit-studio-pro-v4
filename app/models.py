from pydantic import BaseModel, Field
from typing import Literal, Optional

class StoryRequest(BaseModel):
    llm_provider: str="gemini"
    mode: Literal["builder","custom","autonomous"]="builder"
    user_input: str
    language: Literal["en","ta","hi"]="en"

class StoryResponse(BaseModel):
    title: str
    story: str
    summary: str=""
    suggested_duration: int=30

class VideoConfig(BaseModel):
    mode: Literal["manual","automation"]="manual"
    story_mode: Literal["builder","custom","autonomous"]="builder"
    story: str
    title: str=""
    language: Literal["en","ta","hi"]="en"
    llm_provider: str="gemini"

    voice_provider: str="edge"
    voice_id: str="en-US-JennyNeural"

    music_mode: Literal["auto","upload","none"]="auto"
    music_provider: str="library"
    music_mood: str="auto"
    music_path: Optional[str]=None

    art_style: str="Modern Cartoon"
    video_provider: str="none"
    animated_hook: bool=False

    caption_style: str="bold-stroke"
    effects: list[str]=["kenburns"]

    storage_mode: Literal["huggingface","download","both"]="download"
    aspect_ratio: Literal["9:16","16:9"]="9:16"
    duration_seconds: int=Field(30, ge=10, le=300)

    upload_to_youtube: bool=False
    youtube_privacy: Literal["private","unlisted","public"]="private"

class GenerateRequest(BaseModel):
    config: VideoConfig

class ScheduleRequest(BaseModel):
    name: str
    enabled: bool=True
    preset: Literal["every_2_hours","daily","twice_daily","weekly","custom"]="daily"
    local_time: str="18:00"
    second_local_time: Optional[str]=None
    weekday: int=0
    custom_cron: Optional[str]=None
    config: VideoConfig

class ScheduleUpdateRequest(BaseModel):
    enabled: Optional[bool]=None
    name: Optional[str]=None
