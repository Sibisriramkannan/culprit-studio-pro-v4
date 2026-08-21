# Troubleshooting — Culprit Studio Pro V4

---

## FastAPI fails to start

**Symptom:** `uvicorn app.main:app` exits immediately or raises an ImportError.

**Checks:**
1. Virtual environment is activated: `.\.venv\Scripts\Activate.ps1`
2. Dependencies installed: `pip install -r requirements.txt`
3. Syntax errors: `python -m compileall app -q`
4. Missing `.env` file — copy from `.env.example`

---

## Tests fail

**Symptom:** `pytest tests/` reports failures.

**Checks:**
1. Run `python -m compileall app -q` first to catch syntax errors.
2. Ensure no paid provider is required — all tests use mocks.
3. PIL Raqm warnings (`UserWarning: Raqm layout was requested`) are **non-blocking** and safe to ignore.
4. If `_CtxLogger` raises `TypeError: Logger._log() got an unexpected keyword argument`, check `app/log.py` — `_CtxLogger` must be a `logging.Logger` subclass (not `LoggerAdapter`).

---

## FFmpeg not found

**Symptom:** `FileNotFoundError: [WinError 2]` or `ffmpeg: command not found`.

**Fix:**
- Install FFmpeg: https://ffmpeg.org/download.html
- Add to PATH, **or** set in `.env`:
  ```
  FFMPEG_PATH=C:\tools\ffmpeg\bin\ffmpeg.exe
  ```

---

## Tamil text renders as boxes or question marks

**Symptom:** Tamil characters appear as `□□□` or `???` in output video.

**Causes and fixes:**
1. **No Tamil-capable font installed** — Install [Noto Sans Tamil](https://fonts.google.com/noto/specimen/Noto+Sans+Tamil).
2. **Raqm not available** — PIL falls back to basic layout; ligatures may not be perfect but the text is still legible.
3. **Wrong font selected in UI** — ensure `font_language` is set to `ta` in the request, or select a Tamil font explicitly.
4. **FFmpeg subtitle filter** — if burning subtitles via `subtitles=` filter, verify the `.ass` file's font name matches an installed font.

---

## YouTube upload fails

**Symptom:** Upload errors, `401 Unauthorized`, or `Token has been expired`.

**Checks:**
1. `client_secret.json` exists in the project root.
2. `youtube_token.json` exists — if not, run the app and re-authorize.
3. Token is expired — delete `youtube_token.json` and re-run; a browser window will open for re-authorization.
4. YouTube Data API v3 is enabled in Google Cloud Console.
5. Quota limit reached — the free quota is 10,000 units/day.

---

## Video generation hangs / times out

**Symptom:** A job stays in `VIDEO_GENERATION` stage indefinitely.

**Checks:**
1. Check the provider order: `VIDEO_PROVIDER_ORDER` in `.env`.
2. Check API key for the active provider.
3. fal.ai, Replicate, Novita — these are paid; ensure billing is enabled.
4. Increase timeout via `FAL_TIMEOUT_SECONDS` (default 900).
5. The router will automatically try the next provider after timeout — check logs for fallback messages.

---

## No video output — job completes but file is missing

**Symptom:** Job reaches `COMPLETED` but no `.mp4` is present in `output/`.

**Checks:**
1. Check the video provider returned a path (check logs for `video_path=`).
2. If all providers returned `None`, the `none` safety fallback should produce a static slideshow. If that is also missing, check FFmpeg path.
3. Check `output/<job_id>/` for partial artifacts (images, audio).

---

## Gemini story generation fails

**Symptom:** `STORY_GENERATION` stage fails with `API key invalid` or quota error.

**Checks:**
1. `GEMINI_API_KEY` is set in `.env`.
2. Gemini free tier has a daily request limit — check [AI Studio](https://aistudio.google.com/).
3. Groq is configured as automatic fallback; set `GROQ_API_KEY` as a backup.

---

## Music provider returns None / no background music

**Symptom:** Final video has no background music.

**Cause:** `app/data/music/` is empty — no `.mp3` tracks are bundled.

**Fix:**
- Add royalty-free `.mp3` files to `app/data/music/`.
- Name them to match mood candidates in `app/providers/music.py` (`_MOOD_MAP`):
  - `magical.mp3`, `happy.mp3`, `adventure.mp3`, `calm.mp3`, `dreamy.mp3`, etc.
- The pipeline will copy matching tracks automatically.

---

## Scheduler not running

**Symptom:** Scheduled jobs or YouTube publishes are not triggered.

**Fix:**
- Ensure `SCHEDULER_ENABLED` is not set to `false` in `.env`.
- APScheduler logs appear at startup: `[app.API] Scheduler ready`.
- Check for port conflicts if running multiple instances.

---

## S3 / HuggingFace storage upload fails

**Symptom:** Artifacts are not uploaded after generation.

**Checks:**
1. For HuggingFace: `HUGGINGFACE_API_KEY` and `HF_DATASET_REPO` are set.
2. For S3: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, and `S3_ENDPOINT_URL` are all set.
3. The local `download` provider is always available as fallback.

---

## `.env.example` box-drawing characters appear garbled

**Symptom:** PowerShell shows `?` symbols when `cat .env.example`.

**Cause:** The file was written in UTF-8 with box-drawing characters; PowerShell's default encoding differs.

**Fix:** Open in VS Code or a UTF-8 aware editor. The content is correct — only the terminal display is affected.

---

## Port 8000 already in use

**Symptom:** `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)`.

**Fix:**
```
python -m uvicorn app.main:app --reload --port 8001
```

---

## PIL / Pillow ImportError

**Symptom:** `ImportError: cannot import name 'Image' from 'PIL'`.

**Fix:**
```
pip install --upgrade Pillow
```

---

## Still stuck?

1. Run `python scripts/doctor.py` for an automated dependency check.
2. Check `data/culprit.db` for job state via any SQLite browser.
3. Review logs — all provider errors include `provider=` and `error=` fields.
