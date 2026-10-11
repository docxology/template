"""Transported plans preserve resolved behavior and reject malformed authority."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline.plan import ExecutionPlan, compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


def _plan(tmp_path: Path) -> ExecutionPlan:
    scaffold_pipeline(tmp_path)
    return compile_execution_plan(PipelineConfig("demo", tmp_path, clean=False, skip_infra=True))


def test_plan_transport_roundtrip_preserves_parent_digest_and_contract(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    decoded = ExecutionPlan.from_dict(json.loads(json.dumps(plan.to_dict())), expected_digest=plan.digest)
    assert decoded == plan
    assert decoded.digest == plan.digest
    assert isinstance(decoded.stages, tuple)
    assert isinstance(decoded.stages[0].contract.input_artifacts, tuple)
    assert not (tmp_path / "projects/demo/output/.pipeline/execution.json").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("schema_version", 999),
        ("mode", []),
        ("mode", "automatic"),
        ("source_identity", "wrong"),
        ("environment_identity", ""),
        ("definition_identity", "g" * 64),
        ("provenance", "../private.yaml"),
        ("project", "../private"),
        ("hitl_mode", []),
        ("smart_pause_action", False),
        ("run_timeout_seconds", True),
        ("run_timeout_seconds", float("inf")),
        ("run_timeout_seconds", float("nan")),
        ("run_timeout_seconds", 0),
        ("run_timeout_seconds", 10**1000),
        ("stages", []),
    ],
)
def test_invalid_transported_plan_refuses_execution(tmp_path: Path, field: str, value: object) -> None:
    payload = _plan(tmp_path).to_dict()
    payload[field] = value
    with pytest.raises(ValueError):
        ExecutionPlan.from_dict(payload)


@pytest.mark.parametrize(
    "area,field,value",
    [
        ("stage", "key", "Bad key"),
        ("stage", "method", "another_target"),
        ("stage", "arguments", "--project demo"),
        ("stage", "allow_skip", 1),
        ("stage", "dependencies", ["invalid key"]),
        ("stage", "script", "../private.py"),
        ("contract", "retry_policy", True),
        ("contract", "retry_policy", -1),
        ("contract", "input_artifacts", ["../private"]),
        ("hooks", "pre_stage", ["echo forged"]),
        ("hooks", "pre_stage", [[]]),
        ("hooks", "run_in_ci", 1),
        ("hooks", "timeout_seconds", float("inf")),
        ("policy", "pause_before", 1),
        ("policy", "timeout_seconds", 0),
    ],
)
def test_stage_transport_has_no_type_coercion(tmp_path: Path, area: str, field: str, value: object) -> None:
    payload = json.loads(json.dumps(_plan(tmp_path).to_dict()))
    target = payload["stages"][0]
    if area != "stage":
        target = target[area]
    target[field] = value
    with pytest.raises(ValueError):
        ExecutionPlan.from_dict(payload)


def test_transport_rejects_unknown_fields_changed_digest_and_bad_order(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    payload = json.loads(json.dumps(plan.to_dict()))
    for target in (
        payload,
        payload["stages"][0],
        payload["stages"][0]["contract"],
        payload["stages"][0]["hooks"],
        payload["stages"][0]["policy"],
    ):
        target["forged_authority"] = True
        with pytest.raises(ValueError):
            ExecutionPlan.from_dict(payload)
        del target["forged_authority"]
    changed = copy.deepcopy(payload)
    changed["stages"][0]["arguments"].append("unreviewed")
    with pytest.raises(ValueError, match="digest"):
        ExecutionPlan.from_dict(changed, expected_digest=plan.digest)
    changed = copy.deepcopy(payload)
    changed["stages"].append(copy.deepcopy(changed["stages"][0]))
    with pytest.raises(ValueError, match="unique"):
        ExecutionPlan.from_dict(changed)
    payload["stages"][0]["dependencies"] = [payload["stages"][0]["key"]]
    with pytest.raises(ValueError, match="precede"):
        ExecutionPlan.from_dict(payload)


def test_targeted_plan_retains_external_prerequisites(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    payload = json.loads(json.dumps(plan.to_dict()))
    payload["stages"][0]["dependencies"] = ["previous_unselected_stage"]
    loaded = ExecutionPlan.from_dict(payload)
    assert loaded.stages[0].dependencies == ("previous_unselected_stage",)


@pytest.mark.parametrize("mode", ["core", "live"])
def test_transport_cannot_erase_canonical_target_capabilities(tmp_path: Path, mode: str) -> None:
    payload = json.loads(json.dumps(_plan(tmp_path).to_dict()))
    payload["mode"] = mode
    payload["stages"][0]["script"] = "scripts/pipeline/stage_06_llm_review.py"
    payload["stages"][0]["tags"] = []
    with pytest.raises(ValueError, match="binding canonical target capabilities"):
        ExecutionPlan.from_dict(payload)


def test_transported_live_target_cannot_claim_core_execution(tmp_path: Path) -> None:
    payload = json.loads(json.dumps(_plan(tmp_path).to_dict()))
    payload["stages"][0]["script"] = "scripts/pipeline/stage_06_llm_review.py"
    payload["stages"][0]["tags"] = ["llm", "live"]
    with pytest.raises(ValueError, match="live"):
        ExecutionPlan.from_dict(payload)
