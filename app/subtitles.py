"""Subtitle and timed-lyrics generation for Culprit Studio Pro.

Produces SRT and ASS subtitle files from narration text + audio timestamps.
Supports Tamil, English and Hindi Unicode text.
"""
from __future__ import annotations

import json, subprocess, re
from pathlib import Path
from typing import Optional

from app.log import get_logger

log = get_logger("Subtitles")


# ── Time helpers ─────────────────────────────────────────────────────────────
def _fmt_srt(seconds: float) -> str:
    """Format seconds as ``HH:MM:SS,mmm`` (SRT spec)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_ass(seconds: float) -> str:
    """Format seconds as ``H:MM:SS.cc`` (ASS spec, centiseconds)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ── Duration estimation ─────────────────────────────────────────────────────
def _audio_duration(audio_path: str) -> float:
    """Return audio file duration in seconds via ffprobe."""
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", audio_path],
            text=True, encoding="utf-8", errors="replace",
        )
        return float(json.loads(out)["format"]["duration"])
    except Exception:
        return 0.0


# ── Scene-based timing ──────────────────────────────────────────────────────
def _compute_scene_times(
    scenes: list[dict],
    total_duration: float,
) -> list[tuple[float, float]]:
    """Return (start, end) pairs for each scene based on narration length."""
    narrations = [str(s.get("narration", "")).strip() for s in scenes]
    total_chars = sum(len(n) for n in narrations) or 1
    times: list[tuple[float, float]] = []
    cursor = 0.0
    for n in narrations:
        proportion = len(n) / total_chars
        seg_dur = proportion * total_duration
        times.append((cursor, cursor + seg_dur))
        cursor += seg_dur
    return times


# ── Word-level splitting within a scene ─────────────────────────────────────
def _split_into_captions(
    text: str,
    start: float,
    end: float,
    max_chars: int = 42,
) -> list[tuple[float, float, str]]:
    """Break a scene's narration into timed caption segments.

    Each segment is at most *max_chars* characters.  Timing is distributed
    proportionally by character count within the scene window.
    """
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) > max_chars and current:
            chunks.append(current)
            current = word
        else:
            current = test
    if current:
        chunks.append(current)

    if not chunks:
        return [(start, end, text)]

    total_chars = sum(len(c) for c in chunks) or 1
    dur = end - start
    result: list[tuple[float, float, str]] = []
    cursor = start
    for chunk in chunks:
        proportion = len(chunk) / total_chars
        seg = proportion * dur
        result.append((cursor, cursor + seg, chunk))
        cursor += seg
    return result


# ── SRT generation ──────────────────────────────────────────────────────────
def generate_srt(
    scenes: list[dict],
    out_path: str,
    *,
    audio_path: Optional[str] = None,
    total_duration: float = 0.0,
    max_chars: int = 42,
) -> str:
    """Generate an SRT subtitle file from scene narration.

    Parameters
    ----------
    scenes:
        List of scene dicts (must include ``narration`` key).
    out_path:
        Destination ``.srt`` file path.
    audio_path:
        Path to narration audio — used to compute total duration.
    total_duration:
        Override duration in seconds (skips ffprobe if given).
    max_chars:
        Maximum characters per caption line.
    """
    if total_duration <= 0 and audio_path:
        total_duration = _audio_duration(audio_path)
    if total_duration <= 0:
        total_duration = len(scenes) * 5.0  # fallback estimate

    scene_times = _compute_scene_times(scenes, total_duration)
    entries: list[tuple[float, float, str]] = []
    for (start, end), scene in zip(scene_times, scenes):
        text = str(scene.get("narration", "")).strip()
        if not text:
            continue
        entries.extend(_split_into_captions(text, start, end, max_chars))

    lines: list[str] = []
    for idx, (s, e, txt) in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f"{_fmt_srt(s)} --> {_fmt_srt(e)}")
        lines.append(txt)
        lines.append("")

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("SRT generated", path=str(path), entries=len(entries))
    return str(path)


