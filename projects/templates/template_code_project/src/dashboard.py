"""Interactive dashboard facade for template_code_project.

Payload computation lives in ``dashboard_payload``; Plotly panels in ``dashboard_panels``.
CLI entry point: ``scripts/build_dashboard.py`` → ``cli_main()``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

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


def parse_dashboard_args(
    argv: list[str] | None = None,
    *,
    defaults_loader=load_yaml_defaults,
) -> argparse.Namespace:
    """Parse CLI arguments for the dashboard builder."""
    cfg = defaults_loader(CFG_DEFAULT)
    a_diag = np.diag(cfg.A_array()).tolist()
    parser = argparse.ArgumentParser(
        description="Build the interactive optimization dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--step-sizes", type=float, nargs="+", default=list(cfg.step_sizes))
    parser.add_argument("--A", type=float, nargs="+", default=[float(v) for v in a_diag])
    parser.add_argument("--b", type=float, nargs="+", default=list(cfg.quadratic_b))
    parser.add_argument("--x0", type=float, nargs="+", default=[cfg.initial_point])
    parser.add_argument("--tol", type=float, default=float(cfg.tolerance))
    parser.add_argument("--max-iter", type=int, default=int(cfg.max_iterations))
    parser.add_argument("--alpha-sweep-min", type=float, default=0.005)
    parser.add_argument("--alpha-sweep-max", type=float, default=1.95)
    parser.add_argument("--alpha-sweep-num", type=int, default=40)
    parser.add_argument("--landscape-x-min", type=float, default=-3.0)
    parser.add_argument("--landscape-x-max", type=float, default=5.0)
    parser.add_argument("--landscape-num", type=int, default=200)
    parser.add_argument("--html-out", type=Path, default=WEB_DIR / "dashboard.html")
    parser.add_argument("--json-out", type=Path, default=DATA_DIR / "dashboard_payload.json")
    parser.add_argument("--invariants-out", type=Path, default=REP_DIR / "dashboard_invariants.txt")
    parser.add_argument("--summary-out", type=Path, default=REP_DIR / "dashboard_summary.txt")
    args = parser.parse_args(argv)
    if not args.step_sizes:
        parser.error("--step-sizes must list at least one positive α")
    if any(a <= 0 for a in args.step_sizes):
        parser.error("every --step-sizes value must be > 0")
    if len(args.A) != len(args.b):
        parser.error(f"--A length ({len(args.A)}) must equal --b length ({len(args.b)})")
    if len(args.x0) != len(args.b):
        parser.error(f"--x0 length ({len(args.x0)}) must equal --b length ({len(args.b)})")
    if args.alpha_sweep_max <= args.alpha_sweep_min:
        parser.error("--alpha-sweep-max must be > --alpha-sweep-min")
    if args.alpha_sweep_num < 2:
        parser.error("--alpha-sweep-num must be ≥ 2")
    return args


def cli_main(argv: list[str] | None = None, *, dashboard_builder=build_dashboard) -> None:
    """Build dashboard artifacts from CLI arguments."""
    args = parse_dashboard_args(argv)
    payload = compute_payload(args)
    dashboard = dashboard_builder(args, payload)
    outputs = dashboard.write(
        html_path=args.html_out,
        json_path=args.json_out,
        invariants_path=args.invariants_out,
        txt_path=args.summary_out,
    )
    for key in ("html", "json", "invariants", "summary"):
        if key in outputs:
            print(outputs[key])

    failed = [item for item in dashboard.evaluate_invariants() if not item["passed"]]
    if failed:
        names = ", ".join(item["name"] for item in failed)
        print(f"FAILED INVARIANTS: {names}", file=sys.stderr)
        sys.exit(1)


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
    "cli_main",
    "parse_dashboard_args",
]
