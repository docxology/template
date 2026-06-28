"""Minimal, injectable HTTP transport for the Exa client.

Mirrors the design of :mod:`infrastructure.search.literature.http_client` (a
structural :class:`ExaHttpClient` Protocol plus a stdlib implementation) but is
kept Exa-local so the two search interfaces share no imports. Tests inject a
fake transport or point :class:`UrllibExaHttpClient` at a ``pytest-httpserver``
URL — no mocking framework, per the repository's no-mocks policy.
"""

from __future__ import annotations

import json as _json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from infrastructure.search.exa.errors import ExaError


@dataclass
class ExaResponse:
    """Minimal HTTP response wrapper."""

    status_code: int
    text: str
    url: str

    def json(self) -> Any:
        try:
            return _json.loads(self.text)
        except _json.JSONDecodeError as exc:
            raise ExaError(
                f"Exa returned a non-JSON body (HTTP {self.status_code})",
                status=self.status_code,
                body=self.text[:500],
            ) from exc


class ExaHttpClient(Protocol):
    """Structural type for the transport the client depends on."""

    def post(
        self,
        url: str,
        *,
        json: Any,
        headers: dict[str, str],
        timeout: float,
    ) -> ExaResponse: ...  # pragma: no cover - protocol declaration


class UrllibExaHttpClient:
    """stdlib ``urllib`` POST client. Adequate for JSON REST calls."""

    def post(
        self,
        url: str,
        *,
        json: Any,
        headers: dict[str, str],
        timeout: float,
    ) -> ExaResponse:
        body = _json.dumps(json).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                charset = resp.headers.get_content_charset() or "utf-8"
                text = resp.read().decode(charset, errors="replace")
                return ExaResponse(status_code=resp.status, text=text, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover - defensive
                pass
            # Non-2xx is returned, not raised, so the client can attach API context.
            return ExaResponse(status_code=exc.code, text=err_body, url=url)
        except urllib.error.URLError as exc:
            raise ExaError(f"network error posting to {url}: {exc.reason}") from exc


__all__ = ["ExaHttpClient", "ExaResponse", "UrllibExaHttpClient"]
