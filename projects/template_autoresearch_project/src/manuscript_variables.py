"""Render-time manuscript variables for the AutoResearch exemplar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compute_variables(project_root: Path) -> dict[str, str]:
    """Compute manuscript variables from the last loop payload."""
    payload_path = project_root / "output" / "data" / "autoresearch_loop.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("autoresearch_loop.json must contain a mapping")
    variables = compute_variables_from_payload(payload)
    ml_path = project_root / "output" / "data" / "ml_task_results.json"
    if ml_path.exists():
        ml_payload = json.loads(ml_path.read_text(encoding="utf-8"))
        if isinstance(ml_payload, dict):
            variables.update(compute_ml_variables(ml_payload))
    return variables


def compute_variables_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Compute manuscript variables from an in-memory loop payload."""
    metrics = payload.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    config = payload.get("config", {})
    if not isinstance(config, dict):
        config = {}
    stage_results = payload.get("stage_results", [])
    claims = payload.get("claims", [])
    stage_count = int(metrics.get("stage_count", len(stage_results)) or 0)
    supported_claim_count = int(metrics.get("supported_claim_count", len(claims)) or 0)
    required_artifact_count = int(metrics.get("required_artifact_count", 0) or 0)
    readiness_valid = bool(metrics.get("readiness_valid", False))
    readiness_status = "passed" if readiness_valid else "requires review"
    return {
        "AUTORESEARCH_TOPIC": str(config.get("topic", "Deterministic AutoResearch")),
        "LOOP_STAGE_COUNT": str(stage_count),
        "SUPPORTED_CLAIM_COUNT": str(supported_claim_count),
        "REQUIRED_ARTIFACT_COUNT": str(required_artifact_count),
        "READINESS_STATUS": readiness_status,
        "READINESS_VALID": str(readiness_valid).lower(),
        **compute_ml_variables(payload.get("ml_task", {})),
    }


def compute_ml_variables(payload: object) -> dict[str, str]:
    """Compute manuscript variables from an ML task payload or summary."""
    if not isinstance(payload, dict):
        payload = {}
    dataset = payload.get("dataset", {})
    if not isinstance(dataset, dict):
        dataset = {}
    return {
        "ML_TASK_SEED": _string_value(payload.get("seed", dataset.get("seed", "N/A"))),
        "CANDIDATE_COUNT": _string_value(payload.get("candidate_count", "N/A")),
        "EVALUATED_CANDIDATE_COUNT": _string_value(payload.get("evaluated_candidate_count", "N/A")),
        "ACCEPTED_CANDIDATE_ID": _string_value(payload.get("accepted_candidate_id", "N/A")),
        "BASELINE_ACCURACY": _percent_value(payload.get("baseline_accuracy")),
        "BEST_ACCURACY": _percent_value(payload.get("best_accuracy")),
        "ACCURACY_DELTA": _percent_value(payload.get("accuracy_delta")),
        "BUDGET_EXHAUSTED": str(bool(payload.get("budget_exhausted", False))).lower(),
        "BENCHMARK_SCORE": _string_value(payload.get("benchmark_score", "N/A")),
        "LLM_CALLS_USED": _string_value(payload.get("llm_calls_used", 0)),
        "COST_USD_USED": _currency_value(payload.get("cost_usd_used", 0.0)),
    }


def _string_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _percent_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def _currency_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.2f}"


def save_variables(variables: dict[str, str], path: Path) -> Path:
    """Write manuscript variables as stable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
