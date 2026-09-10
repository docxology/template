"""Metric table tokens derived from run_summary.json."""

from __future__ import annotations

from pathlib import Path

from .generation_records import generation_metrics, load_run_summary
from .loop_config import load_sia_settings
from .manuscript_tokens_core import format_metric


def compute_metrics_variables(project_root: Path) -> dict[str, str]:
    """Build per-generation metric tokens and markdown table fragment."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)
    variables: dict[str, str] = {}
    table_lines = [
        "| Gen | Metric | Value | N |",
        "| --- | --- | ---: | ---: |",
    ]
    first_value: float | None = None
    last_value: float | None = None
    for row in metrics:
        generation = int(row.get("generation", 0))
        metric_name = str(row.get("metric_name", "accuracy"))
        metric_value = row.get("metric_value")
        n_samples = int(row.get("n_samples", 0))
        formatted = format_metric(metric_value)
        variables[f"SIA_GEN{generation}_METRIC_NAME"] = metric_name
        variables[f"SIA_GEN{generation}_METRIC_VALUE"] = formatted
        variables[f"SIA_GEN{generation}_N_SAMPLES"] = str(n_samples)
        table_lines.append(f"| {generation} | {metric_name} | {formatted} | {n_samples} |")
        if isinstance(metric_value, (int, float)):
            if first_value is None:
                first_value = float(metric_value)
            last_value = float(metric_value)
    variables["SIA_METRICS_TABLE"] = "\n".join(table_lines)
    if first_value is not None and last_value is not None:
        variables["SIA_METRIC_DELTA"] = format_metric(last_value - first_value)
    else:
        variables["SIA_METRIC_DELTA"] = "0"
    return variables


__all__ = ["compute_metrics_variables"]
