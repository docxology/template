"""Tests for deep_research transient retry, CLI surface, and context packing.

No-mocks policy: real callables, real tmp project trees, real argparse runs.
Live provider dispatch is exercised separately (opt-in, requires keys); these
tests cover the deterministic layer only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.search.deep_research.cli import build_parser, run
from infrastructure.search.deep_research.project_context import (
    DEFAULT_CONTEXT_DIRS,
    collect_project_context,
)
from infrastructure.search.deep_research.retry import (
    is_transient_submit_error,
    submit_with_transient_retry,
)


class _FlakyConnection(ConnectionError):
    pass


def test_retry_recovers_from_transient_connection_errors() -> None:
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise _FlakyConnection("Connection error.")
        return "submitted"

    result = submit_with_transient_retry(operation, provider="test", base_delay_seconds=0.0)
    assert result == "submitted"
    assert len(calls) == 3


def test_retry_propagates_non_transient_errors_immediately() -> None:
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        raise ValueError("bad payload")

    with pytest.raises(ValueError, match="bad payload"):
        submit_with_transient_retry(operation, provider="test", base_delay_seconds=0.0)
    assert len(calls) == 1


def test_retry_exhausts_attempts_then_raises_transient() -> None:
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        raise _FlakyConnection("Connection error.")

    with pytest.raises(_FlakyConnection):
        submit_with_transient_retry(operation, provider="test", attempts=3, base_delay_seconds=0.0)
    assert len(calls) == 3


def test_transient_classification_by_name_without_vendor_imports() -> None:
    class APIConnectionError(Exception):  # same NAME as vendor SDK classes, no import
        pass

    class ReadTimeoutError(Exception):
        pass

    class AuthenticationError(Exception):
        pass

    assert is_transient_submit_error(APIConnectionError())
    assert is_transient_submit_error(ReadTimeoutError())
    assert is_transient_submit_error(ConnectionResetError())
    assert not is_transient_submit_error(AuthenticationError())
    assert not is_transient_submit_error(ValueError("nope"))


def test_manuscript_sources_are_packaged_without_render(tmp_path: Path) -> None:
    """Paper sources under manuscript/ must be packaged on a fresh, un-rendered tree."""
    assert DEFAULT_CONTEXT_DIRS[0] == "manuscript"
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "01_intro.md").write_text("Active inference intro.", encoding="utf-8")
    context = collect_project_context(tmp_path)
    assert any(path.name == "01_intro.md" for path in context.artifact_paths)
    assert "Active inference intro." in context.context_text


def test_cli_providers_reports_environment_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_DEEP_RESEARCH_MODEL", "o3-deep-research")
    args = build_parser().parse_args(["providers"])
    payload = run(args)
    assert payload["available"] == ["openai"]
    assert payload["openai_model"] == "o3-deep-research"


def test_cli_parser_covers_all_subcommands() -> None:
    parser = build_parser()
    args = parser.parse_args(["submit", "a query", "--provider", "openai"])
    assert args.command == "submit" and args.provider == "openai"
    args = parser.parse_args(["poll", "openai", "resp_123"])
    assert args.command == "poll" and args.job_id == "resp_123"
    args = parser.parse_args(["run-project", "some/root", "q", "--providers", "openai"])
    assert args.command == "run-project" and args.providers == "openai"


def test_idempotency_headers_fresh_per_submission() -> None:
    from infrastructure.search.deep_research.retry import build_submit_idempotency_headers

    first = build_submit_idempotency_headers()
    second = build_submit_idempotency_headers()
    assert first.keys() == {"Idempotency-Key"}
    assert first["Idempotency-Key"].startswith("deep-research-")
    assert first["Idempotency-Key"] != second["Idempotency-Key"]
