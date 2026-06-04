"""Load SIA generation records from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_run_summary(project_root: Path, *, run_id: int = 1) -> dict[str, Any]:
    """Load runs/run_{id}/run_summary.json."""
    path = project_root / "output" / "runs" / f"run_{run_id}" / "run_summary.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing run summary: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid run summary: {path}")
    return payload


def generation_metrics(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract per-generation metric rows from a run summary."""
    rows: list[dict[str, Any]] = []
    for item in summary.get("generations", []):
        if not isinstance(item, dict):
            continue
        evaluation = item.get("evaluation")
        if not isinstance(evaluation, dict) or not evaluation.get("metric_name"):
            continue
        rows.append(
            {
                "generation": item.get("generation"),
                "metric_name": evaluation.get("metric_name", ""),
                "metric_value": evaluation.get("metric_value"),
                "n_samples": evaluation.get("n_samples"),
            }
        )
    return rows


__all__ = ["generation_metrics", "load_run_summary"]
