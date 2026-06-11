"""OpenAI deep research adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.search.deep_research.config import DEFAULT_OPENAI_MODEL
from infrastructure.search.deep_research.models import (
    DeepResearchCitation,
    DeepResearchJobHandle,
    DeepResearchRequest,
    DeepResearchResult,
)
from infrastructure.search.deep_research.prompting import build_full_prompt
from infrastructure.search.deep_research.retry import (
    build_submit_idempotency_headers,
    submit_with_transient_retry,
)


class OpenAIDeepResearchError(RuntimeError):
    """Raised when the OpenAI deep research adapter cannot run."""


@dataclass(frozen=True)
class OpenAIDeepResearchOptions:
    api_key: str | None
    model: str = DEFAULT_OPENAI_MODEL


def build_openai_tools(request: DeepResearchRequest) -> list[dict[str, Any]]:
    """Translate provider-neutral source controls into OpenAI deep research tools."""
    tools: list[dict[str, Any]] = []

    if request.sources.web:
        tools.append({"type": "web_search_preview"})

    if request.sources.vector_store_ids:
        tools.append({"type": "file_search", "vector_store_ids": list(request.sources.vector_store_ids)})

    for server in request.sources.mcp_servers:
        tools.append(
            {
                "type": "mcp",
                "server_label": server.server_label,
                "server_url": server.server_url,
                "require_approval": "never",
            }
        )

    if request.analysis.use_code_interpreter:
        tools.append({"type": "code_interpreter", "container": {"type": "auto"}})

    return tools


def build_openai_payload(request: DeepResearchRequest, *, model: str | None = None) -> dict[str, Any]:
    """Build the Responses API payload without touching the SDK."""
    tools = build_openai_tools(request)
    if not (request.sources.web or request.sources.vector_store_ids or request.sources.mcp_servers):
        raise OpenAIDeepResearchError("OpenAI deep research requires at least one supported data source")

    payload: dict[str, Any] = {
        "model": model or request.openai_model or DEFAULT_OPENAI_MODEL,
        "input": request.query,
        "instructions": build_full_prompt(request),
        "background": request.analysis.background,
        "store": True,
        "tools": tools,
    }
    if request.analysis.max_tool_calls:
        payload["max_tool_calls"] = request.analysis.max_tool_calls
    payload["reasoning"] = {"summary": "auto"} if request.thinking_summaries else {"summary": "none"}
    return payload


class OpenAIDeepResearchProvider:
    """Lazy SDK wrapper around the OpenAI Responses API."""

    def __init__(self, *, api_key: str | None, model: str = DEFAULT_OPENAI_MODEL) -> None:
        self.options = OpenAIDeepResearchOptions(api_key=api_key, model=model)

    @property
    def is_available(self) -> bool:
        return bool(self.options.api_key)

    def _client(self):
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised only when optional SDK is absent
            raise OpenAIDeepResearchError(
                "The optional 'openai' package is not installed. Install the OpenAI SDK to use this provider."
            ) from exc
        if not self.options.api_key:
            raise OpenAIDeepResearchError("OPENAI_API_KEY is required for the OpenAI deep research provider")
        return OpenAI(api_key=self.options.api_key)

    def submit(self, request: DeepResearchRequest) -> DeepResearchJobHandle:
        payload = build_openai_payload(request, model=self.options.model)
        client = self._client()
        # One key per logical submission, reused across retries. Best-effort
        # dedup: Idempotency-Key is honoured on OpenAI POST endpoints generally
        # but is not documented for background Responses jobs specifically, so
        # a retried-after-delivery submit MAY still create a duplicate job.
        headers = build_submit_idempotency_headers()
        resp = submit_with_transient_retry(
            lambda: client.responses.create(**payload, extra_headers=headers),
            provider="openai",
        )
        return DeepResearchJobHandle(
            provider="openai",
            job_id=str(resp.id),
            status=str(getattr(resp, "status", "queued")),
            request=request,
            raw={"id": getattr(resp, "id", None), "status": getattr(resp, "status", None)},
        )

    def poll(self, job_id: str) -> DeepResearchResult:
        resp = self._client().responses.retrieve(job_id)
        citations = _extract_citations(resp)
        trace = _extract_trace(resp)
        return DeepResearchResult(
            provider="openai",
            job_id=job_id,
            status=str(getattr(resp, "status", "unknown")),
            output_text=str(getattr(resp, "output_text", "")),
            citations=citations,
            trace=trace,
            raw={"id": getattr(resp, "id", None), "status": getattr(resp, "status", None)},
        )


def _extract_citations(resp: Any) -> tuple[DeepResearchCitation, ...]:
    annotations = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            for annotation in getattr(content, "annotations", []) or []:
                annotations.append(
                    DeepResearchCitation(
                        title=getattr(annotation, "title", None),
                        url=getattr(annotation, "url", None),
                        start_index=getattr(annotation, "start_index", None),
                        end_index=getattr(annotation, "end_index", None),
                        text=getattr(annotation, "text", None),
                        metadata={},
                    )
                )
    return tuple(annotations)


def _extract_trace(resp: Any) -> tuple[dict[str, Any], ...]:
    trace: list[dict[str, Any]] = []
    for item in getattr(resp, "output", []) or []:
        trace.append({"type": getattr(item, "type", None), "raw": item})
    return tuple(trace)


__all__ = [
    "OpenAIDeepResearchError",
    "OpenAIDeepResearchOptions",
    "OpenAIDeepResearchProvider",
    "build_openai_payload",
    "build_openai_tools",
]
