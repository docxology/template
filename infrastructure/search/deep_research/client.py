"""Provider dispatch for deep research jobs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from time import sleep
from typing import Literal

from infrastructure.search.deep_research.artifacts import (
    DeepResearchReportBundle,
    save_deep_research_results,
)
from infrastructure.search.deep_research.config import DeepResearchConfig
from infrastructure.search.deep_research.gemini import GeminiDeepResearchProvider
from infrastructure.search.deep_research.models import DeepResearchJobHandle, DeepResearchRequest, DeepResearchResult
from infrastructure.search.deep_research.openai import OpenAIDeepResearchProvider
from infrastructure.search.deep_research.project_context import build_project_deep_research_request

ProviderName = Literal["auto", "openai", "gemini"]


@dataclass(frozen=True)
class DeepResearchClient:
    """Dispatches deep research jobs to the best available provider."""

    config: DeepResearchConfig

    @classmethod
    def from_env(cls) -> "DeepResearchClient":
        return cls(DeepResearchConfig.from_env())

    def openai_provider(self) -> OpenAIDeepResearchProvider:
        return OpenAIDeepResearchProvider(api_key=self.config.openai_api_key, model=self.config.openai_model)

    def gemini_provider(self) -> GeminiDeepResearchProvider:
        return GeminiDeepResearchProvider(api_key=self.config.gemini_api_key, agent=self.config.gemini_agent)

    def available_providers(self) -> tuple[str, ...]:
        names: list[str] = []
        if self.config.has_openai:
            names.append("openai")
        if self.config.has_gemini:
            names.append("gemini")
        return tuple(names)

    def select_provider(self, request: DeepResearchRequest) -> str:
        """Pick a provider using capability-aware defaults.

        OpenAI is preferred when the job is heavy on private/internal sources
        (vector stores or remote MCP) because the Responses API gives us the
        cleanest project-scale artifact trail. Gemini is preferred when the job
        asks for collaborative planning or generated visuals.
        """
        if request.provider in ("openai", "gemini"):
            return request.provider

        if request.collaborative_planning or request.visualization:
            if self.config.has_gemini:
                return "gemini"
            if self.config.has_openai:
                return "openai"

        if request.sources.vector_store_ids or request.sources.file_search_store_names or request.sources.mcp_servers:
            if self.config.has_openai:
                return "openai"
            if self.config.has_gemini:
                return "gemini"

        if self.config.has_openai:
            return "openai"
        if self.config.has_gemini:
            return "gemini"

        raise RuntimeError("No deep research provider configured: set OPENAI_API_KEY and/or GEMINI_API_KEY")

    def submit(self, request: DeepResearchRequest) -> DeepResearchJobHandle:
        provider = self.select_provider(request)
        if provider == "openai":
            return self.openai_provider().submit(request)
        return self.gemini_provider().submit(request)

    def poll(self, handle: DeepResearchJobHandle) -> DeepResearchResult:
        if handle.provider == "openai":
            return self.openai_provider().poll(handle.job_id)
        if handle.provider == "gemini":
            return self.gemini_provider().poll(handle.job_id)
        raise RuntimeError(f"Unknown deep research provider: {handle.provider}")

    def submit_many(
        self,
        request: DeepResearchRequest,
        providers: tuple[str, ...] = ("openai", "gemini"),
    ) -> dict[str, DeepResearchJobHandle]:
        """Submit the same request to multiple providers.

        Validates every requested provider against ``available_providers()``
        BEFORE submitting any of them. Previously, if a later provider was
        unconfigured, ``submit`` raised only after an earlier provider's job
        (a PAID job for OpenAI/Gemini) had already been submitted — orphaning it
        with no handle returned to the caller.
        """
        available = set(self.available_providers())
        missing = [p for p in providers if p not in available]
        if missing:
            raise RuntimeError(
                "Cannot submit to unconfigured provider(s) "
                f"{', '.join(missing)}; available: {', '.join(sorted(available)) or 'none'}. "
                "No jobs were submitted (fail-fast to avoid orphaning a paid job)."
            )
        handles: dict[str, DeepResearchJobHandle] = {}
        for provider in providers:
            handles[provider] = self.submit(replace(request, provider=provider))
        return handles

    def wait(self, handle: DeepResearchJobHandle, *, poll_interval_seconds: float = 10.0) -> DeepResearchResult:
        """Poll a single provider until it reaches a terminal state."""
        while True:
            result = self.poll(handle)
            if result.status not in ("queued", "in_progress"):
                return result
            sleep(poll_interval_seconds)

    def wait_many(
        self,
        handles: dict[str, DeepResearchJobHandle],
        *,
        poll_interval_seconds: float = 10.0,
    ) -> dict[str, DeepResearchResult]:
        """Poll multiple providers until each job reaches a terminal state."""
        pending = dict(handles)
        results: dict[str, DeepResearchResult] = {}
        while pending:
            for provider, handle in list(pending.items()):
                result = self.poll(handle)
                if result.status in ("queued", "in_progress"):
                    continue
                results[provider] = result
                pending.pop(provider)
            if pending:
                sleep(poll_interval_seconds)
        return results

    def submit_and_wait_many(
        self,
        request: DeepResearchRequest,
        providers: tuple[str, ...] = ("openai", "gemini"),
        *,
        poll_interval_seconds: float = 10.0,
    ) -> dict[str, DeepResearchResult]:
        """Submit one request to multiple providers and wait for all reports."""
        handles = self.submit_many(request, providers=providers)
        return self.wait_many(handles, poll_interval_seconds=poll_interval_seconds)

    def submit_project_and_save_reports(
        self,
        project_root: str | Path,
        query: str,
        *,
        request: DeepResearchRequest | None = None,
        providers: tuple[str, ...] = ("openai", "gemini"),
        poll_interval_seconds: float = 10.0,
    ) -> dict[str, DeepResearchReportBundle]:
        """Pack project context, run both providers, and persist the reports."""
        packaged_request = build_project_deep_research_request(
            project_root,
            query,
            request=request,
        )
        results = self.submit_and_wait_many(
            packaged_request,
            providers=providers,
            poll_interval_seconds=poll_interval_seconds,
        )
        return save_deep_research_results(project_root, results, request=packaged_request)


__all__ = ["DeepResearchClient", "ProviderName"]
