"""Structured logging for Culprit Studio Pro.

Usage::

    from app.log import get_logger
    log = get_logger("VideoRouter")
    log.info("Trying provider", provider="nvidia")
    log.error("Provider failed", provider="nvidia", error_type="NETWORK")

All loggers write to stderr with a consistent ``[name]`` prefix and
optional key-value context.  Secrets are automatically redacted.
"""
from __future__ import annotations

import logging
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------
_SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_\-]?key|token|bearer|authorization|secret)[=:]\s*\S+"), r"\1=***"),
    (re.compile(r"nvapi-[A-Za-z0-9_\-]+"), "***"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), "***"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{10,}"), "***"),
    (re.compile(r"hf_[A-Za-z0-9_\-]{10,}"), "***"),
]


def redact(text: str) -> str:
    """Mask known secret patterns in *text*."""
    s = str(text or "")
    for pat, repl in _SECRET_PATTERNS:
        s = pat.sub(repl, s)
    return s[:2000]


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
class _CulpritFormatter(logging.Formatter):
    """Single-line formatter: ``[name] message  key=val key2=val2``"""

    def format(self, record: logging.LogRecord) -> str:
        msg = redact(str(record.getMessage()))
        ctx = getattr(record, "ctx", None)
        if ctx and isinstance(ctx, dict):
            pairs = "  ".join(f"{k}={redact(str(v))}" for k, v in ctx.items())
            msg = f"{msg}  {pairs}" if pairs else msg
        return f"[{record.name}] {msg}"


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------
_initialised = False


def _ensure_handler() -> None:
    global _initialised
    if _initialised:
        return
    root = logging.getLogger("app")
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_CulpritFormatter())
    root.addHandler(handler)
    root.propagate = False
    _initialised = True


# Standard LogRecord kwargs that should NOT be treated as context keys
_LOG_KWARGS = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})


class _CtxLogger(logging.Logger):
    """Logger subclass that accepts extra keyword arguments as context.

    Example::

        log.info("Trying provider", provider="nvidia", cost=0.05)

    The extra ``provider`` and ``cost`` keys are attached to the log record
    and displayed by the ``_CulpritFormatter``.
    """

    def _log(self, level, msg, args, **kw):
        # Extract non-standard kwargs as context
        ctx_keys = {k: kw.pop(k) for k in list(kw) if k not in _LOG_KWARGS}
        extra = kw.pop("extra", None) or {}
        if isinstance(extra, dict):
            ctx = {**extra, **ctx_keys}
        else:
            ctx = ctx_keys
        if ctx:
            kw.setdefault("extra", {})["ctx"] = ctx
        super()._log(level, msg, args, **kw)


def get_logger(name: str) -> _CtxLogger:
    """Return a named logger under the ``app`` namespace.

    Always returns a ``_CtxLogger`` so that callers can use
    ``log.info("msg", key=val)`` syntax safely.
    """
    _ensure_handler()
    # Register our custom class so getLogger returns the right type
    full_name = f"app.{name}"
    logging.setLoggerClass(_CtxLogger)
    logger = logging.getLogger(full_name)
    logging.setLoggerClass(logging.Logger)  # reset to default
    if not isinstance(logger, _CtxLogger):
        # Logger was already created with default class; wrap it
        logger.__class__ = _CtxLogger
    return logger  # type: ignore[return-value]
