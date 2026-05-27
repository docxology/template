"""Publication figures for analytical and pymdp tracks."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from visualizations.figure_io import save_figure_png
from visualizations.figure_registry import figure_output_path, load_figure_registry
from visualizations.figure_style import FigureStyleConfig, apply_style, load_figure_style
from visualizations.figures_sheaf import figure_sheaf_coverage_heatmap, figure_sheaf_layers_overview


def _read_sweep(path: Path) -> tuple[list[float], list[float], list[float]]:
    lambdas: list[float] = []
    closed: list[float] = []
    empirical: list[float] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lambdas.append(float(row["lambda"]))
            closed.append(float(row["closed_form_mi"]))
            empirical.append(float(row["empirical_mi"]))
    return lambdas, closed, empirical


def _save_styled_figure(fig, path: Path, style: FigureStyleConfig) -> Path:
    fig.tight_layout()
    return save_figure_png(
        fig,
        path,
        dpi=style.dpi,
        facecolor="white",
        transparent=style.transparent,
    )


def _style_grid(ax, style: FigureStyleConfig) -> None:
    if style.grid:
        ax.grid(True, alpha=0.35, color=style.color("grid"))


def _style_discrete_y(ax, style: FigureStyleConfig) -> None:
    _style_grid(ax, style)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


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
            label="empirical",
            color=style.color("secondary"),
            linewidth=2,
        )
        ax_main.set_xlabel(r"Coupling strength $\lambda$")
        ax_main.set_ylabel("Mutual information (nats)")
        ax_main.set_title("Bernoulli–Ising MI sweep")
        _style_grid(ax_main, style)
        ax_main.legend(frameon=False, fontsize=8)
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        ax_resid.plot(lambdas, residuals, color=style.color("accent"), linewidth=1.5)
        ax_resid.set_xlabel(r"$\lambda$")
        ax_resid.set_ylabel("residual")
        ax_resid.set_title("MC − closed", fontsize=9)
        _style_grid(ax_resid, style)
        _save_styled_figure(fig, out, style)
    return out


def figure_si_belief_entropy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    steps_data = trace.get("steps") or []
    entropies = [float(step.get("belief_entropy", 0.0)) for step in steps_data]
    out = figure_output_path(root, "si_belief_entropy_curve")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7, 3.2))
        xs = list(range(len(entropies)))
        ax.plot(xs, entropies, linewidth=2, color=style.color("primary"))
        ax.fill_between(xs, entropies, step="pre", alpha=0.08, color=style.color("secondary"))
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Belief entropy (nats)")
        ax.set_title("T-maze belief entropy")
        _style_grid(ax, style)
        _save_styled_figure(fig, out, style)
    return out


def figure_si_obs_action_trace(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    observations = data.get("observations") or []
    actions = data.get("actions") or []
    out = figure_output_path(root, "si_obs_action_trace")
    with apply_style(style):
        fig, axes = plt.subplots(2, 1, figsize=(7, 4.2), sharex=True)
        obs_ax, act_ax = axes
        xs = list(range(len(observations)))
        obs_ax.step(xs, observations, where="post", linewidth=2, color=style.color("secondary"))
        obs_ax.set_ylabel("Observation")
        obs_ax.set_title("T-maze observation and action traces")
        _style_discrete_y(obs_ax, style)
        act_ax.step(xs, actions, where="post", linewidth=2, color=style.color("primary"))
        act_ax.set_xlabel("Timestep")
        act_ax.set_ylabel("Action")
        _style_discrete_y(act_ax, style)
        _save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_actions(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    policy_len = data.get("policy_len", "?")
    out = figure_output_path(root, "si_tmaze_actions")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7, 3.2))
        steps = list(range(len(actions)))
        ax.step(steps, actions, where="post", linewidth=2, color=style.color("primary"))
        ax.fill_between(steps, actions, step="post", alpha=0.08, color=style.color("secondary"))
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Action index")
        ax.set_title(f"T-maze SI actions (policy_len={policy_len})")
        _style_discrete_y(ax, style)
        _save_styled_figure(fig, out, style)
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
        ax.set_xlabel(r"Coupling strength $\lambda$")
        ax.set_ylabel("Free energy (nats)")
        ax.set_title("Free energy against entangled prior")
        _style_grid(ax, style)
        ax.legend(frameon=False, fontsize=8)
        _save_styled_figure(fig, out, style)
    return out


FIGURE_GENERATORS: dict[str, Callable[[Path], Path]] = {
    "ising_mi_curve": figure_ising_mi_curve,
    "free_energy_curve": figure_free_energy_curve,
    "si_belief_entropy_curve": figure_si_belief_entropy_curve,
    "si_obs_action_trace": figure_si_obs_action_trace,
    "si_tmaze_actions": figure_si_tmaze_actions,
    "sheaf_layers_overview": figure_sheaf_layers_overview,
    "sheaf_coverage_heatmap": figure_sheaf_coverage_heatmap,
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
    from orchestration.coverage_pipeline import run_coverage_pipeline

    json_path, heatmap_path, _page_path = run_coverage_pipeline(project_root)
    paths = [
        json_path,
        figure_ising_mi_curve(project_root),
        figure_free_energy_curve(project_root),
        figure_si_belief_entropy_curve(project_root),
        figure_si_obs_action_trace(project_root),
        figure_si_tmaze_actions(project_root),
        figure_sheaf_layers_overview(project_root),
        heatmap_path,
    ]
    return [p for p in paths if p is not None]
