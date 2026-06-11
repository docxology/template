"""Tests for deep research wait budgets, poll retry, and cancel (DR-2, DR-3).

No Mocks Policy: instead of patching SDK internals we inject a *real* recording
provider object with a scripted poll/cancel sequence, wired in through a real
DeepResearchClient subclass that overrides the single `_provider_for` seam.
Wait loops are kept fast by injecting `sleep`-free intervals via monkeypatch on
the module `sleep` symbol (monkeypatch is permitted) and by using a
`max_wait_seconds=0` budget for the expiry paths.
"""

from __future__ import annotations

import pytest

import infrastructure.search.deep_research.client as client_mod
from infrastructure.search.deep_research.cli import build_parser
from infrastructure.search.deep_research.client import (
    DeepResearchClient,
    DeepResearchWaitTimeout,
)
from infrastructure.search.deep_research.config import DeepResearchConfig
from infrastructure.search.deep_research.models import (
    DeepResearchJobHandle,
    DeepResearchRequest,
    DeepResearchResult,
)


class RecordingProvider:
    """A real provider stand-in with scripted poll/cancel responses.

    `poll_statuses` is consumed one status per call; the last value repeats.
    Every poll and cancel call is recorded for assertions. `poll_raises` lets a
    test script a transient exception on the first N poll calls to exercise the
    retry wrapper.
    """

    def __init__(self, provider: str, poll_statuses, *, poll_raises=None) -> None:
        self.provider = provider
        self._statuses = list(poll_statuses)
        self._poll_raises = list(poll_raises or [])
        self.poll_calls: list[str] = []
        self.cancel_calls: list[str] = []

    def poll(self, job_id: str) -> DeepResearchResult:
        self.poll_calls.append(job_id)
        if self._poll_raises:
            exc = self._poll_raises.pop(0)
            if exc is not None:
                raise exc
        status = self._statuses.pop(0) if len(self._statuses) > 1 else self._statuses[0]
        return DeepResearchResult(provider=self.provider, job_id=job_id, status=status, output_text="ok")

    def cancel(self, job_id: str) -> DeepResearchResult:
        self.cancel_calls.append(job_id)
        return DeepResearchResult(provider=self.provider, job_id=job_id, status="cancelled", output_text="")


class InjectedClient(DeepResearchClient):
    """Real client subclass routing `_provider_for` to recording providers."""

    def with_providers(self, providers: dict[str, RecordingProvider]) -> "InjectedClient":
        object.__setattr__(self, "_recording_providers", providers)
        return self

    def _provider_for(self, name: str):  # type: ignore[override]
        return self._recording_providers[name]


def _client(providers: dict[str, RecordingProvider]) -> InjectedClient:
    config = DeepResearchConfig(openai_api_key="sk-openai", gemini_api_key="gm-key")
    return InjectedClient(config).with_providers(providers)


