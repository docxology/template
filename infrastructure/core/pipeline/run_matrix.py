"""Reproducible project × stage run matrix.

A ``run.config`` (YAML) file declares an explicit, reproducible subset of the
pipeline to run: which stages to execute for which projects. It is the
deterministic, version-controllable alternative to the interactive menu —
ideal for "render exactly these 3 working papers through exactly these stages"
runs that must reproduce byte-for-byte.

The parser validates stable keys and configuration types. Resolution compiles
an immutable execution plan from each project's effective DAG, including
plugins, in declared dependency order. Execution uses the canonical executor's
locking, source custody, checkpoint, deadline, and outcome contracts. A matrix
completes only when every expected project/stage pair completes in order.
Explicit infrastructure verification is a once-only shared gate; its failure
prevents every project stage. Project-only selections remain targeted.

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

from dataclasses import dataclass, field, replace
from pathlib import Path
import re
from typing import Any

import yaml

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import ExecutionPlan, PlannedStage, compile_execution_plan
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.execution_session import compose_run_deadline
from infrastructure.core.pipeline.multi_project_runtime import ProjectExecutionSpec, freeze_shared_plan, validate_budget
from infrastructure.core.pipeline.multi_project_support import SharedInfrastructureResult, run_shared_infrastructure
from infrastructure.core.pipeline.target_contracts import canonical_target_contract
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.orchestration.discovery import validate_project_slug

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
    mode: str = "core"
    resume: bool = False
    run_timeout_seconds: float = 14400.0


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
    outcome: StageOutcome | None = None
    run_result: RunResult | None = None
    shared_result: SharedInfrastructureResult | None = None

    @property
    def ok(self) -> bool:
        """Return True if the result is successful."""
        return (
            self.returncode == 0
            and (self.outcome.complete if self.outcome is not None else not self.skipped)
            and (self.run_result.complete if self.run_result is not None else True)
            and (self.shared_result.exit_code == 0 if self.shared_result is not None else True)
        )


@dataclass
class RunPlan:
    """A resolved, ordered plan plus any non-fatal resolution warnings."""

    steps: tuple[RunStep, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    execution_plans: tuple[ExecutionPlan, ...] = ()
    shared_infrastructure: ProjectExecutionSpec | None = None
    resume: bool = False
    run_timeout_seconds: float = 14400.0
    deadline_monotonic: float | None = None


def _normalize_stage_list(raw: Any, *, where: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RunConfigError(f"{where}: 'stages' must be a list, got {type(raw).__name__}")
    stages: list[str] = []
    for item in raw:
        if not isinstance(item, str) or re.fullmatch(r"[a-z][a-z0-9_-]*", item) is None:
            raise RunConfigError(f"{where}: each stage must be a stable lowercase key, got {item!r}")
        if item in stages:
            raise RunConfigError(f"{where}: duplicate stage key {item!r}")
        stages.append(item)
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

    if type(data.get("version", 1)) is not int or data.get("version", 1) != 1:
        raise RunConfigError("run.config version must be 1")
    unknown = set(data) - {"version", "mode", "resume", "run_timeout_seconds", "defaults", "runs"}
    if unknown:
        raise RunConfigError(f"unsupported run.config fields: {sorted(map(str, unknown))}")
    mode = data.get("mode", "core")
    if not isinstance(mode, str) or mode not in {"core", "live"}:
        raise RunConfigError("run.config mode must be core or live")
    resume = data.get("resume", False)
    if type(resume) is not bool:
        raise RunConfigError("run.config resume must be a boolean")
    timeout = data.get("run_timeout_seconds", 14400.0)
    try:
        validate_budget(timeout)
    except ValueError as exc:
        raise RunConfigError(str(exc)) from exc
    defaults = data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RunConfigError("run.config 'defaults' must be a mapping")
    if set(defaults) - {"stages"}:
        raise RunConfigError("run.config 'defaults' supports only stages")
    default_stages = _normalize_stage_list(defaults.get("stages"), where="defaults")

    raw_runs = data.get("runs")
    if not isinstance(raw_runs, list) or not raw_runs:
        raise RunConfigError("run.config must declare a non-empty 'runs' list")

    runs: list[RunEntry] = []
    for i, entry in enumerate(raw_runs):
        where = f"runs[{i}]"
        if not isinstance(entry, dict):
            raise RunConfigError(f"{where}: each run must be a mapping")
        if set(entry) - {"project", "stages"}:
            raise RunConfigError(f"{where}: unsupported run fields")
        project = entry.get("project")
        if not isinstance(project, str) or not project.strip():
            raise RunConfigError(f"{where}: 'project' must be a non-empty string")
        stages = _normalize_stage_list(entry.get("stages"), where=where)
        runs.append(RunEntry(project=project.strip(), stages=stages))

    return RunConfig(tuple(default_stages), tuple(runs), mode, resume, timeout)


def _shared_definition(stage: PlannedStage, project: str) -> PlannedStage:
    """Compare actual shared declarations while excluding their project binding."""
    args = list(stage.arguments)
    if "--project" in args:
        index = args.index("--project")
        if args[index + 1 : index + 2] != [project]:
            raise RunConfigError("Infrastructure project argument differs from its resolved scope")
        del args[index : index + 2]
    return replace(stage, arguments=tuple(args))


def resolve_run_plan(config: RunConfig, repo_root: Path) -> RunPlan:
    """Compile each project's explicit selection from its effective DAG once."""
    steps: list[RunStep] = []
    plans: list[ExecutionPlan] = []
    specifications: list[ProjectExecutionSpec] = []
    shared_stages: list[tuple[PlannedStage, str]] = []
    try:
        validate_budget(config.run_timeout_seconds)
    except ValueError as exc:
        raise RunConfigError(str(exc)) from exc
    if type(config.resume) is not bool:
        raise RunConfigError("run.config resume must be a boolean")
    deadline = compose_run_deadline(config.run_timeout_seconds, None)
    seen_projects: set[str] = set()
    for entry in config.runs:
        try:
            project = validate_project_slug(entry.project, repo_root)
            if project in seen_projects:
                raise ValueError(f"Duplicate project run: {project}")
            seen_projects.add(project)
            stages = entry.stages or config.default_stages
            if not stages:
                raise ValueError("no stages and no 'defaults.stages' fallback")
            execution_config = PipelineConfig(
                project,
                repo_root,
                mode=config.mode,
                clean=False,
                resume=config.resume,
                run_timeout_seconds=config.run_timeout_seconds,
            )
            plan = compile_execution_plan(
                execution_config,
                skip_clean=True,
                target_stages=stages,
            )
        except ValueError as exc:
            raise RunConfigError(f"run.config run for {entry.project!r}: {exc}") from exc
        specifications.append(ProjectExecutionSpec(execution_config, plan))
        shared = tuple(
            stage
            for stage in plan.stages
            if stage.key == "infra_tests"
            or canonical_target_contract(stage.script, stage.method, stage.arguments).infrastructure_tests
        )
        shared_stages.extend((stage, project) for stage in shared)
        selected = replace(plan, stages=tuple(stage for stage in plan.stages if stage not in shared))
        if selected.stages:
            plans.append(selected)
            steps.extend(RunStep(project, stage.key) for stage in selected.stages)
    shared_spec = None
    if shared_stages:
        try:
            shared_spec = freeze_shared_plan(tuple(specifications))
            canonical = _shared_definition(shared_spec.plan.stages[0], shared_spec.plan.project)
            if any(_shared_definition(stage, project) != canonical for stage, project in shared_stages):
                raise ValueError("Selected infrastructure declarations differ from the canonical once-only gate")
        except ValueError as exc:
            raise RunConfigError(str(exc)) from exc
        steps.insert(0, RunStep("root", "infra_tests"))
    return RunPlan(
        tuple(steps),
        execution_plans=tuple(plans),
        shared_infrastructure=shared_spec,
        resume=config.resume,
        run_timeout_seconds=config.run_timeout_seconds,
        deadline_monotonic=deadline,
    )


