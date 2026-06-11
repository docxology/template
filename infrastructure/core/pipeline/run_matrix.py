"""Reproducible project × stage run matrix.

A ``run.config`` (YAML) file declares an explicit, reproducible subset of the
pipeline to run: which stages to execute for which projects. It is the
deterministic, version-controllable alternative to the interactive menu —
ideal for "render exactly these 3 working papers through exactly these stages"
runs that must reproduce byte-for-byte.

Design (modular / composable):

- :func:`parse_run_config` — pure: YAML text → :class:`RunConfig` (no I/O, no
  resolution). Raises :class:`RunConfigError` on a malformed document.
- :func:`resolve_run_plan` — resolves each project against the discovered
  project set (via ``validate_project_slug``, so path-traversal is rejected),
  expands per-run stage lists (falling back to ``defaults.stages``), validates
  every stage against the canonical vocabulary, and orders the steps
  **canonically** (analysis before render, etc.) regardless of listing order —
  this is what makes a given ``run.config`` reproducible.
- :func:`execute_run_plan` — runs each step through an injected ``runner``
  (defaults to ``execute_single_stage``); returns a list of
  :class:`StepResult`. The ``runner`` seam keeps this unit-testable with a real
  recording callable (dependency injection, not mocking).
- :func:`format_report` — renders the deterministic result matrix.

Example ``run.config``::

    version: 1
    defaults:
      stages: [setup, project_tests, analysis, render_pdf, validate, copy]
    runs:
      - project: templates/template_code_project
        stages: [analysis, render_pdf, validate]   # overrides defaults
      - project: working/my_paper                   # uses defaults
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.core.pipeline.stage_registry import STAGE_DISPATCH, known_stage_keys, normalize_stage_key
from infrastructure.orchestration.discovery import validate_project_slug

# Canonical execution order = the STAGE_DISPATCH declaration order (setup →
# tests → analysis → render → validate → copy → llm → executive_report). Steps
# are sorted by this index so a run.config's stage *listing* order never changes
# what actually runs.
STAGE_ORDER: tuple[str, ...] = tuple(STAGE_DISPATCH.keys())
_STAGE_INDEX: dict[str, int] = {name: i for i, name in enumerate(STAGE_ORDER)}

DEFAULT_CONFIG_NAMES: tuple[str, ...] = ("run.config", "run.config.yaml", "run.config.yml")


class RunConfigError(ValueError):
    """Raised when a ``run.config`` document is malformed."""


@dataclass(frozen=True)
class RunEntry:
    """One project's requested stages (stages already normalized, not yet ordered)."""

    project: str
    stages: tuple[str, ...]


@dataclass(frozen=True)
class RunConfig:
    """Parsed (but unresolved) ``run.config`` document."""

    default_stages: tuple[str, ...]
    runs: tuple[RunEntry, ...]


@dataclass(frozen=True)
class RunStep:
    """A single resolved (project, stage) unit of work, in execution order."""

    project: str
    stage: str


@dataclass
class StepResult:
    """Outcome of one executed :class:`RunStep`."""

    project: str
    stage: str
    returncode: int
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return self.skipped or self.returncode == 0


