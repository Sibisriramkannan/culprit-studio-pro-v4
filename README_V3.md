# Culprit Studio Pro V3

V3 focuses on production reliability and multilingual output.

## Major fixes

- Multi-AI video failover router: selected provider first, then other configured providers, then local FFmpeg fallback.
- Job-level circuit breaker: billing/auth/permanent failures are not retried for every scene.
- Added PixVerse V6 and MiniMax/Hailuo adapters using their current documented async APIs.
- Existing fal, Replicate, Novita and ModelsLab adapters remain in the fallback chain.
- Dynamic scene count based on requested video duration instead of a fixed five scenes.
- Character bible injected into every scene prompt for better continuity.
- Tamil/Hindi narration instructions and automatic Edge voice mapping.
- Captions are now overlaid AFTER AI video generation, so AI-generated clips receive foreground subtitles too.
- Foreground styles now materially differ (font family, size, stroke, background, placement and fill) instead of mostly looking identical.
- Indic captions use Unicode-capable system-font candidates (Nirmala UI on Windows; Noto/DejaVu fallback on Linux).
- UTF-8 file handling retained throughout planning/report files.

## First run

Use Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

## FFmpeg

`ffmpeg` and `ffprobe` must be available in PATH.

## Recommended video-router test

Set at least `PIXVERSE_API_KEY` and/or `MINIMAX_API_KEY`. Choose either in the UI and generate a 15-20 second private/download-only test first. The selected provider is tried first; permanent failures disable that provider for the remainder of that job.

## Tamil test

Choose Tamil in Step 1 and Step 2. Use Valluvar or Pallavi. The planner is instructed to produce Tamil narration/captions, TTS uses a Tamil Edge voice, and caption rendering prefers Nirmala UI on Windows.

## Security

Do not copy secrets into source files. Keep `.env`, `client_secret.json`, and `youtube_token.json` out of Git. Rotate any keys that were previously pasted into chat or screenshots before production use.

## Kling / JSON2Video note

Kling remains visible but is not falsely marked executable with the legacy single key because the current direct official auth contract needs to be verified with access/secret credentials. JSON2Video is classified as a cloud composition/render service rather than a generative-motion model, so it is not used as an AI-motion fallback in this release.