def _project_steps(selection: ExecutionPlan, run: RunResult | None, missing_status: StageStatus) -> list[StepResult]:
    """Retain selected child evidence and the entire project completion contract.

    The final selected row carries the aggregate result, including nonselected
    custody/reporting guards. A succeeded child cannot conceal a failed run.
    """
    actual = {outcome.stage_key: outcome for outcome in run.outcomes} if run is not None else {}
    results: list[StepResult] = []
    for index, stage in enumerate(selection.stages):
        outcome = actual.get(stage.key)
        if outcome is None:
            outcome = StageOutcome(
                stage.key, missing_status, None, reason="No stage execution after an earlier incomplete stage"
            )
        aggregate = run if index == len(selection.stages) - 1 else None
        code = aggregate.exit_code if aggregate is not None else RunResult((stage.key,), (outcome,)).exit_code
        results.append(
            StepResult(
                selection.project,
                stage.key,
                code,
                skipped=outcome.status is StageStatus.ABORTED,
                outcome=outcome,
                run_result=aggregate,
            )
        )
    return results


def execute_run_plan(
    plan: RunPlan, repo_root: Path, *, fail_fast: bool = False, resume: bool | None = None
) -> list[StepResult]:
    """Run fresh shared verification once, then exact project selections/resume."""
    if not plan.execution_plans and plan.shared_infrastructure is None:
        raise RunConfigError("Execution requires resolved immutable project plans")
    selected_resume = plan.resume if resume is None else resume
    if type(selected_resume) is not bool or type(fail_fast) is not bool:
        raise RunConfigError("Matrix resume/fail_fast policy must be exact booleans")
    validate_budget(plan.run_timeout_seconds)
    budget = min((plan.run_timeout_seconds, *(item.run_timeout_seconds for item in plan.execution_plans)))
    deadline = compose_run_deadline(budget, plan.deadline_monotonic)
    results: list[StepResult] = []
    aborted = False
    pending_status = StageStatus.ABORTED
    if plan.shared_infrastructure is not None:
        shared = run_shared_infrastructure(plan.shared_infrastructure, deadline=deadline)
        shared_rows = _project_steps(plan.shared_infrastructure.plan, shared.run_result, StageStatus.ABORTED)
        for row in shared_rows:
            row.project, row.shared_result = "root", shared
        results.extend(shared_rows)
        aborted = shared.exit_code != 0
        if shared.exit_code == 75:
            pending_status = StageStatus.BLOCKED
    for selection in plan.execution_plans:
        run: RunResult | None = None
        missing_status = pending_status
        if not aborted:
            executor = PipelineExecutor(
                PipelineConfig(
                    selection.project,
                    repo_root,
                    mode=selection.mode,
                    clean=False,
                    skip_infra=True,
                    resume=selected_resume,
                    run_timeout_seconds=selection.run_timeout_seconds,
                )
            )
            stage_results = executor.execute_plan(selection, deadline_monotonic=deadline)
            run = executor.run_result(stage_results)
            if run.exit_code == 75:
                missing_status = StageStatus.BLOCKED
            if run.exit_code != 0 and fail_fast:
                aborted = True
                pending_status = missing_status
        results.extend(_project_steps(selection, run, missing_status))
    return results


