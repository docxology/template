"""Admit the canonical isolated storage role before shared execution begins."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.plan import ExecutionPlan, PlannedStage
from infrastructure.core.pipeline.plan_custody import FrozenPlanSources
from infrastructure.core.pipeline.target_contracts import effective_stage_declaration
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult, StagePolicy


class SharedRuntimeCustodyError(ValueError):
    """A frozen shared plan lost Source/environment custody, not invocation syntax."""

    def as_stage_result(self) -> PipelineStageResult:
        """Retain this original refusal as a typed row without revalidation."""
        diagnostic = str(self)
        return PipelineStageResult(
            0,
            "Execution contract",
            False,
            0.0,
            75,
            diagnostic,
            stage_completed=False,
            stage_key="execution",
            outcome=StageOutcome("execution", StageStatus.BLOCKED, child_exit_code=None, diagnostic=diagnostic),
        )


def validate_shared_runtime(config: PipelineConfig, plan: ExecutionPlan) -> None:
    """A storage role cannot redirect arbitrary project approval or resume state."""
    if type(config.shared_infrastructure) is not bool:
        raise ValueError("Runtime storage role must be an exact boolean")
    if not config.shared_infrastructure:
        return
    if (
        config.clean is not False
        or config.resume is not False
        or config.skip_infra is not False
        or config.mode != "core"
        or config.pipeline_path != config.repo_root / "infrastructure/core/pipeline/pipeline.yaml"
        or plan.project != config.project_name
        or plan.mode != "core"
        or plan.expected_stage_keys != ("infra_tests",)
        or plan.provenance != "infrastructure/core/pipeline/pipeline.yaml"
    ):
        raise ValueError("Shared runtime storage requires the fresh canonical infrastructure-only plan")
    # Evaluate confinement before an executor creates logs or other run files.
    config.runtime_output_dir
    # Validate the original contract against held, source-bound declarations;
    # never compile or substitute a new execution plan inside a worker.
    sources = FrozenPlanSources.capture(config)
    if sources.source_identity != plan.source_identity or sources.environment_identity != plan.environment_identity:
        expected = plan.source_identity
        expected_label = (
            expected
            if isinstance(expected, str)
            and len(expected) == 64
            and all(char in "0123456789abcdef" for char in expected)
            else "<invalid-sha256>"
        )
        diagnostic = {
            "expected_total": expected_label,
            "observed_total": sources.source_identity,
            "components": dict(sources.source_components),
        }
        reason = (
            "Consumed source changed after plan resolution; start a fresh run"
            if sources.source_identity != plan.source_identity
            else "Effective child environment changed after plan resolution; start a fresh run"
        )
        raise SharedRuntimeCustodyError(
            reason + "; fingerprint_diagnostics=" + json.dumps(diagnostic, sort_keys=True, separators=(",", ":"))
        )
    declarations = tuple(effective_stage_declaration(stage) for stage in sources.dag().sorted_stages())
    if canonical_digest([asdict(stage) for stage in declarations]) != plan.definition_identity:
        raise ValueError("Shared plan definition differs from the admitted canonical declarations")
    selected = [(ordinal, stage) for ordinal, stage in enumerate(declarations, 1) if stage.key == "infra_tests"]
    if len(selected) != 1:
        raise ValueError("Canonical declaration must contain exactly one infrastructure gate")
    ordinal, stage = selected[0]
    control = sources.control()
    arguments = tuple(stage.args)
    if stage.script and "--project" not in arguments:
        arguments += ("--project", config.project_name)
    policy = control.stage_policies.get(ordinal, StagePolicy())
    if control.hitl_mode == "custom" and ordinal in control.custom_gate_stages:
        policy = replace(policy, pause_after=True)
    identities = {declaration.name: declaration.key for declaration in declarations}
    expected = PlannedStage(
        "infra_tests",
        stage.name,
        Path(stage.script.replace("{project}", config.project_name)).as_posix() if stage.script else None,
        stage.method,
        arguments,
        tuple(str(identities[name]) for name in stage.depends_on),
        tuple(stage.tags),
        stage.contract,
        stage.hooks,
        policy,
        stage.allow_skip,
    )
    if (
        plan.stages != (expected,)
        or plan.hitl_mode != control.hitl_mode
        or plan.smart_pause_action != control.smart_pause_action
    ):
        raise ValueError("Shared plan target or policy differs from its canonical source declaration")
    sources.verify(config)
