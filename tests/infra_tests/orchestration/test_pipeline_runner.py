"""Tests for infrastructure.orchestration.pipeline_runner.

The runner is a thin facade over the existing
:class:`infrastructure.core.pipeline.PipelineExecutor`. We exercise the
banner emission and option-translation logic without invoking the real
heavy pipeline (which would need pandoc / LaTeX). The "no mocks" rule
is honoured by injecting a real subclass that overrides only the
heavy-IO methods, not by using ``unittest.mock``.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from infrastructure.orchestration.pipeline_runner import (
    MultiProjectInvocation,
    PipelineInvocation,
    PipelineRunner,
)


@dataclass
class _FakeStageResult:
    success: bool = True


class _StubExecutor:
    """Stand-in for PipelineExecutor that records calls and returns canned results."""

    last_instance: "_StubExecutor | None" = None

    def __init__(self, config: Any) -> None:
        self.config = config
        self.full_calls = 0
        self.core_calls = 0
        type(self).last_instance = self

    def execute_full_pipeline(self):
        self.full_calls += 1
        return [_FakeStageResult(True), _FakeStageResult(True)]

    def execute_core_pipeline(self):
        self.core_calls += 1
        return [_FakeStageResult(True)]


@pytest.fixture
def patched_runner(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> PipelineRunner:
    """A PipelineRunner with a stubbed executor (heavy IO not needed for these tests)."""
    monkeypatch.setattr("infrastructure.orchestration.pipeline_runner.PipelineExecutor", _StubExecutor)
    return PipelineRunner(repo_root=fake_repo, stream=io.StringIO())


def test_run_full_pipeline_emits_banners(patched_runner: PipelineRunner) -> None:
    rc = patched_runner.run(PipelineInvocation(project="template_code_project"))
    assert rc == 0
    text = patched_runner.stream.getvalue()
    assert "FULL PIPELINE" in text
    assert "Environment Setup" in text
    assert "Copy Outputs" in text
    assert _StubExecutor.last_instance is not None
    assert _StubExecutor.last_instance.full_calls == 1


def test_run_core_only_excludes_llm_banners(patched_runner: PipelineRunner) -> None:
    rc = patched_runner.run(PipelineInvocation(project="template_code_project", core_only=True))
    assert rc == 0
    text = patched_runner.stream.getvalue()
    assert "CORE PIPELINE" in text
    # LLM stages must not be banner-rendered in core-only mode
    assert "LLM Scientific Review" not in text
    assert "LLM Translations" not in text
    assert _StubExecutor.last_instance.core_calls == 1


def test_run_skip_infra_omits_infra_banner(patched_runner: PipelineRunner) -> None:
    patched_runner.run(PipelineInvocation(project="template_code_project", skip_infra=True))
    text = patched_runner.stream.getvalue()
    assert "Infrastructure Tests" not in text
    # Project Tests still present
    assert "Project Tests" in text


def test_run_writes_log_file(patched_runner: PipelineRunner, fake_repo: Path) -> None:
    patched_runner.run(PipelineInvocation(project="template_code_project"))
    log = fake_repo / "projects" / "template_code_project" / "output" / "logs" / "pipeline.log"
    assert log.exists()


def test_run_returns_failure_on_exception(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> None:
    class _BoomExecutor:
        def __init__(self, config):
            pass

        def execute_full_pipeline(self):
            raise RuntimeError("boom")

    monkeypatch.setattr("infrastructure.orchestration.pipeline_runner.PipelineExecutor", _BoomExecutor)
    runner = PipelineRunner(repo_root=fake_repo, stream=io.StringIO())
    rc = runner.run(PipelineInvocation(project="template_code_project"))
    assert rc == 1
    assert "FAILED" in runner.stream.getvalue()


def test_run_returns_failure_when_stage_unsuccessful(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> None:
    class _FailingExecutor:
        def __init__(self, config):
            pass

        def execute_full_pipeline(self):
            return [_FakeStageResult(False)]

        def execute_core_pipeline(self):
            return [_FakeStageResult(False)]

    monkeypatch.setattr("infrastructure.orchestration.pipeline_runner.PipelineExecutor", _FailingExecutor)
    runner = PipelineRunner(repo_root=fake_repo, stream=io.StringIO())
    rc = runner.run(PipelineInvocation(project="template_code_project"))
    assert rc == 1


# --- Multi-project ---------------------------------------------------------


class _StubMulti:
    last_instance: "_StubMulti | None" = None

    def __init__(self, config: Any) -> None:
        self.config = config
        self.calls: list[str] = []
        type(self).last_instance = self

    def _ok(self):
        from infrastructure.core.pipeline.multi_project import MultiProjectResult
        from infrastructure.core.pipeline.types import PipelineStageResult

        names = [p.qualified_name for p in self.config.projects]
        stage = PipelineStageResult(1, "Copy Outputs", True, 0.0)
        project_results = {n: [stage] for n in names}
        return MultiProjectResult(
            project_results=project_results,
            successful_projects=len(names),
            failed_projects=0,
            total_duration=0.5,
            infra_test_duration=0.0,
        )

    def _one_failure(self):
        from infrastructure.core.pipeline.multi_project import MultiProjectResult
        from infrastructure.core.pipeline.types import PipelineStageResult

        names = [p.qualified_name for p in self.config.projects]
        ok = PipelineStageResult(1, "Environment Setup", True, 0.0)
        bad = PipelineStageResult(
            2,
            "Run Tests",
            False,
            0.1,
            exit_code=1,
            error_message="tests failed",
        )
        project_results: dict[str, list[Any]] = {}
        for i, n in enumerate(names):
            project_results[n] = [ok, bad] if i == 0 else [ok]
        successes = sum(1 for n in names if project_results[n] and all(s.success for s in project_results[n]))
        return MultiProjectResult(
            project_results=project_results,
            successful_projects=successes,
            failed_projects=len(names) - successes,
            total_duration=1.0,
        )

    def execute_all_projects_full(self):
        self.calls.append("full")
        return self._ok()

    def execute_all_projects_core(self):
        self.calls.append("core")
        return self._ok()

    def execute_all_projects_full_no_infra(self):
        self.calls.append("full_no_infra")
        return self._ok()

    def execute_all_projects_core_no_infra(self):
        self.calls.append("core_no_infra")
        return self._ok()


@pytest.fixture
def patched_multi_runner(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> PipelineRunner:
    monkeypatch.setattr("infrastructure.orchestration.pipeline_runner.MultiProjectOrchestrator", _StubMulti)
    return PipelineRunner(repo_root=fake_repo, stream=io.StringIO())


def test_run_multi_full(patched_multi_runner: PipelineRunner) -> None:
    rc = patched_multi_runner.run_multi(MultiProjectInvocation())
    assert rc == 0
    assert _StubMulti.last_instance.calls == ["full"]


def test_run_multi_core(patched_multi_runner: PipelineRunner) -> None:
    patched_multi_runner.run_multi(MultiProjectInvocation(skip_llm=True))
    assert _StubMulti.last_instance.calls == ["core"]


def test_run_multi_no_infra(patched_multi_runner: PipelineRunner) -> None:
    patched_multi_runner.run_multi(MultiProjectInvocation(skip_infra=True))
    assert _StubMulti.last_instance.calls == ["full_no_infra"]


def test_run_multi_core_no_infra(patched_multi_runner: PipelineRunner) -> None:
    patched_multi_runner.run_multi(MultiProjectInvocation(skip_infra=True, skip_llm=True))
    assert _StubMulti.last_instance.calls == ["core_no_infra"]


def test_run_multi_emits_succeeded_project_names(patched_multi_runner: PipelineRunner) -> None:
    patched_multi_runner.run_multi(MultiProjectInvocation(skip_infra=True, skip_llm=True))
    text = patched_multi_runner.stream.getvalue()
    assert "Succeeded:" in text
    assert "template_code_project" in text
    assert "some_rotating_project" in text


class _StubMultiOneFail(_StubMulti):
    def execute_all_projects_core_no_infra(self):
        self.calls.append("core_no_infra")
        return self._one_failure()


def test_run_multi_emits_failure_detail(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> None:
    monkeypatch.setattr(
        "infrastructure.orchestration.pipeline_runner.MultiProjectOrchestrator",
        _StubMultiOneFail,
    )
    runner = PipelineRunner(repo_root=fake_repo, stream=io.StringIO())
    rc = runner.run_multi(MultiProjectInvocation(skip_infra=True, skip_llm=True))
    assert rc == 1
    txt = runner.stream.getvalue()
    assert "Failed:" in txt
    assert "Run Tests" in txt
    assert "tests failed" in txt


def test_run_multi_no_projects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When no projects are discovered, run_multi must return non-zero."""
    (tmp_path / "projects").mkdir()
    runner = PipelineRunner(repo_root=tmp_path, stream=io.StringIO())
    rc = runner.run_multi(MultiProjectInvocation())
    assert rc == 1
