# Culprit Studio Pro V4.1 — Architecture

Personal AI video factory for **Zuzu Wonder Worlds**. Incremental V4 → V4.1 upgrades are
backwards-compatible: existing modules stay in place; new packages extend them.

---

## Source Map

```
app/
  main.py                  FastAPI: UI, health, catalog, generate, schedules, YouTube OAuth
                           Endpoints: /api/generate, /api/story, /api/catalog, /api/providers/status
                           /api/characters, /api/fonts, /api/subtitle-styles, /api/video-types
  config.py                Pydantic Settings (.env) — all keys declared; validated at startup
  models.py                API request models (VideoConfig, StoryRequest, ScheduleRequest …)
  db.py                    SQLite jobs + schedules (UTF-8, WAL mode)
  pipeline.py              Job orchestration — 11 modular stages
  pipeline_state.py        Canonical job stages + PROGRESS map + JobEvent
  scheduler.py             APScheduler (process-local, persisted in SQLite)
  video_editor.py          FFmpeg + PIL captions / motion / mix / thumbnail
                           canvas_size() | _resolve_font() | generate_thumbnail()
                           still_to_motion() | overlay_caption_on_video() | concat_and_mix()
  prompt_engine.py         Scene + CharacterProfile → image/video/motion/camera prompts
                           PromptEngine | _resolve_camera() | _resolve_lighting()
  subtitles.py             SRT + ASS subtitle generation with Tamil/Hindi Unicode font support
  log.py                   Structured logging with secret redaction; _CtxLogger(Logger subclass)
  providers/
    base.py                ProviderErrorType, ProviderResult, VideoProvider ABC, classify_http/exception
    video.py               HTTP adapters + VideoRouterState + COST_INFO + configured_provider_order()
                           Adapters: nvidia | wan-fal | hunyuan-fal | ltx-fal |
                                     pixverse | minimax | fal | replicate | novita | modelslab
    router.py              ProviderRouter (order, retry, fallback, metrics)
    llm.py                 Gemini (primary) + Groq/Mistral/Together/OpenAI/Cohere
    image.py               HF FLUX (primary) / OpenAI DALL-E
    tts.py                 Edge Neural (primary, free) + ElevenLabs / Deepgram
    music.py               LibraryMusicProvider (bundled tracks) + SunoMusicProvider (stub)
    youtube.py             OAuth, token refresh, channel info, upload
    storage.py             LocalStorage / HuggingFaceStorage / S3Storage + upload_auto()
  story/
    schemas.py             Validated Story / Scene / CharacterProfile Pydantic models
  characters/
    __init__.py            load_character() / list_characters() factory
  utils/
    ffmpeg.py              Configurable ffmpeg/ffprobe paths (Windows-safe)
  data/
    catalog.json           LLM / image / video / voice / art-style / caption / effect catalog
    music/                 Royalty-free .mp3 tracks (user-populated; mood-keyed filenames)
static/
  index.html               Single-page app shell
  app.js                   7-step wizard (Manual) + 8-step wizard (Automation) + Settings
  styles.css               Dark glass-morphism UI
scripts/
  doctor.py                Pre-flight checks (env, FFmpeg, providers)
  run_batch.py             Kaggle / headless batch runner
tests/
  conftest.py              Shared fixtures (mock providers, temp dirs)
  test_base.py             ProviderErrorType classification + redact (28 tests)
  test_video_router.py     COST_INFO, configured_provider_order, VideoRouterState (15 tests)
  test_subtitles.py        SRT/ASS formatting + Tamil font + scene timing (17 tests)
  test_pipeline_state.py   JobStage, PROGRESS, JobEvent (12 tests)
  test_prompt_engine.py    PromptEngine, Story/Scene/CharacterProfile schemas (14 tests)
  test_models_and_editor.py VideoConfig, canvas_size, _resolve_font, logging (22 tests)
```

---

## What Works (V4.1)

| Area | Status |
|------|--------|
| FastAPI + V4 UI | Working; 7-step wizard POSTs `{config}` to `/api/generate` |
| Gemini story + scene plan | Real Google Generative Language API |
| Edge TTS en/ta/hi | Real `edge-tts` (free, unofficial) |
| YouTube OAuth + upload | Real Google APIs; token refresh; privacy; schedule |
| Scheduler | APScheduler while the API process is running; persisted in SQLite |
| Video HTTP adapters | NVIDIA, Wan 2.6 (fal), HunyuanVideo (fal), LTX-Video (fal), PixVerse, MiniMax, fal Wan 2.2, Replicate, Novita, ModelsLab |
| Provider failover | Automatic: permanent errors disable provider for job; temporary errors allow retry; local FFmpeg always last |
| Provider cost metadata | COST_INFO per provider; displayed in settings UI with color-coded cost badges |
| Configurable provider order | VIDEO_PROVIDER_ORDER env var; sticky on successful provider |
| Local motion fallback | FFmpeg Ken Burns from reference still; always available |
| Caption overlay | PIL + FFmpeg; `caption_style` + `font_family` + `font_size` travel UI→API→renderer |
| Tamil font | `_resolve_font()`: explicit path → Nirmala UI / Noto Sans (Unicode) → per-style group → PIL default |
| SRT / ASS subtitles | `subtitles.py`: proportional timing, Tamil/Hindi Unicode, 12 style presets |
| PromptEngine | Camera vocabulary, mood-based lighting, character identity lock-in |
| CharacterProfile | Zuzu panda profile; load_character() factory |
| Storage abstraction | Local / HuggingFace / S3 via StorageProvider + upload_auto() |
| Music abstraction | LibraryMusicProvider (mood-keyed local files) + SunoMusicProvider (stub) |
| Thumbnail generation | FFmpeg frame extract + PIL title overlay |
| 1:1 aspect ratio | canvas_size() + RATIO_SIZES covers 9:16 / 16:9 / 1:1 |
| Structured logging | `_CtxLogger` (Logger subclass); supports `log.info("msg", key=val)` |
| Secret redaction | `redact()` strips nvapi-*, AIza*, sk-*, hf_* patterns from log output |
| Test suite | 110 tests, no paid API required; runs in ~1.4s |

