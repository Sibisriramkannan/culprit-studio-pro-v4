"""Music generation / sourcing for Culprit Studio Pro.

Two concrete providers are included:

LibraryMusicProvider
    Serves royalty-free tracks bundled in ``app/data/music/``.
    Falls back to silence if no matching track is found.
    Free, offline, no API key required.

SunoMusicProvider (stub)
    Placeholder for future Suno AI API integration.
    Returns None until configured.

Usage (from pipeline or directly)::

    from app.providers.music import get_music_provider
    provider = get_music_provider("library")
    path = provider.generate("magical", "/tmp/bg.mp3", 60.0)
    if path:
        # use path as background music
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Optional

from app.config import settings
from app.log import get_logger
from app.providers.base import MusicProvider

log = get_logger("MusicProvider")

# ---------------------------------------------------------------------------
# Mood → track filename mapping (files live in app/data/music/)
# ---------------------------------------------------------------------------
_MOOD_MAP: dict[str, list[str]] = {
    "magical":     ["magical.mp3", "fantasy.mp3", "dreamy.mp3"],
    "happy":       ["happy.mp3", "fun.mp3", "upbeat.mp3"],
    "adventure":   ["adventure.mp3", "epic.mp3", "action.mp3"],
    "funny":       ["funny.mp3", "happy.mp3", "fun.mp3"],
    "cute":        ["cute.mp3", "gentle.mp3", "happy.mp3"],
    "epic":        ["epic.mp3", "adventure.mp3", "action.mp3"],
    "emotional":   ["emotional.mp3", "calm.mp3", "gentle.mp3"],
    "mystery":     ["mystery.mp3", "suspense.mp3", "dark.mp3"],
    "suspense":    ["suspense.mp3", "mystery.mp3", "dark.mp3"],
    "horror":      ["horror.mp3", "dark.mp3", "suspense.mp3"],
    "calm":        ["calm.mp3", "gentle.mp3", "dreamy.mp3"],
    "dreamy":      ["dreamy.mp3", "calm.mp3", "magical.mp3"],
    "space":       ["space.mp3", "dreamy.mp3", "calm.mp3"],
    "nature":      ["nature.mp3", "calm.mp3", "gentle.mp3"],
    "retro":       ["retro.mp3", "upbeat.mp3", "fun.mp3"],
    "lo-fi":       ["lofi.mp3", "calm.mp3", "gentle.mp3"],
    # default / auto
    "auto":        ["magical.mp3", "happy.mp3", "adventure.mp3", "calm.mp3"],
}

_MUSIC_DIR = Path("app/data/music")


def _find_track(mood: str) -> Optional[Path]:
    """Locate a matching local music track by mood."""
    key = (mood or "auto").lower()
    candidates = _MOOD_MAP.get(key, _MOOD_MAP["auto"])
    for filename in candidates:
        p = _MUSIC_DIR / filename
        if p.exists() and p.stat().st_size > 0:
            return p
    # last resort: any .mp3 in the directory
    for p in _MUSIC_DIR.glob("*.mp3"):
        if p.stat().st_size > 0:
            return p
    return None


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
class LibraryMusicProvider(MusicProvider):
    """Serve bundled royalty-free tracks from ``app/data/music/``.

    This is the zero-cost, offline-capable provider.  To populate it,
    place ``.mp3`` files named after moods (e.g. ``magical.mp3``) into
    ``app/data/music/``.  If no matching file is found, ``generate``
    returns ``None`` and the pipeline proceeds without background music.
    """

    @property
    def name(self) -> str:
        return "library"

    def is_configured(self) -> bool:
        return True  # always available; tracks may or may not be present

    def generate(self, mood: str, out: str, duration: float) -> Optional[str]:
        track = _find_track(mood)
        if not track:
            log.info("No library track found for mood — skipping music", mood=mood)
            return None
        dest = Path(out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(track), str(dest))
        log.info("Library music selected", mood=mood, track=track.name, out=out)
        return str(dest)


class SunoMusicProvider(MusicProvider):
    """Stub for Suno AI API music generation.

    Suno can generate children's music from a text prompt.
    Enable once you have a SUNO_API_KEY and have verified the API contract.

    Cost: per-generation (not free).
    """

    @property
    def name(self) -> str:
        return "suno"

    def is_configured(self) -> bool:
        return bool(getattr(settings, "SUNO_API_KEY", None))

    def generate(self, mood: str, out: str, duration: float) -> Optional[str]:
        if not self.is_configured():
            log.warning("SunoMusicProvider: SUNO_API_KEY not configured")
            return None
        # TODO: implement Suno API integration once official API endpoint
        #       contract is verified.  For now, fall through to library.
        log.warning("SunoMusicProvider: not yet implemented — falling back to library")
        return LibraryMusicProvider().generate(mood, out, duration)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_PROVIDERS: dict[str, type[MusicProvider]] = {
    "library": LibraryMusicProvider,
    "suno":    SunoMusicProvider,
    "none":    type("NoneMusic", (MusicProvider,), {
        "name": property(lambda self: "none"),
        "is_configured": lambda self: True,
        "generate": lambda self, mood, out, dur: None,
    }),
}


def get_music_provider(name: str = "library") -> MusicProvider:
    """Return a music provider instance by name.

    Falls back to ``LibraryMusicProvider`` for unknown names.
    """
    key = (name or "library").lower()
    cls = _PROVIDERS.get(key, LibraryMusicProvider)
    return cls()


def generate_music(mood: str, out: str, duration: float, provider: str = "library") -> Optional[str]:
    """Convenience function: generate background music to *out* path.

    Parameters
    ----------
    mood:
        Mood label (e.g. "magical", "happy", "calm", "auto").
    out:
        Destination file path (.mp3).
    duration:
        Desired duration in seconds (informational; library tracks are
        not trimmed automatically — the pipeline mixer handles timing).
    provider:
        Provider name ("library", "suno", "none").

    Returns the output path on success, or ``None`` if no music is
    generated.
    """
    start = time.monotonic()
    try:
        p = get_music_provider(provider)
        result = p.generate(mood, out, duration)
        if result:
            log.info(
                "Music generated",
                provider=provider,
                mood=mood,
                elapsed=round(time.monotonic() - start, 2),
            )
        return result
    except Exception as e:
        log.warning("Music generation failed", provider=provider, error=str(e))
        return None
