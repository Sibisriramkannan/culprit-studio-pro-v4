# Setup Guide — Culprit Studio Pro V4

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | 3.12 recommended |
| FFmpeg | 6.x+ | Must be on PATH or set via `FFMPEG_PATH` |
| Git | any | For version control |
| Windows / Linux / macOS | — | pathlib-based, no Unix assumptions |

---

## 1. Clone the repository

```
git clone <your-repo-url>
cd culprit_studio_pro
```

---

## 2. Create a virtual environment

```
python -m venv .venv
```

Activate it:

- Windows: `.\.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

---

## 3. Install dependencies

```
pip install -r requirements.txt
```

---

## 4. Install FFmpeg

FFmpeg must be installed separately and available on `PATH`, or its path must be
set in `.env`:

```
FFMPEG_PATH=C:\tools\ffmpeg\bin\ffmpeg.exe
```

Download from: https://ffmpeg.org/download.html

---

## 5. Configure environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit `.env` — see `.env.example` for all supported keys.

**Never commit `.env` to version control.**

---

## 6. YouTube OAuth setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **YouTube Data API v3**.
3. Create OAuth 2.0 credentials (Desktop app type).
4. Download the credentials JSON and save it as `client_secret.json` in the
   project root.
5. On first run, a browser window will open for OAuth consent.
6. After authorization, `youtube_token.json` is saved automatically.

---

## 7. Run the application

```
python -m uvicorn app.main:app --reload --port 8000
```

Open: http://localhost:8000

---

## 8. Run tests

```
python -m pytest tests/ -v
```

All 133 tests should pass without any paid API keys.

---

## 9. Provider configuration

| Provider | Environment Variable | Free Tier |
|----------|----------------------|-----------|
| Gemini (LLM) | `GEMINI_API_KEY` | Yes (limited) |
| Groq (LLM) | `GROQ_API_KEY` | Yes (limited) |
| Mistral (LLM) | `MISTRAL_API_KEY` | Paid |
| OpenAI (LLM/image) | `OPENAI_API_KEY` | Paid |
| HuggingFace (image) | `HUGGINGFACE_API_KEY` | Yes (limited) |
| NVIDIA Cosmos (video) | `NVIDIA_API_KEY` | Preview (verify) |
| fal.ai (video) | `FAL_API_KEY` | Paid per generation |
| Replicate (video) | `REPLICATE_API_TOKEN` | Paid per generation |
| Novita AI (video) | `NOVITA_API_KEY` | Paid per generation |
| ModelsLab (video) | `MODELSLAB_API_KEY` | Paid per generation |
| PixVerse (video) | `PIXVERSE_API_KEY` | Paid per generation |
| MiniMax (video) | `MINIMAX_API_KEY` | Paid per generation |
| ElevenLabs (TTS) | `ELEVENLABS_API_KEY` | Free tier (limited) |
| Deepgram (TTS) | `DEEPGRAM_API_KEY` | Paid |
| HuggingFace (storage) | `HUGGINGFACE_API_KEY` | Yes |
| AWS S3 (storage) | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_ENDPOINT_URL` | Paid |

Edge TTS (Microsoft) is always available as a free fallback voice provider with
no API key required.

### Provider order override

To control which video provider is tried first:

```
VIDEO_PROVIDER_ORDER=wan-fal,ltx-fal,pixverse,minimax,fal-wan22,replicate,novita,modelslab
```

---

## 10. Tamil / multilingual support

Tamil is a first-class language. To ensure correct Tamil rendering:

- The pipeline selects a Unicode-capable font automatically (`NotoSansTamil`,
  `Lohit Tamil`, or system fallback).
- For TTS in Tamil, use Edge TTS with a `ta-IN-*` voice, ElevenLabs
  multilingual v2, or Deepgram.
- Subtitle generation produces Tamil-encoded SRT/ASS files automatically.

Font installation (Windows):

- Install [Noto Sans Tamil](https://fonts.google.com/noto/specimen/Noto+Sans+Tamil)
  for best rendering quality.
- Without Raqm, PIL falls back to basic layout (ligatures may be approximate).
  This does not break functionality.

---

## 11. Local model setup (optional)

The application does **not** automatically download model weights.

If you want to run open models locally (Wan, HunyuanVideo, LTX-Video), use
the separate setup script (when available):

```
python scripts/setup_local_models.py
```

This is optional — all models are available remotely via fal.ai, Replicate,
or Novita.

---

## 12. Kaggle worker (optional)

The Kaggle notebook (`notebooks/culprit_kaggle_pro.ipynb`) can be used as an
on-demand GPU worker:

1. Upload the notebook to Kaggle.
2. Set Kaggle secrets for your API keys.
3. Trigger a run manually.
4. The notebook fetches a job from the queue, generates artifacts, and uploads
   results to HuggingFace storage.
5. The main application polls for the result.

The main API does not depend on a running Kaggle session.

---

## 13. Scheduler

The built-in APScheduler runs automatically on startup. It polls for scheduled
YouTube publishes and pending jobs.

To disable: set `SCHEDULER_ENABLED=false` in `.env`.