---

## Known Gaps / Future Work

| Area | Status |
|------|--------|
| NVIDIA Cosmos endpoint | Not treated as verified contract (prior 404). Adapter kept; disabled unless keys present. |
| Kling direct adapter | Requires access/secret key auth; skipped safely (not in router). |
| Avatar / lip-sync | Architecture evaluated; no adapter implemented yet (HeyGem/MuseTalk). |
| Suno music | Stub only; requires official API contract verification. |
| Local GPU inference | No local model runner yet; all generation via cloud APIs. |
| Kaggle worker | Batch script only; no queue/webhook handshake. |
| Font size from UI | font_size field wired through; preset defaults used when 0. |

---

## Pipeline Stages

```
QUEUED
  → [1] STORY_GENERATION      LLM: plan_video() → scenes JSON
  → [2] SCENE_PLANNING        PromptEngine: enrich image/video/motion prompts with CharacterProfile
  → [3] TTS_GENERATION        Edge TTS / ElevenLabs / Deepgram → voice.mp3
  → [4] IMAGE_GENERATION      HF FLUX / OpenAI → one reference PNG per scene
  → [5] VIDEO_GENERATION      AI provider failover → raw MP4 per scene (or FFmpeg Ken Burns)
  → [6] CAPTION_OVERLAY       PIL + FFmpeg → caption burned into each clip
  → [7] SUBTITLE_GENERATION   SRT + ASS → subtitles.srt / subtitles.ass
  → [8] COMPOSITING           concat clips + mix voice + music → final.mp4
  → [9] THUMBNAIL             FFmpeg frame + PIL title overlay → thumbnail.jpg
  → [10] STORAGE_UPLOAD       LocalStorage / HuggingFace / S3
  → [11] YOUTUBE_UPLOAD       YouTube Data API (optional)
  → COMPLETED | FAILED
```

One provider failure disables that provider for the **job** (permanent) or retries once
(temporary).  Local FFmpeg is always the last video fallback.

---

## Provider Failover Chain (default)

```
NVIDIA Cosmos3 Nano  (free, when API key present)
  → Wan 2.6 via fal.ai
  → HunyuanVideo via fal.ai
  → LTX-Video via fal.ai  (fast)
  → PixVerse V6
  → MiniMax Hailuo 2.3 Fast
  → fal.ai Wan 2.2
  → Replicate Wan 2.2
  → Novita Wan 2.2
  → ModelsLab Wan 2.2
  → Local FFmpeg motion fallback  (always available)
```

Override by setting `VIDEO_PROVIDER_ORDER=nvidia,ltx-fal,pixverse,...` in `.env`.

---

## UI → API Flow

```
GET /                          index.html (SPA shell)
GET /api/catalog               LLM / video / voice / art-style / caption catalog
GET /api/providers/status      Provider health + cost metadata
GET /api/dashboard             Job stats + YouTube channel
POST /api/story                LLM story generation (builder mode)
POST /api/generate             Full pipeline: config → job → video
POST /api/upload/music         Music file upload
GET  /api/voice-preview/:id    TTS preview audio
GET  /api/characters           Character catalog
GET  /api/subtitle-styles      ASS + caption preset names
GET  /api/video-types          Short / Story / Rhyme / Educational
YouTube: /auth/youtube/start → Google OAuth → /auth/youtube/callback
Schedules: CRUD + run-now (APScheduler)
```

---

## Tamil / Multi-Language Support

Tamil is a first-class language throughout:

- **LLM**: Gemini generates Tamil story and scene narration when `language="ta"`
- **TTS**: `ta-IN-ValluvarNeural` / `ta-IN-PallaviNeural` via Edge TTS
- **Captions**: `_resolve_font()` selects Nirmala UI (Windows) or Noto Sans (Linux/other)
- **Subtitles**: ASS files use Tamil-capable Unicode font; Tamil script preserved in all file I/O
- **Database**: SQLite with UTF-8; JSON with `ensure_ascii=False`
- **YouTube**: Tamil title, description, tags pass through unchanged

---

## Security Model

- All secrets loaded from `.env` at startup; never committed
- `.env.example` contains only empty placeholder values
- `redact()` strips common secret patterns from every log line
- YouTube OAuth tokens stored in `youtube_token.json` (excluded from git)
- No model weights bundled; all AI via API calls

---

## Kaggle (Optional)

`scripts/run_batch.py` — batch job runner for Kaggle notebook sessions.
The core FastAPI application does **not** require a Kaggle session.
Kaggle is one optional GPU execution environment; the architecture supports
AWS/GCP/Azure workers as future additions.
