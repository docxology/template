"""Minimal HTTP client for connector implementations.

Wraps :mod:`urllib.request` with:

* Configurable ``User-Agent`` header.
* Per-request timeout.
* Exponential-backoff retry on transient failures (429, 503, 500).
* In-memory TTL cache keyed on the full request URL.

All connector implementations should use this client so that retry logic
and caching live in one place.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


_DEFAULT_USER_AGENT = (
    "infrastructure-connectors/1.0 (+https://github.com/template/infrastructure; mailto:team@example.org)"
)

#: HTTP status codes that warrant an automatic retry.
_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


@dataclass
class _CacheEntry:
    data: Any
    expires_at: float  # monotonic time


class ConnectorHttpClient:
    """Stdlib-only HTTP client used by all connector implementations.

    Args:
        user_agent: ``User-Agent`` header sent with every request.
        timeout: Per-request timeout in seconds.
        max_retries: Maximum number of retry attempts on transient errors.
        backoff_base: Base interval (seconds) for exponential back-off.
        ttl: Cache TTL in seconds.  Pass ``0`` to disable caching.
    """

    def __init__(
        self,
        user_agent: str = _DEFAULT_USER_AGENT,
        timeout: float = 20.0,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        ttl: float = 300.0,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.ttl = ttl
        self._cache: dict[str, _CacheEntry] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_json(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Perform a GET request and return the parsed JSON body.

        Args:
            url: Request URL (query string parameters may be appended via
                *params*).
            params: Optional mapping of query-string parameters.
            headers: Optional extra headers merged with the default set.

        Returns:
            The decoded JSON payload (dict, list, etc.).

        Raises:
            ConnectorHttpError: On HTTP-level errors not resolved after retries.
            ConnectorHttpError: On JSON decoding failures.
        """
        full_url = self._build_url(url, params)
        cached = self._cache_get(full_url)
        if cached is not None:
            return cached

        response_data = self._get_with_retry(full_url, headers or {})
        self._cache_set(full_url, response_data)
        return response_data

    def get_text(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Perform a GET request and return the response body as plain text.

        Args:
            url: Request URL.
            params: Optional query-string parameters.
            headers: Optional extra headers.

        Returns:
            The response body decoded as UTF-8 text.

        Raises:
            ConnectorHttpError: On HTTP-level errors.
        """
        full_url = self._build_url(url, params)
        cached = self._cache_get(full_url)
        if cached is not None:
            return str(cached)

        resp = self._request_with_retry(full_url, headers or {})
        text = resp.decode("utf-8", errors="replace")
        self._cache_set(full_url, text)
        return text

    def clear_cache(self) -> int:
        """Evict all cached entries and return the number removed."""
        count = len(self._cache)
        self._cache.clear()
        return count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_url(url: str, params: dict[str, str] | None) -> str:
        if not params:
            return url
        encoded = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}{encoded}"

    def _build_request(self, url: str, extra_headers: dict[str, str]) -> urllib.request.Request:
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        headers.update(extra_headers)
        return urllib.request.Request(url, headers=headers)

    def _request_with_retry(self, url: str, headers: dict[str, str]) -> bytes:
        req = self._build_request(url, headers)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # nosec B310 — URLs are hard-coded to known public science APIs (OpenAlex, arXiv, etc.)
                    return bytes(resp.read())
            except urllib.error.HTTPError as exc:
                if exc.code in _RETRYABLE_STATUSES and attempt < self.max_retries:
                    time.sleep(self.backoff_base * (2**attempt))
                    last_exc = exc
                    continue
                raise ConnectorHttpError(f"HTTP {exc.code} from {url}") from exc
            except Exception as exc:
                if attempt < self.max_retries:
                    time.sleep(self.backoff_base * (2**attempt))
                    last_exc = exc
                    continue
                raise ConnectorHttpError(f"Request failed: {url}") from exc
        raise ConnectorHttpError(f"Exhausted retries for {url}") from last_exc

    def _get_with_retry(self, url: str, headers: dict[str, str]) -> Any:
        raw = self._request_with_retry(url, headers)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConnectorHttpError(f"Invalid JSON from {url}") from exc

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _cache_get(self, url: str) -> Any | None:
        if self.ttl <= 0:
            return None
        key = self._cache_key(url)
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._cache[key]
            return None
        return entry.data

    def _cache_set(self, url: str, data: Any) -> None:
        if self.ttl <= 0:
            return
        key = self._cache_key(url)
        self._cache[key] = _CacheEntry(data=data, expires_at=time.monotonic() + self.ttl)


class ConnectorHttpError(Exception):
    """Raised on HTTP transport or JSON parsing failures."""


__all__ = ["ConnectorHttpClient", "ConnectorHttpError"]
