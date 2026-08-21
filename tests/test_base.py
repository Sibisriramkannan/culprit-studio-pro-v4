"""Tests for provider base module: error classification, redaction, ProviderResult."""
from __future__ import annotations

import pytest
from app.providers.base import (
    ProviderErrorType, RETRYABLE, classify_http, classify_exception,
    redact, ProviderResult, ProviderInfo, VideoGenerationRequest,
)


class TestClassifyHttp:
    def test_auth_401(self):
        assert classify_http(401) == ProviderErrorType.AUTH

    def test_auth_403(self):
        assert classify_http(403) == ProviderErrorType.AUTH

    def test_insufficient_balance(self):
        assert classify_http(402) == ProviderErrorType.INSUFFICIENT_BALANCE
        assert classify_http(400, "insufficient balance") == ProviderErrorType.INSUFFICIENT_BALANCE

    def test_rate_limit(self):
        assert classify_http(429) == ProviderErrorType.RATE_LIMIT
        assert classify_http(400, "rate limit exceeded") == ProviderErrorType.RATE_LIMIT

    def test_invalid_request(self):
        assert classify_http(400) == ProviderErrorType.INVALID_REQUEST
        assert classify_http(422) == ProviderErrorType.INVALID_REQUEST

    def test_unsupported(self):
        assert classify_http(404) == ProviderErrorType.UNSUPPORTED

    def test_timeout(self):
        assert classify_http(408) == ProviderErrorType.TIMEOUT
        assert classify_http(504) == ProviderErrorType.TIMEOUT
        assert classify_http(400, "request timeout") == ProviderErrorType.TIMEOUT

    def test_server_error(self):
        assert classify_http(500) == ProviderErrorType.SERVER
        assert classify_http(502) == ProviderErrorType.SERVER
        assert classify_http(503) == ProviderErrorType.SERVER

    def test_unknown(self):
        assert classify_http(418) == ProviderErrorType.UNKNOWN


class TestClassifyException:
    def test_timeout(self):
        exc = TimeoutError("connection timed out")
        assert classify_exception(exc) == ProviderErrorType.TIMEOUT

    def test_network(self):
        exc = ConnectionError("connection refused")
        assert classify_exception(exc) == ProviderErrorType.NETWORK

    def test_auth_balance(self):
        exc = RuntimeError("insufficient balance for this request")
        assert classify_exception(exc) == ProviderErrorType.INSUFFICIENT_BALANCE

    def test_auth_key(self):
        exc = RuntimeError("invalid api key provided")
        assert classify_exception(exc) == ProviderErrorType.AUTH

    def test_not_configured(self):
        exc = RuntimeError("API key is not configured")
        assert classify_exception(exc) == ProviderErrorType.NOT_CONFIGURED

    def test_unknown(self):
        exc = ValueError("some unexpected thing")
        assert classify_exception(exc) == ProviderErrorType.UNKNOWN


class TestRedact:
    def test_redacts_api_key(self):
        text = "api_key=nvapi-abc123xyz456 failed"
        assert "nvapi-abc123xyz456" not in redact(text)

    def test_redacts_bearer(self):
        text = "Authorization: Bearer sk-abc1234567890xyz"
        assert "sk-abc1234567890xyz" not in redact(text)

    def test_redacts_gemini(self):
        text = "key=AIzaSyD1234567890abcdefghijklmnopqrstuv"
        assert "AIzaSyD1234567890abcdefghijklmnopqrstuv" not in redact(text)

    def test_truncates(self):
        text = "x" * 3000
        assert len(redact(text)) <= 2000

    def test_empty(self):
        assert redact(None) == ""
        assert redact("") == ""


class TestProviderResult:
    def test_success(self):
        r = ProviderResult(success=True, provider="mock", artifact="/tmp/video.mp4")
        assert r.success is True
        assert r.provider == "mock"

    def test_fail(self):
        r = ProviderResult(success=True, provider="mock")
        r.fail(ProviderErrorType.NETWORK, "connection timeout")
        assert r.success is False
        assert r.error_type == ProviderErrorType.NETWORK
        assert r.retryable is True  # NETWORK is in RETRYABLE

    def test_fail_permanent(self):
        r = ProviderResult(success=True, provider="mock")
        r.fail(ProviderErrorType.AUTH, "invalid key")
        assert r.success is False
        assert r.retryable is False  # AUTH is not in RETRYABLE

    def test_fail_secrets_redacted(self):
        r = ProviderResult(success=True, provider="mock")
        r.fail(ProviderErrorType.AUTH, "Bearer sk-abc1234567890xyz denied")
        assert "sk-abc1234567890xyz" not in r.message


class TestVideoGenerationRequest:
    def test_defaults(self):
        req = VideoGenerationRequest(prompt="test", output_path="/tmp/out.mp4")
        assert req.duration == 5.0
        assert req.aspect_ratio == "9:16"
        assert req.fps == 24

    def test_extra_ignored(self):
        req = VideoGenerationRequest(
            prompt="test", output_path="/tmp/out.mp4",
            unknown_field="should be ignored",
        )
        assert req.prompt == "test"


class TestRetryable:
    def test_retryable_set(self):
        assert ProviderErrorType.NETWORK in RETRYABLE
        assert ProviderErrorType.TIMEOUT in RETRYABLE
        assert ProviderErrorType.RATE_LIMIT in RETRYABLE
        assert ProviderErrorType.SERVER in RETRYABLE

    def test_not_retryable(self):
        assert ProviderErrorType.AUTH not in RETRYABLE
        assert ProviderErrorType.INSUFFICIENT_BALANCE not in RETRYABLE
        assert ProviderErrorType.INVALID_REQUEST not in RETRYABLE
        assert ProviderErrorType.UNSUPPORTED not in RETRYABLE
