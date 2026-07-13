"""Pipeline output artifact validation."""

from __future__ import annotations

from pathlib import Path

from gates.artifact_manifest import REQUIRED_OUTPUTS
from gates.output_checks_promoted import (
    add_canonical_sheaf_checks,
    add_toy_formal_integration_checks,
    add_track_validator_checks,
    add_visualization_checks,
    load_promoted_artifacts,
    set_experiment_plan_metrics,
)
from gates.output_checks_simulation import add_log_check, add_simulation_checks
from gates.output_checks_spine import add_validation_spine_checks
from visualizations.figure_io import image_render_metrics

_MIN_FIGURE_BYTES = 5_000


def _figures_nonblank(
    root: Path,
    *,
    required_outputs: tuple[str, ...] = REQUIRED_OUTPUTS,
    min_figure_bytes: int = _MIN_FIGURE_BYTES,
) -> bool:
    png_rels = [rel for rel in required_outputs if rel.startswith("output/figures/") and rel.endswith(".png")]
    if not png_rels:
        return False
    for rel in png_rels:
        path = root / rel
        if not path.is_file() or path.stat().st_size < min_figure_bytes:
            return False
        metrics = image_render_metrics(path)
        if not metrics["width_px"] or not metrics["height_px"] or not metrics["nonblank"]:
            return False
    return True


def _required_output_checks(root: Path) -> dict[str, bool]:
    return {str((root / rel).relative_to(root)): (root / rel).exists() for rel in REQUIRED_OUTPUTS}


def validate_outputs(project_root: Path) -> dict[str, bool]:
    """Validate every registered output artifact and return gate booleans by name."""
    root = project_root.resolve()
    checks = _required_output_checks(root)
    checks["figures_nonblank"] = _figures_nonblank(root)
    simulation_context = add_simulation_checks(root, checks)
    spine_context = add_validation_spine_checks(root, checks)
    artifacts = load_promoted_artifacts(root)
    add_toy_formal_integration_checks(checks, artifacts)
    add_visualization_checks(checks, artifacts)
    add_canonical_sheaf_checks(checks, artifacts)
    add_track_validator_checks(root, checks, artifacts["animation_deltas"])
    add_log_check(root, checks)
    set_experiment_plan_metrics(root, checks, simulation_context, spine_context)
    return checks
