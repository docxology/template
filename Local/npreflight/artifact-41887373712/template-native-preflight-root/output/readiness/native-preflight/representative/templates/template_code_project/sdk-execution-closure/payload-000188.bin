"""Source-bound execution records shared by every executor entry point."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor

EXECUTION_RECORD_SCHEMA = "template-execution-record/1"


def execution_record_payload(executor: PipelineExecutor, results: list[PipelineStageResult]) -> dict[str, object]:
    """Describe the exact resolved selection and observed outcomes."""
    plan = executor.execution_plan
    if plan is None:
        raise ValueError("Execution recording requires the resolved plan")
    result = executor.run_result(results)
    return {
        "schema_version": EXECUTION_RECORD_SCHEMA,
        "run_id": executor.run_id,
        "shared_infrastructure": executor.config.shared_infrastructure,
        "mode": plan.mode,
        "plan": plan.to_dict(),
        "plan_digest": plan.digest,
        "source_identity": plan.source_identity,
        "environment_identity": plan.environment_identity,
        "expected_stage_keys": list(result.expected_stage_keys),
        "selection": {
            "skip_clean": "clean" not in plan.expected_stage_keys,
            "skip_infra": "infra_tests" not in plan.expected_stage_keys,
        },
        "complete": result.complete,
        "exit_code": result.exit_code,
        "outcomes": [outcome.to_dict() for outcome in result.outcomes],
        "stage_results": [asdict(stage) for stage in results],
    }


def write_execution_record(executor: PipelineExecutor, results: list[PipelineStageResult]) -> list[PipelineStageResult]:
    """Persist actual expected stages and outcomes; a write refusal prevents completion."""
    payload = execution_record_payload(executor, results)
    output = executor.config.runtime_output_dir
    try:
        atomic_write_text_confined(
            output,
            output / ".pipeline" / "execution.json",
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            mode=0o600,
        )
    except (OSError, ValueError) as exc:
        diagnostic = f"Execution record could not be persisted: {exc}"
        results.append(
            PipelineStageResult(
                0,
                "Execution record",
                False,
                0.0,
                1,
                diagnostic,
                stage_completed=False,
                stage_key="execution_record",
                outcome=StageOutcome("execution_record", StageStatus.FAILED, None, diagnostic),
            )
        )
    return results
