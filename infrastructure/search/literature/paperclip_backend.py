"""Paperclip MCP JSON-RPC backend."""

from __future__ import annotations

import json
from typing import Any, Iterable

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.literature.base import BackendError, SearchBackend
from infrastructure.search.literature.http_client import HttpClient, UrllibHttpClient
from infrastructure.search.literature.models import Paper, SearchQuery
from infrastructure.search.literature.paperclip_text_parser import papers_from_text_content

logger = get_logger(__name__)


class PaperclipBackend(SearchBackend):
    """Paperclip (paperclip.gxl.ai) HTTP backend."""

    name = "paperclip"
    base_url = "https://paperclip.gxl.ai/mcp"
    sdk_user_agent = "gxl-paperclip/0.3.0"

    def __init__(
        self,
        *,
        api_key: str,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("PaperclipBackend requires an api_key")
        self.api_key = api_key
        self.http = http_client or UrllibHttpClient()
        self.base_url = base_url or self.base_url
        self.timeout = timeout
        self._call_id = 0

    def _build_command(self, query: SearchQuery) -> str:
        import shlex

        parts = ["search", shlex.quote(query.text)]
        if query.max_results:
            parts += ["-n", str(query.max_results)]
        if query.year_min is not None:
            parts += ["--since", str(query.year_min)]
        return " ".join(parts)

    def search(self, query: SearchQuery) -> list[Paper]:
        """Search for results matching a query."""
        self._call_id += 1
        command = self._build_command(query)
        payload = {
            "jsonrpc": "2.0",
            "id": self._call_id,
            "method": "tools/call",
            "params": {
                "name": "paperclip",
                "arguments": {
                    "command": command,
                    "description": command[:80],
                    "skip_truncation": True,
                },
            },
        }
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": self.sdk_user_agent,
            "Accept": "application/json, text/event-stream",
        }
        try:
            resp = self.http.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except BackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise BackendError(f"Paperclip request failed: {exc}") from exc

        if resp.status_code != 200:
            raise BackendError(f"Paperclip returned HTTP {resp.status_code} (body[:200]: {resp.text[:200]!r})")
        try:
            envelope = resp.json()
        except json.JSONDecodeError as exc:
            raise BackendError(f"Paperclip returned non-JSON body: {exc}") from exc

        if isinstance(envelope, dict) and "error" in envelope:
            err = envelope["error"]
            msg = err.get("message", "Unknown MCP error") if isinstance(err, dict) else str(err)
            raise BackendError(f"Paperclip MCP error: {msg}")

        return self._extract_papers(envelope)

    def _extract_papers(self, envelope: Any) -> list[Paper]:
        if isinstance(envelope, list):
            return self._records_to_papers(envelope)

        if not isinstance(envelope, dict):
            raise BackendError("Paperclip returned an unexpected payload shape")

        result = envelope.get("result")
        if isinstance(result, dict):
            sc = result.get("structuredContent")
            if isinstance(sc, dict):
                for key in ("papers", "results", "items"):
                    if isinstance(sc.get(key), list):
                        return self._records_to_papers(sc[key])
            for key in ("papers", "results", "items"):
                if isinstance(result.get(key), list):
                    return self._records_to_papers(result[key])
            content = result.get("content")
            if isinstance(content, list):
                return papers_from_text_content(content, source=self.name)
        for key in ("papers", "results", "items"):
            if isinstance(envelope.get(key), list):
                return self._records_to_papers(envelope[key])
        return []

    def _records_to_papers(self, records: Iterable[dict[str, Any]]) -> list[Paper]:
        out: list[Paper] = []
        for record in records or []:
            if not isinstance(record, dict):
                continue
            try:
                paper = Paper.from_dict({**record, "source": self.name})
                out.append(paper)
            except (TypeError, ValueError) as exc:
                logger.debug("Skipping malformed Paperclip record: %s", exc)
                continue
        return out


__all__ = ["PaperclipBackend"]
