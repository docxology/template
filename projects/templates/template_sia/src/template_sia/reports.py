"""Manuscript variables and loop summary reports."""

from __future__ import annotations

from pathlib import Path

from .generation_records import generation_metrics, load_run_summary
from .loop_config import load_sia_settings
from .manuscript_tokens_core import format_metric
from .manuscript_variables import compute_variables, save_variables


def write_loop_report(project_root: Path) -> Path:
    """Write a markdown summary of the SIA run."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)
    lines = [
        "# SIA loop report\n",
        f"- Task: `{settings.task_name}`\n",
        f"- Run id: {settings.run_id}\n",
        f"- Live mode: {settings.live}\n",
        f"- Generations: {len(metrics)}\n\n",
        "## Metrics\n\n",
        "| Gen | Metric | Value | N |\n",
        "| --- | --- | ---: | ---: |\n",
    ]
    for row in metrics:
        value = format_metric(row.get("metric_value"))
        lines.append(f"| {row.get('generation')} | {row.get('metric_name')} | {value} | {row.get('n_samples')} |\n")
    report_path = project_root / "output" / "reports" / "sia_loop_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")
    return report_path


def write_manuscript_variables(project_root: Path) -> Path:
    """Persist manuscript variables JSON."""
    return save_variables(project_root)


__all__ = [
    "format_metric",
    "compute_variables",
    "write_loop_report",
    "write_manuscript_variables",
]
