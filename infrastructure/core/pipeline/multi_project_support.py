"""Shared verification and aggregate completion for project orchestrators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.types import PipelineStageResult


if TYPE_CHECKING:
    from infrastructure.core.pipeline.multi_project_runtime import ProjectExecutionSpec


@dataclass(frozen=True)
class SharedInfrastructureResult:
    """Retain original shared child evidence beside its aggregate completion."""

    stage_results: tuple[PipelineStageResult, ...]
    run_result: RunResult

    def validated_run(self) -> RunResult | None:
        """Admit only matching canonical infrastructure-test rows and selection."""
        if (
            not isinstance(self.stage_results, tuple)
            or not isinstance(self.run_result, RunResult)
            or self.run_result.expected_stage_keys != ("infra_tests",)
        ):
            return None
        return validated_run_for_rows(list(self.stage_results), self.run_result)

    @property
    def exit_code(self) -> int:
        bound = self.validated_run()
        return bound.exit_code if bound is not None else 1


def run_shared_infrastructure(spec: ProjectExecutionSpec, *, deadline: float) -> SharedInfrastructureResult:
    """Execute the parent's canonical frozen infrastructure plan exactly once."""
    from infrastructure.core.pipeline.multi_project_runtime import execute_frozen_specs

    from infrastructure.core.pipeline.runtime_namespace import validate_shared_runtime

    if spec.config.shared_infrastructure is not True:
        raise ValueError("Shared execution requires its isolated canonical storage role")
    validate_shared_runtime(spec.config, spec.plan)
    rows, runs = execute_frozen_specs((spec,), workers=1, deadline=deadline)
    return SharedInfrastructureResult(tuple(rows[spec.plan.project]), runs[spec.plan.project])


def aggregate_project_exit_code(
    expected: tuple[str, ...],
    results: dict[str, RunResult],
    shared_exit_code: int = 0,
    *,
    project_results: dict[str, list[PipelineStageResult]],
    shared_result: SharedInfrastructureResult | None = None,
) -> int:
    """Require an exact project set and each project's explicit stage contract."""
    if type(shared_exit_code) is not int:
        return 1
    if shared_result is not None and (
        not isinstance(shared_result, SharedInfrastructureResult)
        or shared_result.validated_run() is None
        or shared_result.exit_code != shared_exit_code
    ):
        return 1
    if shared_exit_code != 0:
        return shared_exit_code if shared_exit_code in {130, 124, 75} else 1
    if not isinstance(project_results, dict) or not isinstance(results, dict):
        return 1
    codes: set[int] = set()
    coherent = set(project_results) == set(results)
    for name, result in results.items():
        rows = project_results.get(name)
        bound = validated_run_for_rows(rows, result)
        if bound is None:
            coherent = False
            codes.add(1)
            if (
                isinstance(result, RunResult)
                and isinstance(rows, list)
                and all(isinstance(row, PipelineStageResult) for row in rows)
            ):
                codes.add(RunResult.from_results(rows, result.expected_stage_keys).exit_code)
        else:
            codes.add(bound.exit_code)
    for code in (130, 124, 1, 75):
        if code in codes:
            return code
    if not expected or len(expected) != len(set(expected)) or set(results) != set(expected):
        return 1
    return 0 if coherent and all(result.complete for result in results.values()) else 1


def validated_run_for_rows(rows: object, run: RunResult | None) -> RunResult | None:
    """Bind a public aggregate claim to its canonical stage rows and selection."""
    if not isinstance(run, RunResult) or not isinstance(rows, list):
        return None
    if any(not isinstance(row, PipelineStageResult) for row in rows):
        return None
    for row in rows:
        if row.outcome is not None and (row.stage_key != row.outcome.stage_key or row.success != row.outcome.complete):
            return None
    return run if RunResult.from_results(rows, run.expected_stage_keys) == run else None
