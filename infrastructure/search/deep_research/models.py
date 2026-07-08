"""Shared models for deep research providers.

The package deliberately keeps request/response shapes provider-neutral so the
dispatcher can choose OpenAI or Gemini without forcing callers to learn two
different APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DeepResearchMCPServer:
    """Remote MCP server specification."""

    server_label: str
    server_url: str
    headers: dict[str, str] = field(default_factory=dict)
    allowed_tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeepResearchSources:
    """Source controls for a deep research job."""

    web: bool = True
    vector_store_ids: tuple[str, ...] = ()
    file_search_store_names: tuple[str, ...] = ()
    mcp_servers: tuple[DeepResearchMCPServer, ...] = ()

    def has_supported_source(self) -> bool:
        """Return whether supported source is present."""
        return bool(self.web or self.vector_store_ids or self.file_search_store_names or self.mcp_servers)


@dataclass(frozen=True)
class DeepResearchAnalysis:
    """Tooling and execution controls."""

    use_code_interpreter: bool = True
    max_tool_calls: int = 12
    background: bool = True
    stream: bool = False


@dataclass(frozen=True)
class DeepResearchRequest:
    """Provider-neutral deep research request."""

    query: str
    provider: str = "auto"
    openai_model: str = "o3-deep-research"
    gemini_agent: str = "deep-research-preview-04-2026"
    sources: DeepResearchSources = field(default_factory=DeepResearchSources)
    analysis: DeepResearchAnalysis = field(default_factory=DeepResearchAnalysis)
    collaborative_planning: bool = False
    visualization: bool = False
    thinking_summaries: bool = True
    output_format: str = "markdown"
    sections: tuple[str, ...] = ("executive_summary", "findings", "risks", "sources")
    instructions: str | None = None


@dataclass(frozen=True)
class DeepResearchCitation:
    """Normalized citation metadata."""

    title: str | None
    url: str | None
    start_index: int | None = None
    end_index: int | None = None
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeepResearchJobHandle:
    """Opaque provider job handle returned after submission."""

    provider: str
    job_id: str
    status: str
    request: DeepResearchRequest
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeepResearchResult:
    """Normalized terminal result returned after polling a job."""

    provider: str
    job_id: str
    status: str
    output_text: str
    citations: tuple[DeepResearchCitation, ...] = ()
    trace: tuple[dict[str, Any], ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "DeepResearchAnalysis",
    "DeepResearchCitation",
    "DeepResearchJobHandle",
    "DeepResearchMCPServer",
    "DeepResearchRequest",
    "DeepResearchResult",
    "DeepResearchSources",
]
