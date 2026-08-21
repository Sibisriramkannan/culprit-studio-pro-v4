from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from app.story.schemas import CharacterProfile
from app.config import settings

_DEFAULT_ZUZU = CharacterProfile(
    id="zuzu",
    name="Zuzu",
    description="Curious, kind host of Zuzu Wonder Worlds — a child-friendly explorer who teaches through play.",
    appearance=(
        "A friendly animated child mascot named Zuzu: round sparkling eyes, warm brown skin, "
        "soft curly hair with a small star clip, simple colorful explorer outfit (teal vest, "
        "yellow scarf), consistent face and proportions across every shot."
    ),
    personality="Warm, brave, playful, never scary; speaks simply for young viewers.",
    style="Modern cartoon, clean shapes, bright kid-safe palette, consistent character sheet.",
    reference_images=[],
    negative_prompt="adult, horror, gore, realistic uncanny face, extra fingers, text, watermark, logo",
    voice_id="en-US-JennyNeural",
)


def characters_dir() -> Path:
    p = Path(settings.DATA_DIR) / "characters"
    p.mkdir(parents=True, exist_ok=True)
    seed = p / "zuzu.json"
    if not seed.exists():
        seed.write_text(_DEFAULT_ZUZU.model_dump_json(indent=2), encoding="utf-8")
    return p


def list_characters() -> list[CharacterProfile]:
    profiles = []
    for f in sorted(characters_dir().glob("*.json")):
        try:
            profiles.append(CharacterProfile.model_validate(json.loads(f.read_text(encoding="utf-8"))))
        except Exception:
            continue
    if not any(p.id == "zuzu" for p in profiles):
        profiles.insert(0, _DEFAULT_ZUZU)
    return profiles


def load_character(character_id: Optional[str]) -> CharacterProfile:
    cid = (character_id or "zuzu").strip() or "zuzu"
    for p in list_characters():
        if p.id == cid:
            return p
    return _DEFAULT_ZUZU
