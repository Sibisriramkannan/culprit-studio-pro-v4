from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProviderErrorType(str, Enum):
    NETWORK = "NETWORK"
    TIMEOUT = "TIMEOUT"
    AUTH = "AUTH"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    RATE_LIMIT = "RATE_LIMIT"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    SERVER = "SERVER"
    UNKNOWN = "UNKNOWN"


RETRYABLE = {
    ProviderErrorType.NETWORK,
    ProviderErrorType.TIMEOUT,
    ProviderErrorType.RATE_LIMIT,
    ProviderErrorType.SERVER,
}

PERM_MARKERS = (
    "balance",
    "credit",
    "billing",
    "subscribe",
    "subscription",
    "unauthorized",
    "invalid api",
    "invalid key",
    "quota exceeded",
    "plan required",
    "exhausted",
    "payment",
)


def redact(text: str) -> str:
    import re

    s = str(text or "")
    s = re.sub(r"(?i)(api[_-]?key|token|bearer|authorization|secret)[=:]\s*\S+", r"\1=***", s)
    s = re.sub(r"nvapi-[A-Za-z0-9_-]+", "nvapi-***", s)
    s = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "AIza***", s)
    s = re.sub(r"sk-[A-Za-z0-9_-]{10,}", "sk-***", s)
    return s[:1400]


def classify_http(status: int, body: str = "") -> ProviderErrorType:
    low = (body or "").lower()
    if status in (401, 403) or "unauthorized" in low or "invalid key" in low or "invalid api" in low:
        return ProviderErrorType.AUTH
    if status == 402 or any(w in low for w in ("balance", "credit", "billing", "payment required")):
        return ProviderErrorType.INSUFFICIENT_BALANCE
    if status == 429 or "rate limit" in low:
        return ProviderErrorType.RATE_LIMIT
    # Check timeout BEFORE generic 400/422 so that timeout messages win
    if status in (408, 425, 504) or "timeout" in low:
        return ProviderErrorType.TIMEOUT
    if status in (400, 422):
        return ProviderErrorType.INVALID_REQUEST
    if status == 404:
        return ProviderErrorType.UNSUPPORTED
    if status in (500, 502, 503):
        return ProviderErrorType.SERVER
    return ProviderErrorType.UNKNOWN


def classify_exception(exc: BaseException) -> ProviderErrorType:
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "timeout" in name or "timeout" in msg:
        return ProviderErrorType.TIMEOUT
    if any(x in msg for x in ("connection", "network", "dns", "refused")):
        return ProviderErrorType.NETWORK
    if any(w in msg for w in PERM_MARKERS):
        if "quota" in msg or "rate" in msg:
            return ProviderErrorType.RATE_LIMIT
        if any(w in msg for w in ("balance", "credit", "billing")):
            return ProviderErrorType.INSUFFICIENT_BALANCE
        if any(w in msg for w in ("unauthorized", "invalid key", "invalid api")):
            return ProviderErrorType.AUTH
    if "not configured" in msg or "missing" in msg and "api" in msg:
        return ProviderErrorType.NOT_CONFIGURED
    if "unsupported" in msg or "404" in msg:
        return ProviderErrorType.UNSUPPORTED
    return ProviderErrorType.UNKNOWN


class VideoGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt: str
    motion_prompt: str = ""
    negative_prompt: str = ""
    reference_image: Optional[str] = None
    output_path: str
    duration: float = 5.0
    aspect_ratio: str = "9:16"
    fps: int = 24
    language: str = "en"


class ProviderResult(BaseModel):
    success: bool
    provider: str
    artifact: Optional[str] = None
    error_type: Optional[ProviderErrorType] = None
    retryable: bool = False
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    latency: float = 0.0
    estimated_cost: Optional[float] = None

    def fail(
        self,
        error_type: ProviderErrorType,
        message: str,
        retryable: Optional[bool] = None,
    ) -> "ProviderResult":
        self.success = False
        self.error_type = error_type
        self.retryable = RETRYABLE.__contains__(error_type) if retryable is None else retryable
        self.message = redact(message)
        return self


class ProviderInfo(BaseModel):
    name: str
    enabled: bool = False
    configured: bool = False
    free_tier: bool = False
    requires_billing: bool = True
    estimated_cost: Optional[str] = None
    status: str = "NOT_CONFIGURED"
    reason: str = ""


class VideoProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def is_configured(self) -> bool:
        return False

    def info(self) -> ProviderInfo:
        configured = self.is_configured()
        return ProviderInfo(
            name=self.name,
            configured=configured,
            enabled=configured,
            free_tier=False,
            requires_billing=True,
            status="READY" if configured else "NOT_CONFIGURED",
        )

    @abstractmethod
    async def generate(self, request: VideoGenerationRequest) -> ProviderResult:
        ...


class ImageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def is_configured(self) -> bool:
        return False

    @abstractmethod
    def generate(self, prompt: str, out: str, *, reference_image: Optional[str] = None) -> str:
        ...


class StoryProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def generate_story(self, user_input: str, language: str, mode: str) -> dict[str, Any]:
        ...


class TTSProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def synth(self, text: str, out: str, *, language: str, voice: str, speed: float = 1.0, pitch: str = "+0Hz") -> str:
        ...


class MusicProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def is_configured(self) -> bool:
        return True

    def generate(self, mood: str, out: str, duration: float) -> Optional[str]:
        return None


class StorageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def upload_folder(self, folder: str, remote_path: str) -> str:
        ...
