"""Shared HTTP retry helper for literature API clients."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any, Optional

import requests

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_SECONDS = 1.0


def request_with_retry(
    http: requests.Session,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
    max_retries: int = DEFAULT_MAX_RETRIES,
    delay_override: Optional[Callable[[float], None]] = None,
    stream: bool = False,
    **kwargs: Any,
) -> requests.Response:
    """Perform an HTTP request with retry on 429/5xx and RequestException backoff."""
    sleep_fn = delay_override or time.sleep
    response: requests.Response | None = None
    last_exc: requests.RequestException | None = None

    for attempt in range(max_retries + 1):
        try:
            response = http.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                stream=stream,
                **kwargs,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            sleep_fn(min(30.0, DEFAULT_RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 0.5)))
            continue

        if response.status_code in RETRYABLE_STATUS:
            if attempt >= max_retries:
                response.raise_for_status()
            sleep_fn(min(30.0, DEFAULT_RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 0.5)))
            continue

        response.raise_for_status()
        return response

    if last_exc is not None:
        raise last_exc
    raise requests.HTTPError("HTTP retries exhausted")
