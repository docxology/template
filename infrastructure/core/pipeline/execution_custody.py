"""Revalidate the frozen execution identity at launch, reuse, and completion."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from infrastructure.core.pipeline.execution_environment import effective_environment_identity
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint_components
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.core.pipeline.plan import ExecutionPlan


def execution_guard_result(
    *,
    config: PipelineConfig,
    plan: ExecutionPlan | None,
    deadline: float,
    stage_num: int = 0,
    stage_name: str = "Execution contract",
    stage_key: str = "execution",
    completion: bool = False,
) -> PipelineStageResult | None:
    """Return a blocking result when custody or the finite run budget changed.

    A completed checkpoint prefix receives the same checks as a child launch.
    Identity failures refuse reuse without deleting the previous checkpoint.
    Environment values are never included in diagnostics.
    """
    source_changed = False
    environment_changed = False
    identity_error = ""
    fingerprint_diagnostics: dict[str, object] | None = None
    if plan is not None:
        try:
            components = source_fingerprint_components(
                config.repo_root, config.project_dir, definition_path=config.repo_root / plan.provenance
            )
            observed_total = canonical_digest(components)
            source_changed = observed_total != plan.source_identity
            if source_changed:
                expected_total = plan.source_identity
                expected_label = (
                    expected_total
                    if isinstance(expected_total, str)
                    and len(expected_total) == 64
                    and all(char in "0123456789abcdef" for char in expected_total)
                    else "<invalid-sha256>"
                )
                fingerprint_diagnostics = {
                    "expected_total": expected_label,
                    "observed_total": observed_total,
                    "components": {key: canonical_digest(components[key]) for key in ("source", "python", "tools")},
                }
            environment_changed = (
                effective_environment_identity(config.repo_root, config.project_dir, mode=config.mode)
                != plan.environment_identity
            )
        except (OSError, ValueError) as exc:
            identity_error = f"Execution identity unavailable: {exc}"
    expired = bool(deadline and time.monotonic() >= deadline)
    if not (expired or source_changed or environment_changed or identity_error):
        return None
    phase = (
        "during execution"
        if completion and stage_num
        else "before completion validation"
        if completion
        else "after plan resolution"
    )
    diagnostic = (
        f"Run deadline expired {phase}"
        if expired
        else identity_error
        if identity_error
        else f"Consumed source changed {phase}; start a fresh run"
        if source_changed
        else f"Effective child environment changed {phase}; start a fresh run"
    )
    if source_changed and not expired and not identity_error and fingerprint_diagnostics is not None:
        diagnostic += "; fingerprint_diagnostics=" + json.dumps(
            fingerprint_diagnostics, sort_keys=True, separators=(",", ":")
        )
    state = StageStatus.TIMED_OUT if expired else StageStatus.BLOCKED
    return PipelineStageResult(
        stage_num,
        stage_name,
        False,
        0.0,
        124 if expired else 75,
        diagnostic,
        stage_completed=False,
        stage_key=stage_key,
        outcome=StageOutcome(stage_key, state, child_exit_code=None, diagnostic=diagnostic),
    )


__all__ = ["execution_guard_result"]
