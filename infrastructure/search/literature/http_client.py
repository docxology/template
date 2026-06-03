"""Injectable HTTP client for literature backends."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from infrastructure.search.literature.base import BackendError


@dataclass
class HttpResponse:
    """Minimal response object used by HTTP backends."""

    status_code: int
    text: str
    url: str

    def json(self) -> Any:
        return json.loads(self.text)


class HttpClient(Protocol):
    """Structural type for an HTTP client used by backends."""

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> HttpResponse: ...  # pragma: no cover

    def get_bytes(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> bytes: ...  # pragma: no cover

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: bytes | str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse: ...  # pragma: no cover


class UrllibHttpClient:
    """Tiny stdlib HTTP client. Adequate for read-only API calls in tests."""

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> HttpResponse:
        if params:
            qs = urllib.parse.urlencode(params, doseq=True)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{qs}"
        req = urllib.request.Request(url, headers=dict(headers or {}))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                charset = resp.headers.get_content_charset() or "utf-8"
                body = resp.read().decode(charset, errors="replace")
                return HttpResponse(status_code=resp.status, text=body, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover
                pass
            return HttpResponse(status_code=exc.code, text=body, url=url)
        except urllib.error.URLError as exc:
            raise BackendError(f"HTTP error fetching {url}: {exc.reason}") from exc

    def get_bytes(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> bytes:
        """Fetch raw response bytes (for binary payloads like PDFs).

        Unlike :meth:`get`, this does NOT decode the body as text — decoding a
        PDF as text and re-encoding corrupts every non-ASCII byte. Raises
        :class:`BackendError` on any non-2xx status or transport error.
        """
        if params:
            qs = urllib.parse.urlencode(params, doseq=True)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{qs}"
        req = urllib.request.Request(url, headers=dict(headers or {}))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                return resp.read()
        except urllib.error.HTTPError as exc:
            raise BackendError(f"HTTP {exc.code} fetching {url}") from exc
        except urllib.error.URLError as exc:
            raise BackendError(f"HTTP error fetching {url}: {exc.reason}") from exc

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: bytes | str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        body: bytes
        if json is not None:
            import json as _json

            body = _json.dumps(json).encode("utf-8")
            hdrs = dict(headers or {})
            hdrs.setdefault("Content-Type", "application/json")
        elif isinstance(data, str):
            body = data.encode("utf-8")
            hdrs = dict(headers or {})
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)
            hdrs = dict(headers or {})
        else:
            body = b""
            hdrs = dict(headers or {})

        req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                charset = resp.headers.get_content_charset() or "utf-8"
                resp_body = resp.read().decode(charset, errors="replace")
                return HttpResponse(status_code=resp.status, text=resp_body, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover
                pass
            return HttpResponse(status_code=exc.code, text=err_body, url=url)
        except urllib.error.URLError as exc:
            raise BackendError(f"HTTP error posting to {url}: {exc.reason}") from exc


class HttpGetMixin:
    """Shared GET helper for HTTP-backed search backends."""

    http: HttpClient
    base_url: str
    timeout: float

    def _http_get(self, params: dict[str, Any], *, label: str) -> HttpResponse:
        try:
            return self.http.get(self.base_url, params=params, timeout=self.timeout)
        except BackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise BackendError(f"{label} request failed: {exc}") from exc


__all__ = ["HttpClient", "HttpGetMixin", "HttpResponse", "UrllibHttpClient"]
