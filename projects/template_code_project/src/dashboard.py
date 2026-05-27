"""Interactive dashboard facade for template_code_project.

Payload computation lives in ``dashboard_payload``; Plotly panels in ``dashboard_panels``.
CLI entry point: ``scripts/build_dashboard.py``.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from .dashboard_panels import REPO_ROOT, build_dashboard, to_dashboard_invariant
from .dashboard_payload import compute_payload, load_yaml_defaults, to_diagonal_A
from .experiment_config import load_experiment_config
from .project_paths import _DEFAULT_ROOT as PROJECT_ROOT, project_output_dirs

_OUTPUT_DIRS = project_output_dirs(PROJECT_ROOT)
OUTPUT = _OUTPUT_DIRS["output"]
WEB_DIR = _OUTPUT_DIRS["web"]
DATA_DIR = _OUTPUT_DIRS["data"]
REP_DIR = _OUTPUT_DIRS["reports"]
CFG_DEFAULT = PROJECT_ROOT / "manuscript" / "config.yaml"

# Backward-compatible private aliases used by scripts/tests.
_load_yaml_defaults = load_yaml_defaults
_compute_payload = compute_payload
_build_dashboard = build_dashboard
_to_dashboard_invariant = to_dashboard_invariant
_to_diagonal_A = to_diagonal_A


def build_dashboard_html(project_root: Path | None = None) -> Path:
    """Build the dashboard with config defaults and write HTML to ``output/web/``."""
    root = (project_root or PROJECT_ROOT).resolve()
    dirs = project_output_dirs(root)
    cfg = load_experiment_config(root)
    args = SimpleNamespace(
        step_sizes=list(cfg.step_sizes),
        A=cfg.A_array().diagonal().tolist(),
        b=list(cfg.quadratic_b),
        x0=[cfg.initial_point],
        tol=float(cfg.tolerance),
        max_iter=int(cfg.max_iterations),
        alpha_sweep_min=0.005,
        alpha_sweep_max=1.95,
        alpha_sweep_num=40,
        landscape_x_min=-3.0,
        landscape_x_max=5.0,
        landscape_num=200,
    )
    payload = compute_payload(args)
    dashboard = build_dashboard(args, payload)
    result = dashboard.write(
        html_path=dirs["web"] / "dashboard.html",
        json_path=dirs["data"] / "dashboard_payload.json",
        invariants_path=dirs["reports"] / "dashboard_invariants.txt",
        txt_path=dirs["reports"] / "dashboard_summary.txt",
    )
    return Path(result["html"])


__all__ = [
    "CFG_DEFAULT",
    "DATA_DIR",
    "OUTPUT",
    "PROJECT_ROOT",
    "REP_DIR",
    "REPO_ROOT",
    "WEB_DIR",
    "_build_dashboard",
    "_compute_payload",
    "_load_yaml_defaults",
    "_to_dashboard_invariant",
    "_to_diagonal_A",
    "build_dashboard_html",
]
