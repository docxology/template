"""Render-time manuscript variables for template_sia."""

from __future__ import annotations

import json
from pathlib import Path

from .manuscript_tokens_core import compute_core_variables
from .manuscript_tokens_metrics import compute_metrics_variables


def compute_variables(project_root: Path) -> dict[str, str]:
    """Merge all manuscript tokens for substitution."""
    variables = compute_core_variables(project_root)
    variables.update(compute_metrics_variables(project_root))
    return variables


def save_variables(project_root: Path) -> Path:
    """Persist manuscript variables JSON under output/data/."""
    variables = compute_variables(project_root)
    out = project_root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(variables, indent=2) + "\n", encoding="utf-8")
    return out


__all__ = ["compute_variables", "save_variables"]
