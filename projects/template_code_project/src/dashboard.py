"""Interactive simulation dashboard implementation for template_code_project.

This module builds the dashboard payload, invariants, and HTML output. The
matching script is a small CLI wrapper so dashboard behavior can be imported
from ``src`` without duplicating orchestration code.

The dashboard:

1. Reads the same configuration the analysis pipeline reads from
   ``manuscript/config.yaml`` (step sizes, A, b, initial point, tolerance,
   max_iterations) — every dashboard knob is also a CLI flag, so the
   simulation is fully configurable without editing source.

2. Runs gradient descent on the configured quadratic problem for every
   step size and a parameterized α-sweep, then emits a self-contained
   ``output/web/dashboard.html`` with five linked Plotly panels:

     - convergence trajectories (per-α objective vs iteration)
     - iterations-to-converge vs α (sweep)
     - final ||x − x*|| vs α (sweep)
     - 1-D objective landscape with overlaid trajectory at slider α
     - condition-number / stability-bound diagnostic

3. Emits plaintext companion artefacts for CI / agent validation:

     - ``output/reports/dashboard_invariants.txt`` (pass/fail with witnesses)
     - ``output/reports/dashboard_summary.txt``
     - ``output/data/dashboard_payload.json`` (full numerical payload)

Defaults read directly from ``manuscript/config.yaml`` (so the dashboard
matches what the manuscript reports). Override any flag to explore a
different regime — exits non-zero on any invariant failure.

Usage through the compatibility wrapper::

    uv run --active python scripts/build_dashboard.py
    uv run --active python scripts/build_dashboard.py --step-sizes 0.05 0.1 0.5 1.0 1.9 2.5
    uv run --active python scripts/build_dashboard.py --A 1.0 --b 1.0 --x0 0.0
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
REPO_ROOT = PROJECT_ROOT.parent.parent
for _p in (SRC_DIR, REPO_ROOT):
    sys.path.insert(0, str(_p))


import numpy as np  # noqa: E402

from infrastructure.reporting.interactive_dashboard import (  # noqa: E402
    InteractiveDashboard,
    Invariant,
    Panel,
)

try:
    from .experiment_config import ExperimentConfig, load_experiment_config
    from .invariants import OptimizerSweepConfig, all_invariants  # noqa: E402
    from .optimizer import (  # noqa: E402
        quadratic_function,
        simulate_trajectory,
    )
except ImportError:  # pragma: no cover - supports direct module execution
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from invariants import OptimizerSweepConfig, all_invariants  # type: ignore[no-redef]  # noqa: E402
    from optimizer import (  # type: ignore[no-redef]  # noqa: E402
        quadratic_function,
        simulate_trajectory,
    )

OUTPUT = PROJECT_ROOT / "output"
WEB_DIR = OUTPUT / "web"
DATA_DIR = OUTPUT / "data"
REP_DIR = OUTPUT / "reports"

CFG_DEFAULT = PROJECT_ROOT / "manuscript" / "config.yaml"


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def _load_yaml_defaults(_path: Path) -> ExperimentConfig:
    """Load experiment defaults from ``manuscript/config.yaml``."""
    return load_experiment_config(PROJECT_ROOT)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    cfg = _load_yaml_defaults(CFG_DEFAULT)
    a_diag = np.diag(cfg.A_array()).tolist()
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--step-sizes",
        type=float,
        nargs="+",
        default=list(cfg.step_sizes),
        help="step sizes α to evaluate",
    )
    p.add_argument(
        "--A",
        type=float,
        nargs="+",
        default=[float(v) for v in a_diag],
        help="diagonal entries of A (quadratic Hessian); order = dim",
    )
    p.add_argument(
        "--b",
        type=float,
        nargs="+",
        default=list(cfg.quadratic_b),
        help="linear-term vector b",
    )
    p.add_argument(
        "--x0",
        type=float,
        nargs="+",
        default=[cfg.initial_point],
        help="initial point",
    )
    p.add_argument("--tol", type=float, default=float(cfg.tolerance))
    p.add_argument("--max-iter", type=int, default=int(cfg.max_iterations))
    p.add_argument(
        "--alpha-sweep-min",
        type=float,
        default=0.005,
        help="lower α for the iterations-vs-α sweep panel",
    )
    p.add_argument(
        "--alpha-sweep-max",
        type=float,
        default=1.95,
        help="upper α for the iterations-vs-α sweep panel",
    )
    p.add_argument("--alpha-sweep-num", type=int, default=40)
    p.add_argument(
        "--landscape-x-min",
        type=float,
        default=-3.0,
        help="x range (lower) for the 1-D objective landscape panel",
    )
    p.add_argument(
        "--landscape-x-max",
        type=float,
        default=5.0,
        help="x range (upper) for the 1-D objective landscape panel",
    )
    p.add_argument("--landscape-num", type=int, default=200)
    p.add_argument("--html-out", type=Path, default=WEB_DIR / "dashboard.html")
    p.add_argument("--json-out", type=Path, default=DATA_DIR / "dashboard_payload.json")
    p.add_argument("--invariants-out", type=Path, default=REP_DIR / "dashboard_invariants.txt")
    p.add_argument("--summary-out", type=Path, default=REP_DIR / "dashboard_summary.txt")
    args = p.parse_args(argv)
    if not args.step_sizes:
        p.error("--step-sizes must list at least one positive α")
    if any(a <= 0 for a in args.step_sizes):
        p.error("every --step-sizes value must be > 0")
    if len(args.A) != len(args.b):
        p.error(f"--A length ({len(args.A)}) must equal --b length ({len(args.b)})")
    if len(args.x0) != len(args.b):
        p.error(f"--x0 length ({len(args.x0)}) must equal --b length ({len(args.b)})")
    if args.alpha_sweep_max <= args.alpha_sweep_min:
        p.error("--alpha-sweep-max must be > --alpha-sweep-min")
    if args.alpha_sweep_num < 2:
        p.error("--alpha-sweep-num must be ≥ 2")
    return args


# ---------------------------------------------------------------------------
# Compute payload
# ---------------------------------------------------------------------------


def _to_diagonal_A(diag: list[float]) -> np.ndarray:
    return np.diag(np.array(diag, dtype=np.float64))


def _compute_payload(args: argparse.Namespace) -> dict:
    A = _to_diagonal_A(args.A)
    b = np.array(args.b, dtype=np.float64)
    x_star = np.linalg.solve(A, b)
    f_star = float(quadratic_function(x_star, A=A, b=b))
    eig = np.linalg.eigvalsh(A)
    stable_bound = float(2.0 / eig.max())

    # Per-α full convergence trajectories (1-D landscape ≈ x history projected)
    trajectories: dict[str, dict] = {}
    for alpha in args.step_sizes:
        traj = simulate_trajectory(
            float(alpha),
            max_iter=min(args.max_iter, 200),
            A=A,
            b=b,
            initial_point=np.array(args.x0, dtype=np.float64),
        )
        trajectories[f"{float(alpha):.4f}"] = {
            "iterations": list(traj["iterations"]),
            "objectives": list(traj["objectives"]),
        }

    # α-sweep: iterations to converge + final distance
    alphas = np.linspace(args.alpha_sweep_min, args.alpha_sweep_max, args.alpha_sweep_num)
    iters: list[int] = []
    final_dist: list[float] = []
    final_obj: list[float] = []
    diverged: list[bool] = []
    cfg_run = OptimizerSweepConfig(
        step_sizes=tuple(float(a) for a in alphas),
        A=tuple(tuple(row) for row in A),
        b=tuple(float(v) for v in b),
        initial_point=tuple(float(v) for v in args.x0),
        max_iterations=int(args.max_iter),
        tolerance=float(args.tol),
    )
    for alpha in alphas:
        try:
            r = cfg_run.run_for(float(alpha))
            iters.append(int(r.iterations))
            final_dist.append(float(np.linalg.norm(r.solution - x_star)))
            final_obj.append(float(r.objective_value))
            diverged.append(bool(np.linalg.norm(r.solution - x_star) > 1e3))
        # Divergent step sizes can raise OverflowError / FloatingPointError or
        # propagate np.linalg errors; record-and-continue is the right per-α
        # behavior so the sweep produces a row for every requested α.
        except (OverflowError, FloatingPointError, ValueError, np.linalg.LinAlgError):  # noqa: BLE001
            iters.append(args.max_iter)
            final_dist.append(float("inf"))
            final_obj.append(float("inf"))
            diverged.append(True)

    # 1-D landscape (only meaningful when n=1; emit anyway with first coord)
    xs = np.linspace(args.landscape_x_min, args.landscape_x_max, args.landscape_num)
    fs = []
    for x in xs:
        xv = np.zeros_like(b)
        xv[0] = x
        fs.append(float(quadratic_function(xv, A=A, b=b)))

    return {
        "step_sizes": [float(a) for a in args.step_sizes],
        "A_diagonal": [float(v) for v in args.A],
        "b": [float(v) for v in args.b],
        "x0": [float(v) for v in args.x0],
        "x_star": x_star.tolist(),
        "f_star": f_star,
        "eigenvalues": eig.tolist(),
        "condition_number": float(eig.max() / eig.min()),
        "stable_step_bound": stable_bound,
        "trajectories": trajectories,
        "alpha_sweep": {
            "alphas": alphas.tolist(),
            "iterations": iters,
            "final_dist": final_dist,
            "final_obj": final_obj,
            "diverged": diverged,
        },
        "landscape": {"x": xs.tolist(), "f": fs},
    }


# ---------------------------------------------------------------------------
# Build dashboard
# ---------------------------------------------------------------------------


def _to_dashboard_invariant(r) -> Invariant:
    return Invariant(
        name=r.name,
        actual=r.actual,
        expected=r.expected,
        tol=r.tol,
        kind=r.kind,
        description=r.description,
    )


def _build_dashboard(args: argparse.Namespace, payload: dict) -> InteractiveDashboard:
    d = InteractiveDashboard(
        title="Optimization Exemplar — Interactive Convergence Suite",
        subtitle=(
            "Live gradient-descent diagnostics on the configurable "
            "quadratic f(x) = (1/2) x^T A x − b^T x. "
            "Defaults read from manuscript/config.yaml; every knob is CLI-overridable."
        ),
        project_name="template_code_project",
        repo_root=REPO_ROOT,
    )
    d.set_hyperparameters(
        {
            "A_diagonal": payload["A_diagonal"],
            "b": payload["b"],
            "x0": payload["x0"],
            "step_sizes": payload["step_sizes"],
            "tolerance": args.tol,
            "max_iterations": args.max_iter,
            "alpha_sweep_min": args.alpha_sweep_min,
            "alpha_sweep_max": args.alpha_sweep_max,
            "alpha_sweep_num": args.alpha_sweep_num,
            "stable_step_bound": payload["stable_step_bound"],
            "condition_number": payload["condition_number"],
            "x_star": payload["x_star"],
            "f_star": payload["f_star"],
        }
    )
    d.set_payload(payload)
    d.add_note("Stable step bound: 2/λ_max(A). Step sizes ≥ this bound are expected to diverge.")
    d.add_note("Closed-form minimum: x* = A^{-1} b; f(x*) is reported in the hyperparameters block.")

    # Controls
    d.add_dropdown(
        control_id="alpha_select",
        label="step size α (overlay)",
        options=payload["step_sizes"],
        default=payload["step_sizes"][0],
        option_labels=[f"α = {a:g}" for a in payload["step_sizes"]],
        description="overlay this α's trajectory on the landscape",
    )
    d.add_slider(
        control_id="x0_landscape",
        label="x_0 (landscape probe)",
        min=float(args.landscape_x_min),
        max=float(args.landscape_x_max),
        step=(args.landscape_x_max - args.landscape_x_min) / args.landscape_num,
        default=float(payload["x0"][0]),
        description="initial x for the live trajectory overlay",
    )

    # Panel 1 — convergence trajectories
    traj_traces = []
    palette = ["#38bdf8", "#fb923c", "#a78bfa", "#22c55e", "#ef4444", "#facc15", "#06b6d4"]
    for i, (alpha_str, t) in enumerate(payload["trajectories"].items()):
        traj_traces.append(
            {
                "type": "scatter",
                "mode": "lines",
                "name": f"α = {float(alpha_str):g}",
                "x": t["iterations"],
                "y": t["objectives"],
                "line": {"color": palette[i % len(palette)]},
            }
        )
    d.add_panel(
        Panel(
            panel_id="convergence_trajectories",
            title="Objective vs iteration (per step size)",
            description=("Stable α (< 2/λ_max(A)) → monotone descent to f(x*). α ≥ stable bound → divergence."),
            traces=traj_traces,
            layout={
                "xaxis": {"title": "iteration"},
                "yaxis": {"title": "objective f(x_t)"},
                "legend": {"orientation": "h", "y": -0.2},
            },
        )
    )

    # Panel 2 — iterations vs α sweep
    sw = payload["alpha_sweep"]
    d.add_panel(
        Panel(
            panel_id="iters_vs_alpha",
            title="Iterations to converge vs α",
            description=(
                "U-shape: too small α → slow (capped at max_iterations); "
                f"α ≥ {payload['stable_step_bound']:.3g} → divergence (also capped)."
            ),
            traces=[
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "iterations",
                    "x": sw["alphas"],
                    "y": sw["iterations"],
                    "line": {"color": "#fb923c"},
                    "marker": {"size": 5},
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "stable bound",
                    "x": [payload["stable_step_bound"], payload["stable_step_bound"]],
                    "y": [0, max(sw["iterations"]) if sw["iterations"] else args.max_iter],
                    "line": {"color": "#94a3b8", "dash": "dot"},
                },
            ],
            layout={
                "xaxis": {"title": "step size α"},
                "yaxis": {"title": "iterations to converge"},
                "legend": {"orientation": "h", "y": -0.2},
            },
        )
    )

    # Panel 3 — final distance vs α
    d.add_panel(
        Panel(
            panel_id="final_dist_vs_alpha",
            title="Final ||x_T − x*|| vs α",
            description=(
                "Stable region: distance ≪ tol; divergent region: distance grows without bound (clipped on log-y)."
            ),
            traces=[
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "||x_T − x*||",
                    "x": sw["alphas"],
                    "y": [max(d, 1e-15) for d in sw["final_dist"]],
                    "line": {"color": "#a78bfa"},
                    "marker": {"size": 5},
                },
            ],
            layout={
                "xaxis": {"title": "step size α"},
                "yaxis": {"title": "||x_T − x*||", "type": "log"},
                "legend": {"orientation": "h", "y": -0.2},
            },
        )
    )

    # Panel 4 — 1-D objective landscape with live trajectory overlay
    d.add_panel(
        Panel(
            panel_id="landscape",
            title="1-D objective landscape (slice along x_0)",
            description=(
                "Quadratic landscape with the live gradient-descent trajectory "
                "for the dropdown-selected α and slider x_0."
            ),
            traces=[
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "f(x)",
                    "x": payload["landscape"]["x"],
                    "y": payload["landscape"]["f"],
                    "line": {"color": "#38bdf8"},
                },
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "x*",
                    "x": [payload["x_star"][0]],
                    "y": [payload["f_star"]],
                    "marker": {"color": "#22c55e", "size": 12, "symbol": "star"},
                },
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "trajectory",
                    "x": [],
                    "y": [],
                    "line": {"color": "#fb923c"},
                    "marker": {"size": 5},
                },
            ],
            layout={
                "xaxis": {"title": "x"},
                "yaxis": {"title": "f(x)"},
                "legend": {"orientation": "h", "y": -0.2},
            },
            driven_by=["alpha_select", "x0_landscape"],
            update_fn=r"""
