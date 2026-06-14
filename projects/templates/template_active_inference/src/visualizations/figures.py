"""Publication figures for analytical and pymdp tracks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from .figure_helpers import (
    add_note,
    configure_axis,
    load_json_artifact,
    save_styled_figure,
    style_grid,
)
from .figure_registry import figure_output_path, load_figure_registry
from .figure_style import FigureStyleConfig, apply_style, load_figure_style
from .figures_diagrams import (
    figure_artifact_contract_map,
    figure_gnn_ontology_concordance,
    figure_invariant_dashboard,
    figure_lean_boundary_status,
    figure_multi_track_architecture,
    figure_track_lane_promotion_map,
    figure_tmaze_schematic,
)
from .figures_sheaf import figure_sheaf_coverage_heatmap, figure_sheaf_layers_overview
from .figures_semantic import (
    figure_causal_ablation_heatmap,
    figure_scholarship_source_map,
    figure_security_posture_map,
    figure_semantic_gluing_graph,
    figure_theorem_traceability_graph,
)
from .figures_simulation import (
    figure_cue_tmaze_advantage,
    figure_dirichlet_convergence,
    figure_efe_decomposition,
    figure_precision_sweep,
)


def _read_sweep(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = read_parameter_sweep(path)
    lambdas = [row["lambda"] for row in rows]
    closed = [row["closed_form_mi"] for row in rows]
    empirical = [row["empirical_mi"] for row in rows]
    return lambdas, closed, empirical


def _style_discrete_y(ax, style: FigureStyleConfig) -> None:
    style_grid(ax, style)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def _apply_artifact_note(ax, artifact: str, style: FigureStyleConfig, *, x: float = 0.02, y: float = 0.96) -> None:
    add_note(ax, f"Source artifact: {artifact}", style, x=x, y=y, width=38)


def figure_ising_mi_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    sweep = root / "output" / "data" / "parameter_sweep.csv"
    lambdas, closed, empirical = _read_sweep(sweep)
    out = figure_output_path(root, "ising_mi_curve")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [2.2, 1]})
        ax_main, ax_resid = axes
        ax_main.plot(lambdas, closed, label="closed form", color=style.color("primary"), linewidth=2)
        ax_main.plot(
            lambdas,
            empirical,
            "--",
            label="exact recompute",
            color=style.color("secondary"),
            linewidth=2,
        )
        configure_axis(
            ax_main,
            style,
            title="Bernoulli–Ising MI sweep",
            xlabel=r"Coupling strength $\lambda$",
            ylabel="Mutual information (nats)",
        )
        ax_main.legend(frameon=False, fontsize=style.text_size("legend"))
        max_idx = int(np.argmax(closed))
        ax_main.annotate(
            f"max {closed[max_idx]:.3f} nats",
            xy=(lambdas[max_idx], closed[max_idx]),
            xytext=(0.52, 0.18),
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "color": style.color("muted")},
            fontsize=style.text_size("annotation"),
        )
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        ax_resid.plot(lambdas, residuals, color=style.color("accent"), linewidth=1.5)
        configure_axis(
            ax_resid,
            style,
            title="recompute − closed",
            xlabel=r"$\lambda$",
            ylabel="residual",
            title_size=style.text_size("subtitle"),
        )
        ax_resid.text(
            0.05,
            0.93,
            f"max |resid|={max(abs(v) for v in residuals):.1e}",
            transform=ax_resid.transAxes,
            va="top",
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_belief_entropy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    trace = load_json_artifact(root, "output/data/si_tmaze_trace.json")
    steps_data = trace.get("steps") or []
    entropies = [float(step.get("belief_entropy", 0.0)) for step in steps_data]
    out = figure_output_path(root, "si_belief_entropy_curve")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7.4, 3.6))
        xs = list(range(len(entropies)))
        ax.plot(xs, entropies, linewidth=2.2, marker="o", markersize=5, color=style.color("primary"))
        ax.fill_between(xs, entropies, min(entropies) if entropies else 0.0, alpha=0.08, color=style.color("secondary"))
        if entropies:
            span = max(max(entropies) - min(entropies), 0.05)
            ax.set_ylim(min(entropies) - span * 0.35, max(entropies) + span * 0.35)
            ax.annotate(
                f"finite trace: {len(entropies)} steps",
                xy=(xs[-1], entropies[-1]),
                xytext=(0.58, 0.78),
                textcoords="axes fraction",
                arrowprops={"arrowstyle": "->", "color": style.color("muted")},
                fontsize=style.text_size("annotation"),
            )
        configure_axis(
            ax,
            style,
            title="T-maze belief entropy trace",
            xlabel="Timestep",
            ylabel="Belief entropy (nats)",
            integer_x=True,
        )
        _apply_artifact_note(ax, "output/data/si_tmaze_trace.json", style, x=0.04, y=0.18)
        save_styled_figure(fig, out, style)
    return out


def figure_si_obs_action_trace(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    data = load_json_artifact(root, "output/data/si_tmaze_summary.json")
    observations = data.get("observations") or []
    actions = data.get("actions") or []
    out = figure_output_path(root, "si_obs_action_trace")
    with apply_style(style):
        fig, axes = plt.subplots(2, 1, figsize=(7.4, 4.6), sharex=True)
        obs_ax, act_ax = axes
        xs = list(range(len(observations)))
        obs_ax.step(xs, observations, where="post", linewidth=2, color=style.color("secondary"))
        obs_ax.plot(xs, observations, "o", color=style.color("secondary"), markersize=4)
        obs_ax.set_ylabel("Observation")
        obs_ax.set_title("T-maze observation and action traces")
        _style_discrete_y(obs_ax, style)
        act_ax.step(xs, actions, where="post", linewidth=2, color=style.color("primary"))
        act_ax.plot(xs, actions, "o", color=style.color("primary"), markersize=4)
        configure_axis(act_ax, style, title="", xlabel="Timestep", ylabel="Action", integer_x=True, integer_y=True)
        _style_discrete_y(act_ax, style)
        goal = data.get("goal_reached", "--")
        add_note(
            obs_ax,
            f"Source: output/data/si_tmaze_summary.json; {len(xs)} samples; goal_reached={goal}",
            style,
            x=0.55,
            y=0.92,
            width=38,
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_actions(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    data = load_json_artifact(root, "output/data/si_tmaze_summary.json")
    actions = data.get("actions", [])
    policy_len = data.get("policy_len", "?")
    out = figure_output_path(root, "si_tmaze_actions")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7.4, 3.6))
        steps = list(range(len(actions)))
        ax.step(steps, actions, where="post", linewidth=2, color=style.color("primary"))
        ax.plot(steps, actions, "o", color=style.color("primary"), markersize=4)
        ax.fill_between(steps, actions, step="post", alpha=0.08, color=style.color("secondary"))
        configure_axis(
            ax,
            style,
            title=f"T-maze SI actions (policy_len={policy_len})",
            xlabel="Timestep",
            ylabel="Action index",
            integer_x=True,
            integer_y=True,
        )
        switches = sum(1 for left, right in zip(actions, actions[1:], strict=False) if left != right)
        add_note(
            ax,
            f"action switches: {switches}; saved summary drives manuscript statistics",
            style,
            x=0.04,
            y=0.86,
            width=36,
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_summary(project_root: Path) -> Path:
    """Deprecated alias for ``figure_si_tmaze_actions``."""
    return figure_si_tmaze_actions(project_root)


def figure_free_energy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from analytical.decomposition import free_energy_against_entangled_prior
    from analytical.bernoulli_toy import ising_coupling, ising_joint_posterior, symmetric_mean_field_prior

    hp_lambdas = lambda_grid(load_hyperparameters())
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    values = []
    for lam in hp_lambdas:
        q = ising_joint_posterior(float(lam))
        values.append(free_energy_against_entangled_prior(q, mf, g0, j, kc, gamma=1.0, lam=float(lam)))
    out = figure_output_path(root, "free_energy_curve")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(hp_lambdas, values, linewidth=2, color=style.color("primary"))
        min_idx = int(np.argmin(values))
        ax.scatter(
            [hp_lambdas[min_idx]],
            [values[min_idx]],
            color=style.color("accent"),
            s=40,
            zorder=3,
            label=f"min at λ={hp_lambdas[min_idx]:.2f}",
        )
        configure_axis(
            ax,
            style,
            title="Free energy against mean-field prior",
            xlabel=r"Coupling strength $\lambda$",
            ylabel="Free energy (nats)",
        )
        ax.legend(frameon=False, fontsize=style.text_size("legend"))
        add_note(ax, "Mean-field prior comparison: coupling raises F away from the independence point.", style)
        save_styled_figure(fig, out, style)
    return out


FIGURE_GENERATORS: dict[str, Callable[[Path], Path | None]] = {
    "efe_decomposition": figure_efe_decomposition,
    "precision_sweep": figure_precision_sweep,
    "cue_tmaze_advantage": figure_cue_tmaze_advantage,
    "dirichlet_convergence": figure_dirichlet_convergence,
    "ising_mi_curve": figure_ising_mi_curve,
    "free_energy_curve": figure_free_energy_curve,
    "si_belief_entropy_curve": figure_si_belief_entropy_curve,
    "si_obs_action_trace": figure_si_obs_action_trace,
    "si_tmaze_actions": figure_si_tmaze_actions,
    "sheaf_layers_overview": figure_sheaf_layers_overview,
    "sheaf_coverage_heatmap": figure_sheaf_coverage_heatmap,
    "invariant_dashboard": figure_invariant_dashboard,
    "tmaze_schematic": figure_tmaze_schematic,
    "multi_track_architecture": figure_multi_track_architecture,
    "lean_boundary_status": figure_lean_boundary_status,
    "gnn_ontology_concordance": figure_gnn_ontology_concordance,
    "semantic_gluing_graph": figure_semantic_gluing_graph,
    "track_lane_promotion_map": figure_track_lane_promotion_map,
    "artifact_contract_map": figure_artifact_contract_map,
    "theorem_traceability_graph": figure_theorem_traceability_graph,
    "causal_ablation_heatmap": figure_causal_ablation_heatmap,
    "scholarship_source_map": figure_scholarship_source_map,
    "security_posture_map": figure_security_posture_map,
}


def run_figure(figure_id: str, project_root: Path) -> Path:
    """Dispatch a registry figure id to its generator."""
    load_figure_registry(project_root)  # fail fast when registry missing
    try:
        generator = FIGURE_GENERATORS[figure_id]
    except KeyError as exc:
        raise KeyError(f"unknown figure id: {figure_id}") from exc
    result = generator(project_root)
    if result is None:
        raise RuntimeError(f"figure generator returned no path for {figure_id}")
    return result


def generate_all_figures(project_root: Path) -> list[Path]:
    from orchestration.coverage_pipeline import ensure_coverage_artifacts
    from .figure_registry import write_figure_registry_json

    json_path, _, page_path = ensure_coverage_artifacts(project_root, write_page=True)
    paths: list[Path] = [json_path]
    paths.extend(run_figure(figure_id, project_root) for figure_id in FIGURE_GENERATORS)
    paths.append(write_figure_registry_json(project_root))
    if page_path is not None:
        paths.append(page_path)
    return [path for path in paths if path is not None]
