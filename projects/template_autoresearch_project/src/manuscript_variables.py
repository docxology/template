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
    return compute_variables_from_payload(payload)


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
    }


def save_variables(variables: dict[str, str], path: Path) -> Path:
    """Write manuscript variables as stable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
