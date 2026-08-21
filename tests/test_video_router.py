"""Tests for the video provider router: ordering, fallback, cost metadata."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.providers.video import (
    VideoRouterState, configured_provider_order,
    generate_scene, VideoProviderError, PermanentProviderError,
    TemporaryProviderError, COST_INFO, ALIASES, DEFAULT_ORDER,
)


class TestConfiguredProviderOrder:
    @patch("app.providers.video.settings")
    def test_default_order_with_all_keys(self, mock_settings):
        """All providers configured → returns DEFAULT_ORDER."""
        mock_settings.VIDEO_PROVIDER_ORDER = ""
        # Mock _key to return a truthy value for all
        with patch("app.providers.video._key", return_value="some-key"):
            order = configured_provider_order()
        assert order == DEFAULT_ORDER

    @patch("app.providers.video.settings")
    def test_preferred_first(self, mock_settings):
        """Preferred provider is moved to the front."""
        mock_settings.VIDEO_PROVIDER_ORDER = ""
        with patch("app.providers.video._key", return_value="some-key"):
            order = configured_provider_order("pixverse")
        assert order[0] == "pixverse"

    @patch("app.providers.video.settings")
    def test_env_order_override(self, mock_settings):
        """VIDEO_PROVIDER_ORDER from .env overrides the default order."""
        mock_settings.VIDEO_PROVIDER_ORDER = "minimax,nvidia,fal"
        with patch("app.providers.video._key", return_value="some-key"):
            order = configured_provider_order()
        assert order[0] == "minimax"
        assert order[1] == "nvidia"
        assert order[2] == "fal"

    @patch("app.providers.video.settings")
    def test_unconfigured_filtered(self, mock_settings):
        """Providers without API keys are excluded."""
        mock_settings.VIDEO_PROVIDER_ORDER = ""
        def fake_key(name):
            return "key" if name in ("PIXVERSE_API_KEY", "FAL_API_KEY") else ""
        with patch("app.providers.video._key", side_effect=fake_key):
            order = configured_provider_order()
        assert "pixverse" in order
        assert "fal" in order
        assert "nvidia" not in order


class TestVideoRouterState:
    def test_initial_state(self):
        state = VideoRouterState()
        assert state.disabled_providers == set()
        assert state.failures == {}
        assert state.successful_provider is None

    def test_disable_provider(self):
        state = VideoRouterState()
        state.disabled_providers.add("nvidia")
        assert "nvidia" in state.disabled_providers

    def test_sticky_provider(self):
        state = VideoRouterState()
        state.successful_provider = "pixverse"
        assert state.successful_provider == "pixverse"


class TestCostInfo:
    def test_all_default_providers_have_cost(self):
        for name in DEFAULT_ORDER:
            assert name in COST_INFO, f"Missing cost info for {name}"

    def test_cost_structure(self):
        for name, info in COST_INFO.items():
            assert "estimated_cost" in info
            assert "currency" in info
            assert "free_tier" in info
            assert "requires_billing" in info
            assert isinstance(info["estimated_cost"], (int, float))
            assert isinstance(info["free_tier"], bool)

    def test_nvidia_is_free(self):
        assert COST_INFO["nvidia"]["free_tier"] is True
        assert COST_INFO["nvidia"]["requires_billing"] is False


class TestAliases:
    def test_auto_alias(self):
        assert ALIASES["auto"] == "auto"

    def test_nvidia_aliases(self):
        assert ALIASES["nvidia-cosmos"] == "nvidia"
        assert ALIASES["cosmos3-nano"] == "nvidia"

    def test_fal_alias(self):
        assert ALIASES["fal-wan22"] == "fal"

    def test_minimax_alias(self):
        assert ALIASES["hailuo"] == "minimax"

    def test_wan_aliases(self):
        assert ALIASES["wan"] == "wan-fal"
        assert ALIASES["wan-fal"] == "wan-fal"

    def test_hunyuan_aliases(self):
        assert ALIASES["hunyuan"] == "hunyuan-fal"
        assert ALIASES["hunyuan-fal"] == "hunyuan-fal"

    def test_ltx_aliases(self):
        assert ALIASES["ltx"] == "ltx-fal"
        assert ALIASES["ltx-fal"] == "ltx-fal"

    def test_new_providers_in_default_order(self):
        assert "wan-fal" in DEFAULT_ORDER
        assert "hunyuan-fal" in DEFAULT_ORDER
        assert "ltx-fal" in DEFAULT_ORDER

    def test_new_providers_have_cost_info(self):
        for p in ("wan-fal", "hunyuan-fal", "ltx-fal"):
            assert p in COST_INFO, f"Missing COST_INFO for {p}"
            assert COST_INFO[p]["free_tier"] is False
            assert COST_INFO[p]["requires_billing"] is True


class TestGenerateSceneFallback:
    def test_none_provider_returns_none(self):
        result = generate_scene("test prompt", "/fake/ref.png", "/fake/out.mp4", "none")
        assert result is None

    @patch("app.providers.video.configured_provider_order", return_value=[])
    def test_no_providers_returns_none(self, mock_order):
        result = generate_scene("test", "/fake/ref.png", "/fake/out.mp4", "auto")
        assert result is None

    def test_router_state_tracks_failures(self):
        state = VideoRouterState()
        state.disabled_providers.add("nvidia")
        state.failures["nvidia"] = "test failure"
        assert "nvidia" in state.disabled_providers
        assert "nvidia" in state.failures
