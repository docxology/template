"""Transient-error retry for deep research provider submissions.

Live verification (2026-06-10) showed provider submissions failing
intermittently with connection-level errors — the same payload that fails can
succeed seconds later, and failures are likelier on large (~300 KB) request
bodies. Submission is idempotent from the caller's perspective (a failed
submit returns no job handle), so a bounded retry with exponential backoff is
safe. Scope: connection/timeout-level transients ONLY — HTTP 429 rate limits
and 5xx statuses are deliberately NOT retried here (a rate limit should
surface to the caller, not be hammered). Same spirit as the bounded arXiv
retry in ``infrastructure.search.literature``, narrower trigger set.

Stdlib-only on purpose: the adapters keep their vendor SDKs lazy, so this
module must not import ``openai`` or ``google.genai`` to classify errors.
"""

from __future__ import annotations

from time import sleep
from typing import Callable, TypeVar
from uuid import uuid4

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

TRANSIENT_NAME_FRAGMENTS = ("connection", "timeout", "temporarily", "serviceunavailable")


def is_transient_submit_error(exc: BaseException) -> bool:
    """Classify an exception as transient without importing vendor SDKs."""
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    name = type(exc).__name__.lower()
    return any(fragment in name for fragment in TRANSIENT_NAME_FRAGMENTS)


def submit_with_transient_retry(
    operation: Callable[[], T],
    *,
    provider: str,
    attempts: int = 3,
    base_delay_seconds: float = 2.0,
) -> T:
    """Run ``operation`` retrying transient failures with exponential backoff.

    Non-transient errors (auth, validation, quota) propagate immediately.
    """
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except BaseException as exc:  # noqa: BLE001 - classified then re-raised
            if not is_transient_submit_error(exc) or attempt == attempts:
                raise
            last_exc = exc
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "%s deep research submit hit transient %s (attempt %d/%d); retrying in %.1fs",
                provider,
                type(exc).__name__,
                attempt,
                attempts,
                delay,
            )
            sleep(delay)
    raise RuntimeError(f"unreachable retry exit for {provider}") from last_exc  # pragma: no cover


def build_submit_idempotency_headers() -> dict[str, str]:
    """Return headers carrying a fresh idempotency key for one logical submit.

    Generate ONCE per submission and reuse across retry attempts so a retried
    POST whose first attempt actually reached the server cannot create a
    duplicate job. OpenAI honours ``Idempotency-Key``; the Gemini Interactions
    API has no documented equivalent, so its submit retry carries a bounded
    residual duplicate-job risk (attempts are capped at 3).
    """
    return {"Idempotency-Key": f"deep-research-{uuid4()}"}


__all__ = [
    "build_submit_idempotency_headers",
    "is_transient_submit_error",
    "submit_with_transient_retry",
]
