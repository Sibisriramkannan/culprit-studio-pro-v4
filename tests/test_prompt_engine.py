"""Tests for PromptEngine and Story schemas."""
from __future__ import annotations

import pytest

from app.prompt_engine import PromptEngine
from app.story.schemas import CharacterProfile, Scene, Story


class TestPromptEngine:
    def setup_method(self):
        self.engine = PromptEngine()
        self.character = CharacterProfile(
            id="zuzu",
            name="Zuzu",
            appearance="A friendly animated panda with round eyes",
            personality="Curious, friendly",
            style="Modern cartoon",
            negative_prompt="blurry, watermark",
        )

    def test_build_returns_all_keys(self):
        scene = Scene(
            number=1, narration="Zuzu walks in a forest.",
            visual_prompt="Panda in a colorful forest.",
            motion_prompt="Panda walks forward slowly.",
        )
        result = self.engine.build(scene, self.character, "Cartoon", "9:16")
        assert "image" in result
        assert "video" in result
        assert "motion" in result
        assert "negative" in result

    def test_image_prompt_includes_character(self):
        scene = Scene(number=1, narration="Test", visual_prompt="A lab scene.")
        result = self.engine.build(scene, self.character, "Cartoon", "16:9")
        assert "friendly animated panda" in result["image"].prompt

    def test_image_prompt_includes_style(self):
        scene = Scene(number=1, narration="Test", visual_prompt="Scene.")
        # Character has no style set, so art_style param is used
        char = CharacterProfile(id="t", name="T", appearance="A test character")
        result = self.engine.build(scene, char, "Watercolor", "9:16")
        assert "Watercolor" in result["image"].prompt

    def test_image_prompt_includes_aspect(self):
        scene = Scene(number=1, narration="Test", visual_prompt="Scene.")
        result = self.engine.build(scene, self.character, "Cartoon", "1:1")
        assert "1:1" in result["image"].prompt

    def test_video_prompt_includes_identity(self):
        scene = Scene(
            number=1, narration="Test",
            visual_prompt="Forest.",
            motion_prompt="Panda waves.",
        )
        result = self.engine.build(scene, self.character, "Cartoon", "9:16")
        assert "character identity" in result["video"].prompt.lower()

    def test_negative_prompt_passed(self):
        scene = Scene(number=1, narration="Test")
        result = self.engine.build(scene, self.character, "Cartoon", "9:16")
        assert result["negative"] == "blurry, watermark"

    def test_camera_resolution(self):
        engine = PromptEngine()
        assert "push-in" in engine._resolve_camera("gentle push-in").lower()
        assert "tracking" in engine._resolve_camera("slow tracking shot").lower()
        # Unknown camera returns original text
        assert engine._resolve_camera("custom orbit") == "custom orbit"

    def test_lighting_resolution(self):
        engine = PromptEngine()
        scene_magical = Scene(number=1, narration="Test", music_mood="magical")
        assert "magical" in engine._resolve_lighting(scene_magical).lower()

        scene_default = Scene(number=1, narration="Test", music_mood="auto")
        assert "kids-lighting" in engine._resolve_lighting(scene_default)


class TestStorySchema:
    def test_valid_story(self):
        story = Story(
            title="Test Story",
            language="en",
            scenes=[
                Scene(number=1, narration="Hello world.", visual_prompt="A test scene."),
            ],
        )
        assert story.title == "Test Story"
        assert len(story.scenes) == 1

    def test_empty_title_rejected(self):
        with pytest.raises(Exception):
            Story(title="", scenes=[Scene(narration="Test")])

    def test_no_scenes_rejected(self):
        with pytest.raises(Exception):
            Story(title="Test", scenes=[])

    def test_empty_narration_rejected(self):
        with pytest.raises(Exception):
            Scene(narration="")


class TestCharacterProfile:
    def test_defaults(self):
        c = CharacterProfile(id="test", name="Test")
        assert c.negative_prompt  # has default
        assert c.reference_images == []

    def test_zuzu_profile(self):
        c = CharacterProfile(
            id="zuzu",
            name="Zuzu",
            appearance="A friendly panda",
            style="Modern cartoon",
            personality="Curious",
        )
        assert c.id == "zuzu"
        assert "panda" in c.appearance.lower()
