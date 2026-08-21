from __future__ import annotations

from app.story.schemas import CharacterProfile, Scene, ImagePrompt, VideoPrompt, MotionPrompt
from app.log import get_logger

log = get_logger("PromptEngine")


class PromptEngine:
    """Builds image/video/motion/negative prompts from a scene and character profile.

    Automatically injects character identity, style, camera, lighting and
    environment details so downstream AI providers receive rich, consistent prompts.
    """

    # Camera movement vocabulary for video prompts
    CAMERA_MOVES = {
        "gentle push-in": "slow cinematic push-in towards the subject",
        "slow tracking shot": "smooth lateral tracking shot following the subject",
        "wide establishing shot": "wide establishing shot showing the full environment",
        "close-up": "close-up framing on the character's face and expression",
        "overhead": "top-down overhead angle looking at the scene",
        "low angle": "low-angle shot emphasising the character's presence",
        "dolly zoom": "subtle dolly-zoom creating depth parallax",
        "pan right": "smooth horizontal pan to the right revealing the scene",
        "pan left": "smooth horizontal pan to the left revealing the scene",
    }

    # Lighting presets by scene mood
    LIGHTING = {
        "default": "soft cinematic kids-lighting, even key light, no flicker",
        "magical": "warm magical glow, soft rim light, sparkle highlights",
        "adventure": "bright adventure lighting, warm sun tones, dynamic shadows",
        "calm": "gentle diffused lighting, soft pastels, no harsh shadows",
        "night": "moonlit ambience, cool blue fill light, soft highlights",
        "educational": "bright even classroom lighting, clean and clear",
    }

    def _resolve_camera(self, camera: str) -> str:
        cam = camera.strip().lower()
        return self.CAMERA_MOVES.get(cam, camera or "gentle push-in")

    def _resolve_lighting(self, scene: Scene) -> str:
        mood = (scene.music_mood or "default").lower()
        for key in self.LIGHTING:
            if key in mood:
                return self.LIGHTING[key]
        return self.LIGHTING["default"]

    def build(
        self, scene: Scene, character: CharacterProfile,
        art_style: str, aspect_ratio: str,
    ) -> dict:
        appearance = character.appearance.strip()
        style = character.style or art_style
        env = scene.visual_prompt or scene.narration
        camera_desc = self._resolve_camera(scene.camera or "gentle push-in")
        lighting = self._resolve_lighting(scene)
        motion = scene.motion_prompt or f"{appearance} moves naturally. {camera_desc}."

        image = (
            f"{appearance}. {style}. Scene: {env}. "
            f"Camera: {camera_desc}. Lighting: {lighting}. "
            f"Aspect {aspect_ratio}. No on-image text, subtitles, watermark or logo."
        )
        video = (
            f"Keep character identity exactly consistent: {appearance}. Style: {style}. "
            f"{motion} Environment stays coherent. {lighting}."
        )
        negative = character.negative_prompt

        log.debug(
            "Prompts built  scene=%d  image_len=%d  video_len=%d",
            scene.number, len(image), len(video),
        )
        return {
            "image": ImagePrompt(prompt=image, negative_prompt=negative),
            "video": VideoPrompt(prompt=video, negative_prompt=negative),
            "motion": MotionPrompt(prompt=motion),
            "negative": negative,
        }
