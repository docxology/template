"""Tests for deterministic AutoResearch result models."""

from __future__ import annotations

from pathlib import Path

from src.config import load_loop_config
from src.models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult


def test_stage_and_claim_models_serialize_to_json_safe_dicts() -> None:
    stage = LoopStageResult(
        name="readiness",
        status="declared",
        evidence="output/reports/autoresearch_readiness.json",
        suggested_action="Proceed to manuscript hydration.",
    )
    claim = AutoResearchClaim(
        identifier="rq1",
        statement="The readiness gate passed.",
        evidence_path="output/reports/autoresearch_readiness.json",
        supported=True,
    )

    assert stage.to_dict() == {
        "name": "readiness",
        "status": "declared",
        "evidence": "output/reports/autoresearch_readiness.json",
        "suggested_action": "Proceed to manuscript hydration.",
    }
    assert claim.to_dict() == {
        "identifier": "rq1",
        "statement": "The readiness gate passed.",
        "evidence_path": "output/reports/autoresearch_readiness.json",
        "supported": True,
    }


def test_loop_result_serializes_metrics_and_nested_models(project_root: Path) -> None:
    config = load_loop_config(project_root)
    result = AutoResearchLoopResult(
        project_name="template_autoresearch_project",
        generated_at="2026-05-25T00:00:00+00:00",
        config=config,
        stage_results=(
            LoopStageResult(
                name="plan",
                status="declared",
                evidence="output/data/autoresearch_plan.json",
                suggested_action="Review plan.",
            ),
        ),
        claims=(
            AutoResearchClaim(
                identifier="rq1",
                statement="The loop produces a plan artifact.",
                evidence_path="output/data/autoresearch_plan.json",
                supported=True,
            ),
            AutoResearchClaim(
                identifier="rq2",
                statement="An unsupported claim is counted separately.",
                evidence_path="output/data/autoresearch_claims.json",
                supported=False,
            ),
        ),
        readiness_valid=True,
        output_paths=("output/data/autoresearch_loop.json",),
    )

    payload = result.to_dict()

    assert result.supported_claim_count == 1
    assert payload["config"]["topic"] == config.topic
    assert payload["stage_results"][0]["name"] == "plan"
    assert payload["claims"][1]["supported"] is False
    assert payload["metrics"] == {
        "stage_count": 1,
        "supported_claim_count": 1,
        "required_artifact_count": len(config.required_artifacts),
        "readiness_valid": True,
    }
    assert payload["ml_task"] == {}
    assert payload["output_paths"] == ["output/data/autoresearch_loop.json"]
