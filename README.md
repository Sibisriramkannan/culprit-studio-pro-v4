# Culprit Studio Pro V2

A pro-level, responsive personal AI video factory with two distinct workflows:

- **Manual Studio** — human review before generation
- **Automation Studio** — scheduled autonomous generation and optional YouTube upload

## Main UI
- Home dashboard with generation metrics, YouTube connection status, live-style performance graph and recent jobs
- Manual wizard:
  1. AI Story Builder or Custom Story
  2. English/Tamil/Hindi + 4 male / 4 female preview voices
  3. Auto-match music or upload your own
  4. Visual art preset + moving-video model
  5. Foreground caption presets with previews
  6. Effects with animated previews
  7. Storage, ratio, duration and optional YouTube upload
- Automation wizard:
  - AI Story Builder
  - Direct Full Prompt
  - Autonomous one-line topic direction
  - same production settings as Manual
  - final local-time scheduler trigger
- Scheduler List:
  - every 2 hours
  - daily
  - twice daily
  - weekly
  - custom cron
  - Run now / Pause / Resume / Delete
- Settings / YouTube OAuth status

## Important architecture note
The UI exposes several AI video providers, but only adapters marked ready are executable. Providers marked `experimental` are visible for product design but are intentionally blocked until their *current* endpoint/model contract is configured. This prevents silent credit burn against stale APIs.

## Local Windows setup — use Python 3.12
Do **not** use the old Python 3.14 virtual environment.

```powershell
cd "C:\path\to\culprit_studio_pro"

py -3.12 --version

# If an old .venv is locked:
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
cmd /c "rmdir /s /q .venv"

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python --version
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

Copy-Item .env.example .env
notepad .env
```

Run:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

### Recommended first test
Use:
- LLM: Gemini
- Voice: prototype Edge voice
- Music: none
- Art: Modern Cartoon
- Video model: Smart Motion
- Storage: Download
- Ratio: 9:16
- Duration: 20–30 seconds
- YouTube upload: OFF

This validates the entire orchestration layer before spending video-generation credits.

## YouTube OAuth
1. Enable YouTube Data API v3 in Google Cloud.
2. Create/configure a Web Application OAuth client.
3. Add this Authorized Redirect URI:
   `http://127.0.0.1:8000/auth/youtube/callback`
4. Put the downloaded OAuth JSON in the project root as:
   `client_secret.json`
5. Keep these ignored:
   `client_secret.json`
   `youtube_token.json`
6. Open **Settings → Connect YouTube**.

## Scheduler behavior
The local scheduler runs only while the Culprit backend process is running.

For 24/7 autonomous execution, deploy the scheduler/worker on an always-on cloud service. Kaggle is designed here as a controlled batch worker, not the permanent scheduler.

## Kaggle batch use
The original Kaggle notebook is retained. Upload/extract the project to `/kaggle/working/culprit_studio_pro`, add provider keys under Kaggle Secrets, install dependencies, and run `scripts/run_batch.py`.

For automation testing on Kaggle, manually invoke a batch; do not rely on Kaggle as an always-on clock scheduler.

## Security
All API keys previously pasted into chat should be rotated before use.
Never place provider secrets in `app/static`, GitHub, screenshots, or a public Hugging Face repository.
