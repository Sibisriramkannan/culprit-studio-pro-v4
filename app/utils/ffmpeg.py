from __future__ import annotations

import shutil
from pathlib import Path
from app.config import settings


def ffmpeg_bin() -> str:
    configured = (getattr(settings, "FFMPEG_BIN", None) or "").strip()
    if configured:
        return configured
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"


def ffprobe_bin() -> str:
    configured = (getattr(settings, "FFPROBE_BIN", None) or "").strip()
    if configured:
        return configured
    sibling = Path(ffmpeg_bin()).with_name("ffprobe.exe" if ffmpeg_bin().lower().endswith(".exe") else "ffprobe")
    if sibling.exists():
        return str(sibling)
    return shutil.which("ffprobe") or shutil.which("ffprobe.exe") or "ffprobe"


def canvas(ratio: str) -> tuple[int, int]:
    r = (ratio or "9:16").strip()
    if r in ("16:9", "16x9"):
        return 1920, 1080
    if r in ("1:1", "1x1"):
        return 1080, 1080
    return 1080, 1920
