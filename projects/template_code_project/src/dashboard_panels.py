"""Plotly panel assembly for the interactive dashboard."""

from __future__ import annotations

from infrastructure.reporting.interactive_dashboard import InteractiveDashboard, Invariant, Panel

from .dashboard_payload import to_diagonal_A
from .invariants import OptimizerSweepConfig, all_invariants
from .project_paths import _DEFAULT_ROOT as PROJECT_ROOT

REPO_ROOT = PROJECT_ROOT.parent.parent


def to_dashboard_invariant(r) -> Invariant:
    return Invariant(
        name=r.name,
        actual=r.actual,
        expected=r.expected,
        tol=r.tol,
        kind=r.kind,
        description=r.description,
    )


def build_dashboard(args, payload: dict) -> InteractiveDashboard:
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
                    "y": [max(dist, 1e-15) for dist in sw["final_dist"]],
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

    cfg = OptimizerSweepConfig(
        step_sizes=tuple(args.step_sizes),
        A=tuple(tuple(row) for row in to_diagonal_A(args.A)),
        b=tuple(float(v) for v in args.b),
        initial_point=tuple(float(v) for v in args.x0),
        max_iterations=int(args.max_iter),
        tolerance=float(args.tol),
    )
    for r in all_invariants(cfg):
        d.add_invariant(to_dashboard_invariant(r))

    return d


__all__ = ["REPO_ROOT", "build_dashboard", "to_dashboard_invariant"]