@dataclass
class RunPlan:
    """A resolved, ordered plan plus any non-fatal resolution warnings."""

    steps: tuple[RunStep, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _normalize_stage_list(raw: Any, *, where: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RunConfigError(f"{where}: 'stages' must be a list, got {type(raw).__name__}")
    stages: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise RunConfigError(f"{where}: each stage must be a non-empty string, got {item!r}")
        stages.append(normalize_stage_key(item))
    return tuple(stages)


def parse_run_config(text: str) -> RunConfig:
    """Parse ``run.config`` YAML text into a :class:`RunConfig`. Pure, no I/O."""
    try:
        data: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RunConfigError(f"run.config is not valid YAML: {exc}") from exc
    if data is None:
        raise RunConfigError("run.config is empty")
    if not isinstance(data, dict):
        raise RunConfigError(f"run.config must be a mapping at the top level, got {type(data).__name__}")

    defaults = data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RunConfigError("run.config 'defaults' must be a mapping")
    default_stages = _normalize_stage_list(defaults.get("stages"), where="defaults")

    raw_runs = data.get("runs")
    if not isinstance(raw_runs, list) or not raw_runs:
        raise RunConfigError("run.config must declare a non-empty 'runs' list")

    runs: list[RunEntry] = []
    for i, entry in enumerate(raw_runs):
        where = f"runs[{i}]"
        if not isinstance(entry, dict):
            raise RunConfigError(f"{where}: each run must be a mapping")
        project = entry.get("project")
        if not isinstance(project, str) or not project.strip():
            raise RunConfigError(f"{where}: 'project' must be a non-empty string")
        stages = _normalize_stage_list(entry.get("stages"), where=where)
        runs.append(RunEntry(project=project.strip(), stages=stages))

    return RunConfig(default_stages=default_stages, runs=tuple(runs))


def _order_stages(stages: tuple[str, ...]) -> tuple[str, ...]:
    """De-duplicate and sort stages into canonical pipeline order."""
    unique = list(dict.fromkeys(stages))  # preserve-then-dedupe
    return tuple(sorted(unique, key=lambda s: _STAGE_INDEX[s]))


def resolve_run_plan(config: RunConfig, repo_root: Path) -> RunPlan:
    """Resolve projects + stages into an ordered, validated :class:`RunPlan`.

    Raises :class:`RunConfigError` if a project can't be resolved or a stage is
    not in the canonical vocabulary — fail-fast before any subprocess runs.
    """
    valid = known_stage_keys()
    steps: list[RunStep] = []
    warnings: list[str] = []

    for entry in config.runs:
        try:
            resolved_project = validate_project_slug(entry.project, repo_root)
        except ValueError as exc:
            raise RunConfigError(f"run.config run for {entry.project!r}: {exc}") from exc

        stages = entry.stages or config.default_stages
        if not stages:
            raise RunConfigError(
                f"run.config run for {entry.project!r} has no stages and no 'defaults.stages' fallback"
            )
        unknown = [s for s in stages if s not in valid]
        if unknown:
            raise RunConfigError(
                f"run.config run for {entry.project!r}: unknown stage(s) {', '.join(unknown)}; "
                f"valid: {', '.join(sorted(valid))}"
            )
        for stage in _order_stages(stages):
            steps.append(RunStep(project=resolved_project, stage=stage))

    return RunPlan(steps=tuple(steps), warnings=tuple(warnings))


def execute_run_plan(
    plan: RunPlan,
    repo_root: Path,
    *,
    fail_fast: bool = False,
    runner: Callable[[str, str, Path], int] = execute_single_stage,
) -> list[StepResult]:
    """Execute each step via ``runner`` (default ``execute_single_stage``).

    ``runner`` is injected for testability (a real recording callable — no mock
    framework). With ``fail_fast`` the first non-zero return marks all remaining
    steps skipped and stops; otherwise every step runs and failures accumulate.
    """
    results: list[StepResult] = []
    aborted = False
    for step in plan.steps:
        if aborted:
            results.append(StepResult(project=step.project, stage=step.stage, returncode=0, skipped=True))
            continue
        rc = runner(step.stage, step.project, repo_root)
        results.append(StepResult(project=step.project, stage=step.stage, returncode=rc))
        if rc != 0 and fail_fast:
            aborted = True
    return results


def find_run_config(repo_root: Path) -> Path | None:
    """Return the first existing default ``run.config`` file under *repo_root*."""
    for name in DEFAULT_CONFIG_NAMES:
        candidate = repo_root / name
        if candidate.is_file():
            return candidate
    return None


def format_report(results: list[StepResult]) -> str:
    """Render a deterministic per-step result table."""
    if not results:
        return "run.config: no steps to run."
    width = max(len(f"{r.project} · {r.stage}") for r in results)
    lines = ["run.config results:"]
    for r in results:
        status = "SKIP" if r.skipped else ("ok" if r.returncode == 0 else f"FAIL({r.returncode})")
        lines.append(f"  {f'{r.project} · {r.stage}':<{width}}  {status}")
    failed = [r for r in results if not r.skipped and r.returncode != 0]
    skipped = [r for r in results if r.skipped]
    lines.append(
        f"Summary: {len(results) - len(failed) - len(skipped)} ok, "
        f"{len(failed)} failed, {len(skipped)} skipped of {len(results)} steps."
    )
    return "\n".join(lines)