def run_plan_exit_code(plan: RunPlan, results: list[StepResult]) -> int:
    """Require every planned project/stage pair in its declared order."""
    for code in (130, 124, 1, 75):
        if any(result.returncode == code for result in results):
            return code
    if not plan.steps or [(result.project, result.stage) for result in results] != [
        (step.project, step.stage) for step in plan.steps
    ]:
        return 1
    return 0 if all(result.ok for result in results) else 1


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
        failure = (
            next(
                (
                    outcome
                    for outcome in r.run_result.outcomes
                    if not outcome.complete and RunResult((outcome.stage_key,), (outcome,)).exit_code == r.returncode
                ),
                None,
            )
            if r.run_result is not None and not r.run_result.complete
            else None
        )
        status = (
            failure.status.value.upper()
            if failure is not None
            else "INCOMPLETE"
            if r.run_result is not None and not r.run_result.complete
            else r.outcome.status.value.upper()
            if r.outcome is not None
            else "ABORTED"
            if r.skipped
            else "ok"
            if r.ok
            else f"FAIL({r.returncode})"
        )
        lines.append(f"  {f'{r.project} · {r.stage}':<{width}}  {status}")
        if failure is not None and failure.stage_key != r.stage:
            lines.append(f"    {failure.stage_key}: {failure.diagnostic or failure.reason}")
    failed = [r for r in results if not r.skipped and r.returncode not in {0, 75}]
    skipped = [r for r in results if r.skipped]
    pending = [r for r in results if r.returncode == 75]
    lines.append(
        f"Summary: {len(results) - len(failed) - len(skipped) - len(pending)} complete, "
        f"{len(failed)} failed, {len(skipped)} aborted, {len(pending)} pending of {len(results)} steps."
    )
    return "\n".join(lines)