def _handle(provider: str, job_id: str = "job_1") -> DeepResearchJobHandle:
    return DeepResearchJobHandle(
        provider=provider,
        job_id=job_id,
        status="queued",
        request=DeepResearchRequest(query="q", provider=provider),
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Keep wait loops and retry backoff instantaneous; monkeypatch is permitted.
    monkeypatch.setattr(client_mod, "sleep", lambda _seconds: None)
    monkeypatch.setattr("infrastructure.search.deep_research.retry.sleep", lambda _seconds: None)


def test_wait_returns_when_terminal():
    provider = RecordingProvider("openai", ["in_progress", "completed"])
    client = _client({"openai": provider})
    result = client.wait(_handle("openai"), poll_interval_seconds=0.0)
    assert result.status == "completed"
    assert len(provider.poll_calls) == 2


def test_wait_raises_timeout_with_handle_preserved():
    provider = RecordingProvider("openai", ["in_progress"])
    client = _client({"openai": provider})
    handle = _handle("openai")
    with pytest.raises(DeepResearchWaitTimeout) as excinfo:
        client.wait(handle, poll_interval_seconds=0.0, max_wait_seconds=0.0)
    # Handle preserved so the paid job can be re-polled or cancelled.
    assert excinfo.value.pending == {"openai": handle}


def test_wait_retries_transient_poll_error():
    # First poll raises a transient ConnectionError; retry succeeds.
    provider = RecordingProvider(
        "openai",
        ["completed"],
        poll_raises=[ConnectionError("boom"), None],
    )
    client = _client({"openai": provider})
    result = client.wait(_handle("openai"), poll_interval_seconds=0.0)
    assert result.status == "completed"
    # Two poll attempts: one transient failure + one success.
    assert len(provider.poll_calls) == 2


def test_poll_does_not_retry_nontransient_error():
    provider = RecordingProvider("openai", ["completed"], poll_raises=[ValueError("auth")])
    client = _client({"openai": provider})
    with pytest.raises(ValueError, match="auth"):
        client.poll(_handle("openai"))
    assert len(provider.poll_calls) == 1


def test_wait_many_returns_all_terminal():
    op = RecordingProvider("openai", ["in_progress", "completed"])
    gm = RecordingProvider("gemini", ["completed"])
    client = _client({"openai": op, "gemini": gm})
    handles = {"openai": _handle("openai"), "gemini": _handle("gemini")}
    results = client.wait_many(handles, poll_interval_seconds=0.0)
    assert set(results) == {"openai", "gemini"}
    assert results["openai"].status == "completed"
    assert results["gemini"].status == "completed"


def test_wait_many_timeout_drops_finished_keeps_pending():
    # gemini completes immediately; openai stays in_progress -> only openai pending.
    op = RecordingProvider("openai", ["in_progress"])
    gm = RecordingProvider("gemini", ["completed"])
    client = _client({"openai": op, "gemini": gm})
    handles = {"openai": _handle("openai"), "gemini": _handle("gemini")}
    with pytest.raises(DeepResearchWaitTimeout) as excinfo:
        client.wait_many(handles, poll_interval_seconds=0.0, max_wait_seconds=0.0)
    assert set(excinfo.value.pending) == {"openai"}


def test_cancel_invokes_provider_cancel():
    provider = RecordingProvider("openai", ["in_progress"])
    client = _client({"openai": provider})
    result = client.cancel(_handle("openai", job_id="resp_abc"))
    assert result.status == "cancelled"
    assert provider.cancel_calls == ["resp_abc"]


def test_cancel_retries_transient_then_succeeds(monkeypatch):
    class FlakyCancel(RecordingProvider):
        def __init__(self):
            super().__init__("openai", ["in_progress"])
            self._cancel_fail_once = True

        def cancel(self, job_id):
            self.cancel_calls.append(job_id)
            if self._cancel_fail_once:
                self._cancel_fail_once = False
                raise ConnectionError("transient")
            return DeepResearchResult(provider="openai", job_id=job_id, status="cancelled", output_text="")

    provider = FlakyCancel()
    client = _client({"openai": provider})
    # retry helper sleeps via its own module; keep it instant.
    monkeypatch.setattr("infrastructure.search.deep_research.retry.sleep", lambda _s: None)
    result = client.cancel(_handle("openai", job_id="resp_abc"))
    assert result.status == "cancelled"
    assert provider.cancel_calls == ["resp_abc", "resp_abc"]


def test_cli_parser_supports_cancel_subcommand():
    args = build_parser().parse_args(["cancel", "openai", "resp_123"])
    assert args.command == "cancel"
    assert args.provider == "openai"
    assert args.job_id == "resp_123"


def test_cli_parser_run_project_max_wait():
    args = build_parser().parse_args(["run-project", "some/root", "q", "--providers", "openai", "--max-wait", "120"])
    assert args.command == "run-project"
    assert args.max_wait == 120.0
