"""Pipeline manifest for template_active_inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptStep:
    """Data container for ScriptStep."""

    name: str
    script: str


DEFAULT_ANALYSIS_SCRIPTS: tuple[ScriptStep, ...] = (
    ScriptStep("compose_manuscript", "compose_manuscript.py"),
    ScriptStep("run_analytical_sweep", "run_analytical_sweep.py"),
    ScriptStep("simulate_si_tmaze", "simulate_si_tmaze.py"),
    ScriptStep("simulate_si_graph_world", "simulate_si_graph_world.py"),
    ScriptStep("compute_statistics", "compute_statistics.py"),
    ScriptStep("generate_figures", "generate_figures.py"),
    ScriptStep("render_animation", "render_animation.py"),
    ScriptStep("generate_validation_spine", "generate_validation_spine.py"),
    ScriptStep("generate_toy_sweep_tracks", "generate_toy_sweep_tracks.py"),
    ScriptStep("generate_formal_interop_tracks", "generate_formal_interop_tracks.py"),
    ScriptStep("generate_integration_audit", "generate_integration_audit.py"),
    ScriptStep("generate_sheaf_tracks", "generate_sheaf_tracks.py"),
    ScriptStep("generate_manuscript_variables", "z_generate_manuscript_variables.py"),
)


def analysis_scripts(project_root: Path | None = None) -> list[Path]:
    """Process analysis scripts."""
    root = (project_root or Path(".")).resolve()
    scripts_dir = root / "scripts"
    return [scripts_dir / step.script for step in DEFAULT_ANALYSIS_SCRIPTS if (scripts_dir / step.script).exists()]
