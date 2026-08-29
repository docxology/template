"""Minimal, injectable HTTP transport for the Monid client."""

from __future__ import annotations

import json as _json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from infrastructure.search.monid.errors import MonidError


@dataclass
class MonidResponse:
    """Minimal HTTP response wrapper."""

    status_code: int
    text: str
    url: str

    def json(self) -> Any:
        """Return the response as parsed JSON."""
        try:
            return _json.loads(self.text)
        except _json.JSONDecodeError as exc:
            raise MonidError(
                f"Monid returned a non-JSON body (HTTP {self.status_code})",
                status=self.status_code,
                body=self.text[:500],
            ) from exc


class MonidHttpClient(Protocol):
    """Structural type for the transport the client depends on."""

    def request(
        self,
        method: str,
        url: str,
        *,
        json: Mapping[str, Any] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> MonidResponse:
        """Send an HTTP request and return a :class:`MonidResponse`."""
        ...  # pragma: no cover - protocol declaration


class UrllibMonidHttpClient:
    """stdlib ``urllib`` client for JSON REST calls."""

    def request(
        self,
        method: str,
        url: str,
        *,
        json: Mapping[str, Any] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> MonidResponse:
        """Send an HTTP request."""
        data = _json.dumps(dict(json or {})).encode("utf-8") if json is not None else None
        req = urllib.request.Request(url, data=data, headers=dict(headers), method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                charset = resp.headers.get_content_charset() or "utf-8"
                text = resp.read().decode(charset, errors="replace")
                return MonidResponse(status_code=resp.status, text=text, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover - defensive
                pass
            return MonidResponse(status_code=exc.code, text=err_body, url=url)
        except urllib.error.URLError as exc:
            raise MonidError(f"network error {method} {url}: {exc.reason}") from exc


__all__ = ["MonidHttpClient", "MonidResponse", "UrllibMonidHttpClient"]
