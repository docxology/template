"""Core manuscript tokens for template_sia."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .generation_records import generation_metrics, load_run_summary
from .loop_config import load_paper_title, load_sia_settings


def _format_metric(value: Any) -> str:
    if value is None:
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return str(value)


def compute_core_variables(project_root: Path) -> dict[str, str]:
    """Build run metadata tokens shared across manuscript sections."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)
    final = metrics[-1] if metrics else {}
    return {
        "CONFIG_TITLE": load_paper_title(project_root),
        "SIA_TASK_NAME": settings.task_name,
        "SIA_RUN_ID": str(settings.run_id),
        "SIA_MAX_GENERATIONS": str(settings.max_generations),
        "SIA_LIVE_MODE": str(settings.live).lower(),
        "SIA_GENERATION_COUNT": str(len(metrics)),
        "SIA_FINAL_METRIC_NAME": str(final.get("metric_name", "accuracy")),
        "SIA_FINAL_METRIC_VALUE": _format_metric(final.get("metric_value")),
        "SIA_FINAL_N_SAMPLES": str(final.get("n_samples", 0)),
    }


__all__ = ["compute_core_variables", "_format_metric"]