const alpha = controls.alpha_select;
const x0 = controls.x0_landscape;
const A0 = payload.A_diagonal[0];
const b0 = payload.b[0];
const xs = [x0];
const ys = [];
function f(x){ return 0.5 * A0 * x * x - b0 * x; }
function g(x){ return A0 * x - b0; }
ys.push(f(x0));
let x = x0;
for (let i = 0; i < 200; i++){
  const grad = g(x);
  if (Math.abs(grad) < 1e-8) break;
  x = x - alpha * grad;
  if (!isFinite(x) || Math.abs(x) > 1e6) break;
  xs.push(x);
  ys.push(f(x));
}
Plotly.restyle(panelId, {x: [xs], y: [ys]}, [2]);
""",
        )
    )

    # Panel 5 — diagnostics
    d.add_panel(
        Panel(
            panel_id="diagnostics",
            title="Stability diagnostics",
            description=("Bar chart of A's eigenvalues with the stable-step bound 2/λ_max marked."),
            traces=[
                {
                    "type": "bar",
                    "name": "eigenvalues of A",
                    "x": [f"λ_{i}" for i in range(len(payload["eigenvalues"]))],
                    "y": payload["eigenvalues"],
                    "marker": {"color": "#a78bfa"},
                },
            ],
            layout={
                "xaxis": {"title": "eigenvalue"},
                "yaxis": {"title": "value"},
                "annotations": [
                    {
                        "x": 0.5,
                        "y": 0.95,
                        "xref": "paper",
                        "yref": "paper",
                        "text": (
                            f"stable α-bound 2/λ_max = "
                            f"{payload['stable_step_bound']:.4g}; "
                            f"κ(A) = {payload['condition_number']:.4g}"
                        ),
                        "showarrow": False,
                        "font": {"color": "#e5e7eb"},
                    }
                ],
            },
        )
    )

    # Invariants
    cfg = OptimizerSweepConfig(
        step_sizes=tuple(args.step_sizes),
        A=tuple(tuple(row) for row in _to_diagonal_A(args.A)),
        b=tuple(float(v) for v in args.b),
        initial_point=tuple(float(v) for v in args.x0),
        max_iterations=int(args.max_iter),
        tolerance=float(args.tol),
    )
    for r in all_invariants(cfg):
        d.add_invariant(_to_dashboard_invariant(r))

    return d


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    payload = _compute_payload(args)
    d = _build_dashboard(args, payload)
    out = d.write(
        html_path=args.html_out,
        json_path=args.json_out,
        invariants_path=args.invariants_out,
        txt_path=args.summary_out,
    )
    for k in ("html", "json", "invariants", "summary"):
        if k in out:
            print(out[k])

    failed = [i for i in d.evaluate_invariants() if not i["passed"]]
    if failed:
        names = ", ".join(i["name"] for i in failed)
        print(f"FAILED INVARIANTS: {names}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
