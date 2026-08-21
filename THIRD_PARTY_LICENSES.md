# Third-Party Licenses

This file lists every third-party library, model, and service integrated into
**Culprit Studio Pro V4**.  Only our own application code is original work.
We study architectures, documentation, and model interfaces from these sources
but do not redistribute model weights, copy source code, or embed API secrets.

---

## Python Runtime Libraries

| Package | License | Notes |
|---------|---------|-------|
| [FastAPI](https://fastapi.tiangolo.com/) | MIT | Web framework |
| [Uvicorn](https://www.uvicorn.org/) | BSD-3-Clause | ASGI server |
| [Pydantic](https://docs.pydantic.dev/) | MIT | Data validation |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | MIT | .env settings |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | BSD-3-Clause | .env loader |
| [Requests](https://docs.python-requests.org/) | Apache 2.0 | HTTP client |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause | Async HTTP client |
| [python-multipart](https://github.com/andrew-d/python-multipart) | Apache 2.0 | File upload |
| [Pillow](https://pillow.readthedocs.io/) | HPND (PIL fork) | Image processing |
| [huggingface-hub](https://github.com/huggingface/huggingface_hub) | Apache 2.0 | HF dataset upload |
| [google-genai](https://github.com/googleapis/python-genai) | Apache 2.0 | Gemini API client |
| [google-api-python-client](https://github.com/googleapis/google-api-python-client) | Apache 2.0 | YouTube Data API |
| [google-auth-oauthlib](https://github.com/googleapis/google-auth-library-python-oauthlib) | Apache 2.0 | YouTube OAuth |
| [google-auth-httplib2](https://github.com/googleapis/google-auth-library-python-httplib2) | Apache 2.0 | YouTube auth transport |
| [groq](https://github.com/groq/groq-python) | Apache 2.0 | Groq LLM client |
| [openai](https://github.com/openai/openai-python) | MIT | OpenAI client |
| [cohere](https://github.com/cohere-ai/cohere-python) | MIT | Cohere client |
| [mistralai](https://github.com/mistralai/client-python) | Apache 2.0 | Mistral client |
| [edge-tts](https://github.com/rany2/edge-tts) | GPL-3.0 | Microsoft Edge TTS (unofficial) |
| [APScheduler](https://apscheduler.readthedocs.io/) | MIT | Job scheduler |
| [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) | Apache 2.0 | AWS S3 / S3-compatible (optional) |

---

## System Dependencies

| Tool | License | Notes |
|------|---------|-------|
| [FFmpeg](https://ffmpeg.org/) | LGPL/GPL | Video/audio composition. We invoke as external process; we do not bundle FFmpeg binaries. Users must install separately. |
| [Python 3.12](https://www.python.org/) | PSF | Runtime |
| SQLite | Public Domain | Embedded database via Python stdlib |

---

## AI Model APIs

We call these APIs via HTTP; we do not host, redistribute, or bundle model weights.

| Provider | API / Model | License | Billing |
|----------|-------------|---------|---------|
| Google Gemini | gemini-2.0-flash-lite, gemini-2.0-flash | [Google Generative AI ToS](https://ai.google.dev/terms) | Free tier / paid |
| Groq | LLaMA 3 variants | [Groq ToS](https://groq.com/terms-of-service/) | Free tier / paid |
| Mistral AI | mistral-small, mistral-medium | [Mistral ToS](https://mistral.ai/terms/) | Paid |
| OpenAI | gpt-4o, DALL-E | [OpenAI ToS](https://openai.com/policies/) | Paid |
| Together AI | LLaMA 3 variants | [Together ToS](https://together.ai/terms-of-service) | Paid |
| NVIDIA NIM | Cosmos3 Nano | [NVIDIA API ToS](https://www.nvidia.com/en-us/about-nvidia/terms-of-service/) | Free preview / verify contract |
| fal.ai | Wan 2.2/2.6, HunyuanVideo, LTX-Video | [fal.ai ToS](https://fal.ai/policies/terms) | Paid per generation |
| Replicate | Wan 2.2 i2v-fast | [Replicate ToS](https://replicate.com/terms) | Paid per generation |
| Novita AI | Wan 2.2 i2v | [Novita ToS](https://novita.ai/legal/terms-of-service) | Paid per generation |
| ModelsLab | Wan 2.2 img2video | [ModelsLab ToS](https://modelslab.com/terms-of-service) | Paid per generation |
| PixVerse | V6 image-to-video | [PixVerse ToS](https://app.pixverse.ai/terms-of-service) | Paid per generation |
| MiniMax / Hailuo | Hailuo 2.3 Fast | [MiniMax ToS](https://www.minimaxi.com/en/terms) | Paid per generation |
| Hugging Face | FLUX.1-dev / SDXL (Inference API) | [HF ToS](https://huggingface.co/terms-of-service) | Free tier / paid |
| ElevenLabs | Multilingual v2 TTS | [ElevenLabs ToS](https://elevenlabs.io/terms) | Free tier / paid |
| Deepgram | Aura-2 TTS | [Deepgram ToS](https://deepgram.com/legal/terms-of-service) | Paid |
| YouTube Data API v3 | Upload, metadata | [Google API ToS](https://developers.google.com/youtube/terms/api-services-terms-of-service) | Free within quota |

---

## Open Video / Image Models (Evaluated)

These models were evaluated for quality, licensing, and local feasibility.
We call them via the APIs above and do not redistribute their weights.

| Model | License | Source |
|-------|---------|--------|
| [Wan 2.1 / 2.2](https://github.com/Wan-Video/Wan2.1) | Apache 2.0 | Alibaba / Wan-Video |
| [HunyuanVideo](https://github.com/Tencent/HunyuanVideo) | HunyuanVideo License (non-commercial restrictions) | Tencent |
| [LTX-Video](https://github.com/Lightricks/LTX-Video) | LTX-Video Non-Commercial Research License | Lightricks |
| [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) | FLUX Non-Commercial License | Black Forest Labs |
| [SDXL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | CreativeML OpenRAIL++-M | Stability AI |
| [NVIDIA Cosmos](https://www.nvidia.com/en-us/ai/cosmos/) | NVIDIA Open Model License | NVIDIA |

> **Note on HunyuanVideo and LTX-Video**: These models carry non-commercial
> restrictions in their weight licenses.  We access them via the fal.ai API
> which manages licensing compliance on their platform.  For direct local
> hosting, review the respective weight licenses before production use.

---

## Microsoft Edge TTS

`edge-tts` is an unofficial Python library that uses the Microsoft Edge
browser's read-aloud feature.  It is licensed GPL-3.0.

The underlying Text-to-Speech service is provided by Microsoft and is
subject to [Microsoft's Terms of Service](https://www.microsoft.com/en-us/servicesagreement/).
This service is not officially offered as a public API.  We use it as the
free prototype/fallback voice provider only.  For production use, evaluate
ElevenLabs or Deepgram.

---

## UI / Frontend

| Asset | License | Notes |
|-------|---------|-------|
| [Inter font](https://rsms.me/inter/) | SIL OFL 1.1 | Via Google Fonts CDN |
| [Space Grotesk font](https://fonts.google.com/specimen/Space+Grotesk) | SIL OFL 1.1 | Via Google Fonts CDN |

SVG art-style previews in `app/static/previews/art/` are original artwork
created for this project.

---

## No Bundled Model Weights

This repository does **not** contain any model weights, checkpoints, or
pre-trained parameters from third-party sources.  All model usage is via
official API endpoints or the Hugging Face Inference API.

---

## Security & Secret Policy

- `.env` is excluded from version control via `.gitignore`
- `.env.example` contains only placeholder values (no real credentials)
- API keys are loaded at runtime from environment variables only
- Secrets are automatically redacted from all log output (`app/log.py`)

---

*Last updated: 2026-08-21*