# ── ASS generation ───────────────────────────────────────────────────────────
_ASS_HEADER = """[Script Info]
Title: Culprit Studio Pro
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{fontname},{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,20,20,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Alignment codes: 2 = bottom-center
# MarginV: distance from bottom

# Style presets mapping to ASS style parameters
ASS_STYLES: dict[str, dict] = {
    "bold-stroke":   {"fontname": "Arial Bold", "fontsize": 58, "outline": 4, "shadow": 2, "marginv": 60},
    "red-highlight": {"fontname": "Arial Bold", "fontsize": 54, "outline": 2, "shadow": 1, "marginv": 60},
    "sleek":         {"fontname": "Segoe UI",   "fontsize": 44, "outline": 2, "shadow": 1, "marginv": 50},
    "karaoke":       {"fontname": "Arial Bold", "fontsize": 52, "outline": 3, "shadow": 2, "marginv": 60},
    "majestic":      {"fontname": "Georgia",    "fontsize": 50, "outline": 3, "shadow": 2, "marginv": 55},
    "beast":         {"fontname": "Impact",     "fontsize": 66, "outline": 5, "shadow": 3, "marginv": 50},
    "elegant":       {"fontname": "Georgia",    "fontsize": 46, "outline": 2, "shadow": 1, "marginv": 55},
    "pixel":         {"fontname": "Consolas",   "fontsize": 46, "outline": 3, "shadow": 0, "marginv": 50},
    "clarity":       {"fontname": "Segoe UI",   "fontsize": 44, "outline": 2, "shadow": 0, "marginv": 50},
    "neon":          {"fontname": "Arial Bold", "fontsize": 52, "outline": 4, "shadow": 2, "marginv": 55},
    "comic":         {"fontname": "Arial Bold", "fontsize": 50, "outline": 4, "shadow": 2, "marginv": 55},
    "minimal":       {"fontname": "Segoe UI",   "fontsize": 38, "outline": 1, "shadow": 0, "marginv": 45},
}

# Tamil / Hindi → use Nirmala UI on Windows, Noto Sans otherwise
_UNICODE_FONTNAMES = {
    "ta": "Nirmala UI",
    "hi": "Nirmala UI",
}


def generate_ass(
    scenes: list[dict],
    out_path: str,
    *,
    audio_path: Optional[str] = None,
    total_duration: float = 0.0,
    style: str = "bold-stroke",
    ratio: str = "9:16",
    language: str = "en",
    max_chars: int = 42,
) -> str:
    """Generate an ASS subtitle file with styled captions.

    Parameters
    ----------
    scenes:
        List of scene dicts (must include ``narration`` key).
    out_path:
        Destination ``.ass`` file path.
    style:
        Caption style preset name (must exist in ASS_STYLES).
    ratio:
        Video aspect ratio — determines PlayResX/PlayResY.
    language:
        Language code — selects Unicode font for Tamil/Hindi.
    """
    W, H = (1080, 1920) if ratio == "9:16" else (1920, 1080) if ratio == "16:9" else (1080, 1080)

    if total_duration <= 0 and audio_path:
        total_duration = _audio_duration(audio_path)
    if total_duration <= 0:
        total_duration = len(scenes) * 5.0

    style_cfg = ASS_STYLES.get(style, ASS_STYLES["bold-stroke"])
    fontname = _UNICODE_FONTNAMES.get(language, style_cfg["fontname"])

    header = _ASS_HEADER.format(
        W=W, H=H,
        fontname=fontname,
        fontsize=style_cfg["fontsize"],
        outline=style_cfg["outline"],
        shadow=style_cfg["shadow"],
        marginv=style_cfg["marginv"],
    )

    scene_times = _compute_scene_times(scenes, total_duration)
    dialogue_lines: list[str] = []
    for (start, end), scene in zip(scene_times, scenes):
        text = str(scene.get("narration", "")).strip()
        if not text:
            continue
        for s, e, chunk in _split_into_captions(text, start, end, max_chars):
            # ASS uses \N for line breaks within dialogue
            safe = chunk.replace("\n", "\\N")
            dialogue_lines.append(
                f"Dialogue: 0,{_fmt_ass(s)},{_fmt_ass(e)},Default,,0,0,0,,{safe}"
            )

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(dialogue_lines) + "\n", encoding="utf-8")
    log.info("ASS generated", path=str(path), entries=len(dialogue_lines))
    return str(path)


# ── Burn subtitles into video (optional) ────────────────────────────────────
def burn_subtitles(
    video: str,
    srt_path: str,
    out: str,
    *,
    font_name: str = "Arial",
    font_size: int = 24,
    language: str = "en",
) -> str:
    """Burn an SRT subtitle track into a video using FFmpeg ``subtitles`` filter."""
    # Use Nirmala UI for Tamil/Hindi
    if language in ("ta", "hi"):
        font_name = "Nirmala UI"
    # Escape special characters in path for FFmpeg filter
    safe_srt = str(Path(srt_path).resolve()).replace("\\", "/").replace(":", "\\:")
    vf = (
        f"subtitles='{safe_srt}':force_style="
        f"'FontName={font_name},FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"Outline=2,Shadow=1,Alignment=2,MarginV=30'"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", video, "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast",
         "-c:a", "copy", out],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    log.info("Subtitles burned", video=out)
    return out
