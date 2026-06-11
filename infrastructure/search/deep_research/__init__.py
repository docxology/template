"""Deep research orchestration over OpenAI and Gemini.

This package provides a provider-neutral job model and lazy adapters for:

* OpenAI Responses API deep research models (`o3-deep-research`,
  `o4-mini-deep-research`)
* Gemini Deep Research agent (`deep-research-preview-04-2026`,
  `deep-research-max-preview-04-2026`)

Imports are side-effect free. The optional SDKs are only loaded when a provider
is used, so the rest of :mod:`infrastructure.search` stays importable without
those extras installed.
"""

from infrastructure.search.deep_research.artifacts import (
    DeepResearchReportBundle,
    save_deep_research_result,
    save_deep_research_results,
)
from infrastructure.search.deep_research.client import DeepResearchClient, DeepResearchWaitTimeout
from infrastructure.search.deep_research.config import (
    DEFAULT_GEMINI_AGENT,
    DEFAULT_OPENAI_MODEL,
    DeepResearchConfig,
)
from infrastructure.search.deep_research.gemini import (
    GeminiDeepResearchError,
    GeminiDeepResearchProvider,
    build_gemini_payload,
    build_gemini_tools,
)
from infrastructure.search.deep_research.models import (
    DeepResearchAnalysis,
    DeepResearchCitation,
    DeepResearchJobHandle,
    DeepResearchMCPServer,
    DeepResearchRequest,
    DeepResearchResult,
    DeepResearchSources,
)
from infrastructure.search.deep_research.project_context import (
    DeepResearchProjectContext,
    build_project_deep_research_request,
    collect_project_context,
)
from infrastructure.search.deep_research.openai import (
    OpenAIDeepResearchError,
    OpenAIDeepResearchProvider,
    build_openai_payload,
    build_openai_tools,
)

__all__ = [
    "DEFAULT_GEMINI_AGENT",
    "DEFAULT_OPENAI_MODEL",
    "DeepResearchAnalysis",
    "DeepResearchCitation",
    "DeepResearchClient",
    "DeepResearchConfig",
    "DeepResearchJobHandle",
    "DeepResearchMCPServer",
    "DeepResearchReportBundle",
    "DeepResearchRequest",
    "DeepResearchResult",
    "DeepResearchSources",
    "DeepResearchProjectContext",
    "DeepResearchWaitTimeout",
    "GeminiDeepResearchError",
    "GeminiDeepResearchProvider",
    "OpenAIDeepResearchError",
    "OpenAIDeepResearchProvider",
    "build_project_deep_research_request",
    "build_gemini_payload",
    "build_gemini_tools",
    "build_openai_payload",
    "build_openai_tools",
    "collect_project_context",
    "save_deep_research_result",
    "save_deep_research_results",
]
