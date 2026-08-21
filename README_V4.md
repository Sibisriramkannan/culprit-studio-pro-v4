# Culprit Studio Pro V4

V4 adds NVIDIA Cosmos3 Nano as the first-class hosted video generator and upgrades the automatic multi-provider failover router.

## Video routing

Default **Auto AI Router** order:

1. NVIDIA Cosmos3 Nano
2. PixVerse
3. MiniMax / Hailuo
4. fal.ai Wan
5. Replicate Wan
6. Novita Wan
7. ModelsLab Wan
8. Local FFmpeg cinematic-motion fallback

Permanent auth/billing/quota failures disable that provider for the rest of the job. Once a provider succeeds, it becomes sticky and is tried first on later scenes.

## NVIDIA Cosmos3 Nano

The V4 adapter targets NVIDIA's hosted Preview API style:

```env
NVIDIA_API_KEY=nvapi-...
NVIDIA_COSMOS_BASE_URL=https://ai.api.nvidia.com/v1
NVIDIA_COSMOS_INFER_PATH=/infer
```

It sends the reference scene image as a data URI and supports both a synchronous `b64_video` response and asynchronous NVCF `202` polling.

Default generation settings are intentionally shorter for testing/free-endpoint usage:

```env
NVIDIA_COSMOS_RESOLUTION=720_16_9
NVIDIA_COSMOS_NUM_FRAMES=97
NVIDIA_COSMOS_FPS=24
NVIDIA_COSMOS_STEPS=35
NVIDIA_COSMOS_GUIDANCE=4.0
```

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Put your own keys in `.env`, then validate:

```powershell
python -m py_compile app\config.py app\providers\video.py app\pipeline.py app\main.py app\video_editor.py
python -c "from app.providers.video import VideoRouterState, generate_scene; print('V4 VIDEO ROUTER OK')"
python -c "from app.main import app; print('V4 BACKEND OK')"
```

Run:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. For the first test choose **Auto AI Router** or **NVIDIA Cosmos3 Nano**, keep YouTube and Hugging Face upload off, and use a 10-15 second test video.

## V4 caption normalization

AI providers can return landscape video even when the project is a 9:16 Short. V4 now scales and center-crops the raw AI clip to the requested canvas before applying the selected foreground caption preset.

## Security

Never commit `.env`, OAuth tokens, or API keys. Rotate credentials that have been pasted into chats, screenshots, tickets, or repositories.
