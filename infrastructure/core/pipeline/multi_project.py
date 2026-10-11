"""Multi-project orchestration system.

This module provides orchestration for running pipelines across multiple projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.multi_project_support import (
    aggregate_project_exit_code,
    run_shared_infrastructure,
    SharedInfrastructureResult,
    validated_run_for_rows,
)

if TYPE_CHECKING:
    from infrastructure.project.project_info import ProjectInfo
    from infrastructure.core.pipeline.multi_project_runtime import ProjectExecutionSpec

logger = get_logger(__name__)


@dataclass
class MultiProjectConfig:
    """Configuration for multi-project execution."""

    repo_root: Path
    projects: list[ProjectInfo]
    run_infra_tests: bool = True
    mode: str = "core"
    resume: bool = False
    run_timeout_seconds: float = 14400.0
    deadline_monotonic: float | None = None


@dataclass
class MultiProjectResult:
    """Result of multi-project execution."""

    project_results: dict[str, list[PipelineStageResult]]
    infra_test_duration: float = 0.0
    total_duration: float = 0.0
    successful_projects: int = 0
    failed_projects: int = 0
    expected_projects: tuple[str, ...] = ()
    run_results: dict[str, RunResult] = field(default_factory=dict)
    shared_infrastructure_exit_code: int = 0
    shared_infrastructure_result: SharedInfrastructureResult | None = None

    @property
    def exit_code(self) -> int:
        return aggregate_project_exit_code(
            self.expected_projects,
            self.run_results,
            self.shared_infrastructure_exit_code,
            project_results=self.project_results,
            shared_result=self.shared_infrastructure_result,
        )


def validated_project_run(result: MultiProjectResult, name: str) -> RunResult | None:
    """Only matching typed outcomes and their original expected selection grant completion."""
    if not isinstance(result.project_results, dict):
        return None
    return validated_run_for_rows(result.project_results.get(name), result.run_results.get(name))


def format_multi_project_outcome_lines(
    ordered_projects: Sequence[ProjectInfo],
    result: MultiProjectResult,
    *,
    hint_max_chars: int = 160,
) -> list[str]:
    """Human-readable lines naming succeeded vs failed projects (serial multi-project UX).

    ``ordered_projects`` must match discovery order and use ``qualified_name`` keys
    consistent with :class:`MultiProjectOrchestrator`.

    Args:
        ordered_projects: Projects in run order (same list passed to orchestrator config).
        result: Aggregate result from ``execute_all_projects``.
        hint_max_chars: Truncate first failing stage ``error_message`` to this length.
    """
    lines: list[str] = []
    n = len(ordered_projects)
    if n == 0:
        return lines

    pr = result.project_results
    infra_aborted = len(pr) == 0 and result.successful_projects == 0 and result.failed_projects == n
    if infra_aborted:
        lines.append(
            "Infrastructure tests failed — no project pipelines were run.",
        )
        return lines

    succeeded: list[str] = []
    failed: list[str] = []

    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn)
        if stages is None:
            failed.append(f"{qn}: no pipeline results recorded")
            continue
        if not stages:
            failed.append(f"{qn}: pipeline failed before stage results were recorded")
            continue
        run = validated_project_run(result, qn)
        if run is not None and run.complete:
            succeeded.append(qn)
        else:
            first_bad = next((s for s in stages if not s.success), None)
            if first_bad is None:
                failed.append(f"{qn}: unknown stage failure")
                continue
            msg = (first_bad.error_message or "").strip()
            if len(msg) > hint_max_chars:
                msg = msg[: hint_max_chars - 1] + "…"
            if msg:
                failed.append(f"{qn}: {first_bad.stage_name} — {msg}")
            else:
                failed.append(f"{qn}: {first_bad.stage_name}")

    if succeeded:
        lines.append("Succeeded:")
        lines.extend(f"  - {name}" for name in succeeded)
    if failed:
        lines.append("Failed:")
        lines.extend(f"  - {entry}" for entry in failed)
    return lines


class MultiProjectOrchestrator:
    """Orchestrate pipeline execution across multiple projects."""

    def __init__(self, config: MultiProjectConfig) -> None:
        self.config = config

    def execute_all_projects(self) -> MultiProjectResult:
        """Freeze all plans once, then execute that exact prepared contract."""
        from infrastructure.core.pipeline.multi_project_runtime import (
            freeze_project_plans,
            freeze_shared_plan,
            validate_budget,
        )
        from infrastructure.core.pipeline.execution_session import compose_run_deadline

        started = time.monotonic()
        validate_budget(self.config.run_timeout_seconds)
        if self.config.mode not in {"core", "live"} or any(
            type(getattr(self.config, name)) is not bool for name in ("run_infra_tests", "resume")
        ):
            raise ValueError("Prepared invocation requires the canonical mode and exact boolean policy")
        deadline = compose_run_deadline(self.config.run_timeout_seconds, self.config.deadline_monotonic)
        specs = freeze_project_plans(
            self.config.projects,
            self.config.repo_root,
            mode=self.config.mode,
            resume=self.config.resume,
            timeout=self.config.run_timeout_seconds,
        )
        shared = freeze_shared_plan(specs) if self.config.run_infra_tests and specs else None
        result = self.execute_prepared_projects(specs, shared, deadline_monotonic=deadline)
        result.total_duration = time.monotonic() - started
        return result

    def _admit_prepared_spec(self, spec: ProjectExecutionSpec, expected: PipelineConfig) -> ProjectExecutionSpec:
        """Bind typed transported identities without consulting a new definition."""
        from infrastructure.core.pipeline.multi_project_runtime import ProjectExecutionSpec
        from infrastructure.core.pipeline.plan import ExecutionPlan

        if not isinstance(spec, ProjectExecutionSpec) or not isinstance(spec.config, PipelineConfig):
            raise ValueError("Prepared projects require typed execution specifications")
        if spec.config != expected or any(
            type(getattr(spec.config, name)) is not bool for name in ("clean", "skip_infra", "resume")
        ):
            raise ValueError("Prepared project configuration differs from the selected invocation")
        plan = spec.plan
        if not isinstance(plan, ExecutionPlan):
            raise ValueError("Prepared projects require typed execution plans")
        admitted_plan = ExecutionPlan.from_dict(plan.to_dict(), expected_digest=plan.digest)
        if (
            plan.project != expected.project_name
            or plan.mode != expected.mode
            or plan.run_timeout_seconds != expected.run_timeout_seconds
        ):
            raise ValueError("Prepared plan identity differs from the selected invocation")
        # Config is mutable: retain a privately constructed canonical copy so a
        # caller cannot change the admitted transport while a worker is queued.
        return ProjectExecutionSpec(expected, admitted_plan)

    def execute_prepared_projects(
        self,
        specs: tuple[ProjectExecutionSpec, ...],
        shared: ProjectExecutionSpec | None,
        *,
        deadline_monotonic: float | None = None,
    ) -> MultiProjectResult:
        """Validate and supervise the original plans; never recompile after preflight.

        The existing worker source guards refuse mutations after preparation,
        and the original supervising deadline includes caller preflight time.
        """
        from infrastructure.core.pipeline.execution_session import compose_run_deadline
        from infrastructure.core.pipeline.multi_project_runtime import (
            execute_frozen_specs,
            selected_project_config,
            selected_shared_config,
            validate_budget,
        )

        started = time.monotonic()
        validate_budget(self.config.run_timeout_seconds)
        if self.config.mode not in {"core", "live"} or any(
            type(getattr(self.config, name)) is not bool for name in ("run_infra_tests", "resume")
        ):
            raise ValueError("Prepared invocation requires the canonical mode and exact boolean policy")
        deadline = compose_run_deadline(self.config.run_timeout_seconds, self.config.deadline_monotonic)
        if deadline_monotonic is not None:
            deadline = min(deadline, compose_run_deadline(self.config.run_timeout_seconds, deadline_monotonic))
        if not isinstance(specs, tuple) or len(specs) != len(self.config.projects):
            raise ValueError("Prepared project selection differs from the selected invocation")
        admitted = []
        for project, spec in zip(tuple(self.config.projects), specs, strict=True):
            expected_config = selected_project_config(
                project,
                self.config.repo_root,
                mode=self.config.mode,
                resume=self.config.resume,
                timeout=self.config.run_timeout_seconds,
            )
            spec = self._admit_prepared_spec(spec, expected_config)
            from infrastructure.core.pipeline.target_contracts import canonical_target_contract

            if any(
                stage.key == "infra_tests"
                or canonical_target_contract(stage.script, stage.method, stage.arguments).infrastructure_tests
                for stage in spec.plan.stages
            ):
                raise ValueError("Prepared project plans must leave shared infrastructure to the once-only gate")
            admitted.append(spec)
        specs = tuple(admitted)
        expected = tuple(spec.plan.project for spec in specs)
        if len(expected) != len(set(expected)):
            raise ValueError("Duplicate prepared project identities")
        if self.config.run_infra_tests and specs:
            if shared is None:
                raise ValueError("Prepared invocation is missing its shared infrastructure plan")
            shared = self._admit_prepared_spec(shared, selected_shared_config(specs))
            if (
                shared.plan.expected_stage_keys != ("infra_tests",)
                or shared.plan.provenance != "infrastructure/core/pipeline/pipeline.yaml"
                or not canonical_target_contract(
                    shared.plan.stages[0].script, shared.plan.stages[0].method, shared.plan.stages[0].arguments
                ).infrastructure_tests
            ):
                raise ValueError("Prepared shared infrastructure policy differs from the canonical gate")
        elif shared is not None:
            raise ValueError("Prepared invocation includes an unselected shared infrastructure gate")
        shared_started = time.monotonic()
        shared_result = run_shared_infrastructure(shared, deadline=deadline) if shared is not None else None
        shared_exit = shared_result.exit_code if shared_result is not None else 0
        infra_duration = time.monotonic() - shared_started if shared is not None else 0.0
        if shared_exit:
            return MultiProjectResult(
                {}, infra_duration, time.monotonic() - started, 0, len(specs), expected, {}, shared_exit, shared_result
            )
        rows, runs = execute_frozen_specs(specs, workers=1, deadline=deadline)
        succeeded = sum(run.complete for run in runs.values())
        return MultiProjectResult(
            rows,
            infra_duration,
            time.monotonic() - started,
            succeeded,
            len(specs) - succeeded,
            expected,
            runs,
            shared_infrastructure_result=shared_result,
        )
