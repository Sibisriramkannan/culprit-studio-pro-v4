from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)

    # LLM
    GEMINI_API_KEY: str|None=None
    GROQ_API_KEY: str|None=None
    COHERE_API_KEY: str|None=None
    MISTRAL_API_KEY: str|None=None
    TOGETHER_API_KEY: str|None=None
    OPENAI_API_KEY: str|None=None
    CLOUDFLARE_ACCOUNT_ID: str|None=None
    CLOUDFLARE_API_KEY: str|None=None

    # Image
    HUGGINGFACE_API_KEY: str|None=None
    DEEPAI_API_KEY: str|None=None
    SEGMIND_API_KEY: str|None=None
    STABILITY_API_KEY: str|None=None

    # Voice
    ELEVENLABS_API_KEY: str|None=None
    DEEPGRAM_API_KEY: str|None=None
    CARTESIA_API_KEY: str|None=None

    # Video
    FAL_API_KEY: str|None=None
    REPLICATE_API_KEY: str|None=None
    NOVITA_API_KEY: str|None=None
    MODELSLAB_API_KEY: str|None=None
    JSON2VIDEO_API_KEY: str|None=None
    KLING_API_KEY: str|None=None
    KLING_ACCESS_KEY: str|None=None
    KLING_SECRET_KEY: str|None=None
    PIXVERSE_API_KEY: str|None=None
    MINIMAX_API_KEY: str|None=None

    # NVIDIA Cosmos3 Nano hosted Preview API
    NVIDIA_API_KEY: str|None=None
    NVIDIA_COSMOS_BASE_URL: str='https://ai.api.nvidia.com/v1'
    NVIDIA_COSMOS_INFER_PATH: str='/infer'
    NVIDIA_COSMOS_RESOLUTION: str='720_16_9'
    NVIDIA_COSMOS_NUM_FRAMES: int=97
    NVIDIA_COSMOS_FPS: int=24
    NVIDIA_COSMOS_STEPS: int=35
    NVIDIA_COSMOS_GUIDANCE: float=4.0
    NVIDIA_COSMOS_TIMEOUT: int=900
    NVIDIA_COSMOS_NEGATIVE_PROMPT: str='blurry, distorted, low quality, text, watermark, morphing, warping, flickering'

    PIXVERSE_MODEL: str='v6'
    MINIMAX_VIDEO_MODEL: str='MiniMax-Hailuo-2.3-Fast'
    REPLICATE_VIDEO_OWNER: str='wan-video'
    REPLICATE_VIDEO_MODEL: str='wan-2.2-i2v-fast'

    # Storage
    HF_TOKEN: str|None=None
    HF_REPO_ID: str|None=None
    HF_REPO_TYPE: str='dataset'

    # YouTube
    YOUTUBE_CLIENT_SECRETS_FILE: str='client_secret.json'
    YOUTUBE_TOKEN_FILE: str='youtube_token.json'
    YOUTUBE_REDIRECT_URI: str='http://127.0.0.1:8000/auth/youtube/callback'

    OUTPUT_DIR: str='output'
    DATA_DIR: str='data'
    UPLOAD_DIR: str='uploads'
    APP_ENV: str='development'
    DEMO_MODE: bool=False

settings=Settings()
for d in [settings.OUTPUT_DIR, settings.DATA_DIR, settings.UPLOAD_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)
