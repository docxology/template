"""Provider dispatch for deep research jobs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic, sleep
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
from infrastructure.search.deep_research.retry import submit_with_transient_retry

ProviderName = Literal["auto", "openai", "gemini"]


class DeepResearchWaitTimeout(RuntimeError):
    """Raised when wait/wait_many exceeds its poll budget with jobs still pending.

    Carries the still-pending handles so the caller can re-poll or cancel them
    instead of losing track of paid background jobs.
    """

    def __init__(self, pending: dict[str, DeepResearchJobHandle], waited_seconds: float) -> None:
        self.pending = dict(pending)
        self.waited_seconds = waited_seconds
        providers = ", ".join(sorted(pending)) or "none"
        super().__init__(
            f"Deep research wait exceeded {waited_seconds:.0f}s budget with pending job(s) "
            f"for: {providers}. Handles preserved on this exception (.pending) so the "
            "still-running paid job(s) can be re-polled or cancelled."
        )


@dataclass(frozen=True)
class DeepResearchClient:
    """Dispatches deep research jobs to the best available provider."""

    config: DeepResearchConfig

    @classmethod
    def from_env(cls) -> "DeepResearchClient":
        """Construct an instance from environment variables, or return None."""
        return cls(DeepResearchConfig.from_env())

    def openai_provider(self) -> OpenAIDeepResearchProvider:
        """Return the OpenAI provider configuration."""
        return OpenAIDeepResearchProvider(api_key=self.config.openai_api_key, model=self.config.openai_model)

    def gemini_provider(self) -> GeminiDeepResearchProvider:
        """Return the Gemini provider configuration."""
        return GeminiDeepResearchProvider(api_key=self.config.gemini_api_key, agent=self.config.gemini_agent)

    def available_providers(self) -> tuple[str, ...]:
        """Return the list of available providers."""
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

    def _provider_for(self, name: str) -> OpenAIDeepResearchProvider | GeminiDeepResearchProvider:
        """Resolve a provider adapter by name.

        Single seam through which ``submit``/``poll``/``cancel`` reach an
        adapter, so tests can inject a real recording provider via subclassing
        without patching SDK internals.
        """
        if name == "openai":
            return self.openai_provider()
        if name == "gemini":
            return self.gemini_provider()
        raise RuntimeError(f"Unknown deep research provider: {name}")

    def submit(self, request: DeepResearchRequest) -> DeepResearchJobHandle:
        """Submit a request to the API."""
        provider = self.select_provider(request)
        return self._provider_for(provider).submit(request)

    def poll(self, handle: DeepResearchJobHandle) -> DeepResearchResult:
        """Poll one job, retrying transient connection/timeout errors.

        A live poll is an HTTPS round-trip; an unwrapped transient failure
        during a long (30-60+ minute) run would crash the whole wait loop and
        discard every still-pending handle. Retrying transients here keeps the
        loop alive; non-transient errors (auth, validation, quota) propagate.
        """
        provider = self._provider_for(handle.provider)
        return submit_with_transient_retry(
            lambda: provider.poll(handle.job_id),
            provider=handle.provider,
        )

    def cancel(self, handle: DeepResearchJobHandle) -> DeepResearchResult:
        """Cancel a running background job so it stops billing (DR-3).

        ``background=True`` jobs bill to completion even if never polled, so the
        cost-containment story in the README needs a real cancel path. Wrapped
        in the same transient-retry helper as ``poll`` because the cancel call
        is an HTTPS round-trip too.
        """
        provider = self._provider_for(handle.provider)
        return submit_with_transient_retry(
            lambda: provider.cancel(handle.job_id),
            provider=handle.provider,
        )

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

    def wait(
        self,
        handle: DeepResearchJobHandle,
        *,
        poll_interval_seconds: float = 10.0,
        max_wait_seconds: float | None = None,
    ) -> DeepResearchResult:
        """Poll a single provider until it reaches a terminal state.

        ``max_wait_seconds`` bounds the total poll budget. On expiry a
        ``DeepResearchWaitTimeout`` is raised carrying the still-pending handle
        (in ``.pending``) so the paid background job can be re-polled or
        cancelled rather than silently lost. ``None`` (default) waits forever,
        preserving prior behaviour. Gemini runs documented at 30-60+ minutes —
        give a budget well above that or do not set one.
        """
        start = monotonic()
        while True:
            result = self.poll(handle)
            if result.status not in ("queued", "in_progress"):
                return result
            if max_wait_seconds is not None and (monotonic() - start) >= max_wait_seconds:
                raise DeepResearchWaitTimeout({handle.provider: handle}, monotonic() - start)
            sleep(poll_interval_seconds)

    def wait_many(
        self,
        handles: dict[str, DeepResearchJobHandle],
        *,
        poll_interval_seconds: float = 10.0,
        max_wait_seconds: float | None = None,
    ) -> dict[str, DeepResearchResult]:
        """Poll multiple providers until each job reaches a terminal state.

        ``max_wait_seconds`` bounds the total poll budget across all providers.
        On expiry a ``DeepResearchWaitTimeout`` is raised carrying every
        still-pending handle (in ``.pending``); jobs that already reached a
        terminal state are dropped from ``.pending`` so only the genuinely
        running paid jobs need re-polling or cancelling.
        """
        pending = dict(handles)
        results: dict[str, DeepResearchResult] = {}
        start = monotonic()
        while pending:
            for provider, handle in list(pending.items()):
                result = self.poll(handle)
                if result.status in ("queued", "in_progress"):
                    continue
                results[provider] = result
                pending.pop(provider)
            if pending:
                if max_wait_seconds is not None and (monotonic() - start) >= max_wait_seconds:
                    raise DeepResearchWaitTimeout(pending, monotonic() - start)
                sleep(poll_interval_seconds)
        return results

    def submit_and_wait_many(
        self,
        request: DeepResearchRequest,
        providers: tuple[str, ...] = ("openai", "gemini"),
        *,
        poll_interval_seconds: float = 10.0,
        max_wait_seconds: float | None = None,
    ) -> dict[str, DeepResearchResult]:
        """Submit one request to multiple providers and wait for all reports."""
        handles = self.submit_many(request, providers=providers)
        return self.wait_many(
            handles,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
        )

    def submit_project_and_save_reports(
        self,
        project_root: str | Path,
        query: str,
        *,
        request: DeepResearchRequest | None = None,
        providers: tuple[str, ...] = ("openai", "gemini"),
        poll_interval_seconds: float = 10.0,
        max_wait_seconds: float | None = None,
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
            max_wait_seconds=max_wait_seconds,
        )
        return save_deep_research_results(project_root, results, request=packaged_request)


__all__ = ["DeepResearchClient", "DeepResearchWaitTimeout", "ProviderName"]
