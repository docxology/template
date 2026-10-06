"""Original input and human review bindings transported to actual stage attempts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifact_contracts import InputContractError, InputSnapshot, capture_inputs_at
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.hitl_context import reviewed_content_digest
from infrastructure.core.pipeline.types import StageContract, StageSpec

SCHEMA = "template-stage-admission/1"


def original_stage_admission(
    snapshot: InputSnapshot,
    stage: StageSpec,
    controller: HitlController,
    *,
    shared_infrastructure: bool = False,
) -> dict[str, object]:
    """Bind the snapshot taken before hooks and the original consumed decision."""
    return {
        "schema": SCHEMA,
        "run_id": controller.run_id,
        "plan_digest": controller.plan_digest,
        "stage_key": stage.key or stage.name,
        "input_artifacts": list(stage.contract.input_artifacts),
        "output_artifacts": list(stage.contract.output_artifacts),
        "mutable_artifacts": list(stage.contract.mutable_artifacts),
        "input_digest": snapshot.digest,
        "approval": controller.approved_binding(stage),
        "shared_infrastructure": shared_infrastructure,
    }


def validate_stage_admission(
    payload: object,
    *,
    repo: Path,
    project: Path,
    run_id: str,
    plan_digest: str,
    stage_key: str,
    before_attempt: bool = True,
) -> None:
    """Recheck original inputs, and approval immediately before actual execution."""
    fields = {
        "schema",
        "run_id",
        "plan_digest",
        "stage_key",
        "input_artifacts",
        "output_artifacts",
        "mutable_artifacts",
        "input_digest",
        "approval",
        "shared_infrastructure",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != fields
        or payload["schema"] != SCHEMA
        or payload["run_id"] != run_id
        or payload["plan_digest"] != plan_digest
        or payload["stage_key"] != stage_key
        or not isinstance(payload["input_digest"], str)
        or len(payload["input_digest"]) != 64
        or any(
            not isinstance(payload[key], list) or any(not isinstance(item, str) for item in payload[key])
            for key in ("input_artifacts", "output_artifacts", "mutable_artifacts")
        )
        or (payload["approval"] is not None and not isinstance(payload["approval"], dict))
        or type(payload["shared_infrastructure"]) is not bool
        or (payload["shared_infrastructure"] and stage_key != "infra_tests")
    ):
        raise InputContractError("Actual attempt has no valid original stage admission")
    contract = StageContract(
        input_artifacts=tuple(payload["input_artifacts"]),
        output_artifacts=tuple(payload["output_artifacts"]),
        mutable_artifacts=tuple(payload["mutable_artifacts"]),
    )
    if capture_inputs_at(repo, project, contract).digest != payload["input_digest"]:
        raise InputContractError("Consumed input contents changed before the actual attempt")
    approval: dict[str, Any] | None = payload["approval"]
    if before_attempt and approval is not None:
        runtime_root = (
            repo / "output/.pipeline/shared_infrastructure" / project.relative_to(repo)
            if payload["shared_infrastructure"]
            else project / "output"
        )
        controller = HitlController(
            project_output_dir=runtime_root,
            run_id=run_id,
            plan_digest=plan_digest,
            repo_root=repo,
            project_dir=project,
        )
        controller.validate_consumed_binding(approval, stage_key)
        if approval.get("artifact_digest") != reviewed_content_digest(
            runtime_root,
            contract.input_artifacts,
            repo,
            contract.output_artifacts,
            project_dir=project,
        ):
            raise InputContractError("Originally approved review contents changed before the actual attempt")


__all__ = ["original_stage_admission", "validate_stage_admission"]
