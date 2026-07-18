"""Gemini deep research adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.search.deep_research.config import DEFAULT_GEMINI_AGENT
from infrastructure.search.deep_research.models import (
    DeepResearchCitation,
    DeepResearchJobHandle,
    DeepResearchRequest,
    DeepResearchResult,
)
from infrastructure.search.deep_research.prompting import build_full_prompt
from infrastructure.search.deep_research.retry import submit_with_transient_retry


class GeminiDeepResearchError(RuntimeError):
    """Raised when the Gemini deep research adapter cannot run."""


@dataclass(frozen=True)
class GeminiDeepResearchOptions:
    """Data container for GeminiDeepResearchOptions."""

    api_key: str | None
    agent: str = DEFAULT_GEMINI_AGENT


def build_gemini_tools(request: DeepResearchRequest) -> list[dict[str, Any]]:
    """Translate provider-neutral source controls into Gemini deep research tools."""
    tools: list[dict[str, Any]] = []

    if request.sources.web:
        tools.append({"type": "google_search"})

    if request.sources.file_search_store_names:
        tools.append({"type": "file_search", "file_search_store_names": list(request.sources.file_search_store_names)})

    for server in request.sources.mcp_servers:
        tool: dict[str, Any] = {
            "type": "mcp_server",
            "name": server.server_label,
            "url": server.server_url,
        }
        if server.headers:
            tool["headers"] = dict(server.headers)
        if server.allowed_tools:
            tool["allowed_tools"] = list(server.allowed_tools)
        tools.append(tool)

    if request.analysis.use_code_interpreter:
        tools.append({"type": "code_execution"})

    return tools


def build_gemini_payload(request: DeepResearchRequest, *, agent: str | None = None) -> dict[str, Any]:
    """Build the Interactions API payload without touching the SDK."""
    tools = build_gemini_tools(request)
    if not tools:
        raise GeminiDeepResearchError("Gemini deep research requires at least one supported data source")

    payload: dict[str, Any] = {
        "agent": agent or request.gemini_agent or DEFAULT_GEMINI_AGENT,
        "input": build_full_prompt(request),
        "agent_config": {
            "type": "deep-research",
            "thinking_summaries": "auto" if request.thinking_summaries else "none",
            "visualization": "auto" if request.visualization else "off",
            "collaborative_planning": request.collaborative_planning,
        },
        "background": request.analysis.background,
        "store": True,
        "tools": tools,
    }
    return payload


class GeminiDeepResearchProvider:
    """Lazy SDK wrapper around the Gemini Interactions API."""

    def __init__(self, *, api_key: str | None, agent: str = DEFAULT_GEMINI_AGENT) -> None:
        self.options = GeminiDeepResearchOptions(api_key=api_key, agent=agent)

    @property
    def is_available(self) -> bool:
        """Return True if the service is available (credentials present)."""
        return bool(self.options.api_key)

    def _client(self) -> Any:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - exercised only when optional SDK is absent
            raise GeminiDeepResearchError(
                "The optional 'google-genai' package is not installed. Install the Gemini SDK to use this provider."
            ) from exc
        if not self.options.api_key:
            raise GeminiDeepResearchError("GEMINI_API_KEY is required for the Gemini deep research provider")
        return genai.Client(api_key=self.options.api_key)

    def submit(self, request: DeepResearchRequest) -> DeepResearchJobHandle:
        """Submit a request to the API."""
        payload = build_gemini_payload(request, agent=self.options.agent)
        client = self._client()
        resp = submit_with_transient_retry(lambda: client.interactions.create(**payload), provider="gemini")
        return DeepResearchJobHandle(
            provider="gemini",
            job_id=str(resp.id),
            status=str(getattr(resp, "status", "in_progress")),
            request=request,
            raw={"id": getattr(resp, "id", None), "status": getattr(resp, "status", None)},
        )

    def poll(self, job_id: str) -> DeepResearchResult:
        """Poll the API for completion status."""
        resp = self._client().interactions.get(job_id)
        return DeepResearchResult(
            provider="gemini",
            job_id=job_id,
            status=str(getattr(resp, "status", "unknown")),
            output_text=str(getattr(resp, "output_text", "")),
            citations=_extract_citations(resp),
            trace=_extract_trace(resp),
            raw={"id": getattr(resp, "id", None), "status": getattr(resp, "status", None)},
        )

    def cancel(self, job_id: str) -> DeepResearchResult:
        """Cancel a running interaction (Gemini ``interactions.cancel``)."""
        resp = self._client().interactions.cancel(job_id)
        return DeepResearchResult(
            provider="gemini",
            job_id=job_id,
            status=str(getattr(resp, "status", "cancelled")),
            output_text=str(getattr(resp, "output_text", "")),
            raw={"id": getattr(resp, "id", None), "status": getattr(resp, "status", None)},
        )


def _extract_citations(resp: Any) -> tuple[DeepResearchCitation, ...]:
    citations: list[DeepResearchCitation] = []
    for step in getattr(resp, "steps", []) or []:
        for content_item in getattr(step, "content", []) or []:
            if getattr(content_item, "type", None) != "text":
                continue
            for annotation in getattr(content_item, "annotations", []) or []:
                citations.append(
                    DeepResearchCitation(
                        title=getattr(annotation, "title", None),
                        url=getattr(annotation, "url", None),
                        start_index=getattr(annotation, "start_index", None),
                        end_index=getattr(annotation, "end_index", None),
                        text=getattr(annotation, "text", None),
                        metadata={},
                    )
                )
    return tuple(citations)


def _extract_trace(resp: Any) -> tuple[dict[str, Any], ...]:
    trace: list[dict[str, Any]] = []
    for step in getattr(resp, "steps", []) or []:
        trace.append({"type": getattr(step, "type", None), "raw": step})
    return tuple(trace)


__all__ = [
    "GeminiDeepResearchError",
    "GeminiDeepResearchOptions",
    "GeminiDeepResearchProvider",
    "build_gemini_payload",
    "build_gemini_tools",
]
