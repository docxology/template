"""Publication figures for analytical and pymdp tracks."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from .figure_helpers import save_styled_figure, style_grid
from .figure_registry import figure_output_path, load_figure_registry
from .figure_style import FigureStyleConfig, apply_style, load_figure_style
from .figures_diagrams import (
    figure_gnn_ontology_concordance,
    figure_invariant_dashboard,
    figure_lean_boundary_status,
    figure_multi_track_architecture,
    figure_tmaze_schematic,
)
from .figures_sheaf import figure_sheaf_coverage_heatmap, figure_sheaf_layers_overview


def _read_sweep(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = read_parameter_sweep(path)
    lambdas = [row["lambda"] for row in rows]
    closed = [row["closed_form_mi"] for row in rows]
    empirical = [row["empirical_mi"] for row in rows]
    return lambdas, closed, empirical


def _style_discrete_y(ax, style: FigureStyleConfig) -> None:
    style_grid(ax, style)
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
            label="exact recompute",
            color=style.color("secondary"),
            linewidth=2,
        )
        ax_main.set_xlabel(r"Coupling strength $\lambda$")
        ax_main.set_ylabel("Mutual information (nats)")
        ax_main.set_title("Bernoulli–Ising MI sweep")
        style_grid(ax_main, style)
        ax_main.legend(frameon=False, fontsize=8)
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        ax_resid.plot(lambdas, residuals, color=style.color("accent"), linewidth=1.5)
        ax_resid.set_xlabel(r"$\lambda$")
        ax_resid.set_ylabel("residual")
        ax_resid.set_title("recompute − closed", fontsize=9)
        style_grid(ax_resid, style)
        save_styled_figure(fig, out, style)
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
        style_grid(ax, style)
        save_styled_figure(fig, out, style)
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
        save_styled_figure(fig, out, style)
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
        ax.set_xlabel(r"Coupling strength $\lambda$")
        ax.set_ylabel("Free energy (nats)")
        ax.set_title("Free energy against entangled prior")
        style_grid(ax, style)
        ax.legend(frameon=False, fontsize=8)
        save_styled_figure(fig, out, style)
    return out


def _gluing_rows_from_edges(graph: dict, *, top_n: int = 14) -> list[dict]:
    """Derive the highest-fan-out artifact rows from the real dependency edges.

    Reads ``graph["edges"]`` (not a hardcoded artifact list): the producer comes
    from the ``produces`` edge, consumers from ``consumed_by`` edges, and gates
    from ``validated_by`` edges. Artifacts are ranked by real fan-out degree
    (consumers + gates) so the figure reflects — and changes with — the actual
    topology. Ordering is fully deterministic: degree desc, then path asc.
    """
    edges = graph.get("edges") or []
    producer_of: dict[str, str] = {}
    consumers_of: dict[str, list[str]] = {}
    gates_of: dict[str, list[str]] = {}
    for edge in edges:
        kind = edge.get("kind")
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if kind == "produces":
            producer_of[target] = source
        elif kind == "consumed_by":
            consumers_of.setdefault(source, []).append(target)
        elif kind == "validated_by":
            gates_of.setdefault(source, []).append(target)
    artifacts = sorted(set(producer_of) | set(consumers_of) | set(gates_of))
    rows: list[dict] = []
    for rel in artifacts:
        consumers = sorted(set(consumers_of.get(rel, [])))
        gates = sorted(set(gates_of.get(rel, [])))
        rows.append(
            {
                "artifact": rel,
                "producer": producer_of.get(rel, "?"),
                "consumers": consumers,
                "gates": gates,
                "fan_out": len(consumers) + len(gates),
            }
        )
    rows.sort(key=lambda row: (-row["fan_out"], row["artifact"]))
    return rows[:top_n]


def figure_semantic_gluing_graph(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    graph = build_validation_dependency_graph(root)
    artifacts = graph.get("artifacts") or {}
    rows = _gluing_rows_from_edges(graph)
    out = figure_output_path(root, "semantic_gluing_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(10.4, 6.0))
        ax.axis("off")
        producer_x, artifact_x, consumer_x = 0.04, 0.40, 0.74
        y_positions = np.linspace(0.86, 0.10, max(1, len(rows)))
        ax.text(producer_x, 0.96, "Producer script", weight="bold", color=style.color("primary"))
        ax.text(artifact_x, 0.96, "Evidence artifact", weight="bold", color=style.color("primary"))
        ax.text(consumer_x, 0.96, "Consumers / gates (fan-out)", weight="bold", color=style.color("primary"))
        for y, row in zip(y_positions, rows, strict=False):
            rel = str(row["artifact"])
            producer = str(row["producer"])
            targets = list(row["consumers"]) + [f"[{gate}]" for gate in row["gates"]]
            consumer_label = ", ".join(targets) if targets else "—"
            if len(consumer_label) > 46:
                consumer_label = consumer_label[:43] + "…"
            ok = bool(artifacts.get(rel, {}).get("produced_by_configured_analysis"))
            box_color = style.color("pass") if ok else style.color("fail")
            ax.text(
                producer_x,
                y,
                producer,
                fontsize=7.5,
                va="center",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="#f8fafc", edgecolor=box_color),
            )
            ax.text(
                artifact_x,
                y,
                rel.replace("output/", ""),
                fontsize=7.5,
                va="center",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                consumer_x,
                y,
                f"{consumer_label}  (×{row['fan_out']})",
                fontsize=7.5,
                va="center",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            ax.annotate("", xy=(artifact_x - 0.02, y), xytext=(producer_x + 0.23, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(consumer_x - 0.02, y), xytext=(artifact_x + 0.27, y), arrowprops={"arrowstyle": "->"})
        ax.set_title(
            f"Semantic sheaf gluing dependency graph (top {len(rows)} by fan-out of {len(artifacts)} artifacts)",
            loc="left",
            pad=16,
        )
        save_styled_figure(fig, out, style)
    return out


def figure_theorem_traceability_graph(project_root: Path) -> Path:
    """Render theorem → proof dependency → witness links from generated JSON rows."""
    root = project_root.resolve()
    style = load_figure_style(root)
    theorem_path = root / "output" / "data" / "theorem_traceability_matrix.json"
    dependency_path = root / "output" / "data" / "proof_dependency_graph.json"
    if not theorem_path.is_file() or not dependency_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    theorem = json.loads(theorem_path.read_text(encoding="utf-8"))
    dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
    rows = (theorem.get("rows") or [])[:6]
    edges = dependency.get("edges") or []
    edge_count_by_theorem = {
        row.get("theorem", ""): sum(1 for edge in edges if edge.get("source") == row.get("theorem")) for row in rows
    }
    out = figure_output_path(root, "theorem_traceability_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.2, 4.8))
        ax.axis("off")
        columns = [0.05, 0.42, 0.78]
        headers = ["Lean theorem", "Proof dependency rows", "Finite witnesses"]
        for x, header in zip(columns, headers, strict=True):
            ax.text(x, 0.94, header, weight="bold", color=style.color("primary"), fontsize=10)
        y_positions = np.linspace(0.82, 0.14, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
            theorem_id = str(row.get("theorem", ""))
            theorem_words = theorem_id.split("_")
            theorem_label = "\n".join(
                " ".join(theorem_words[index : index + 3]) for index in range(0, len(theorem_words), 3)
            )
            witness_count = len(row.get("model_witnesses") or [])
            linked = row.get("linked") is True
            edge_color = style.color("pass") if linked else style.color("fail")
            proof_label = f"{edge_count_by_theorem.get(theorem_id, 0)} dependency edges"
            witness_label = f"{witness_count} finite witnesses"
            ax.text(
                columns[0],
                y,
                theorem_label,
                fontsize=7.5,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=edge_color),
            )
            ax.text(
                columns[1],
                y,
                proof_label,
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                columns[2],
                y,
                witness_label,
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            ax.annotate("", xy=(columns[1] - 0.03, y), xytext=(columns[0] + 0.24, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(columns[2] - 0.03, y), xytext=(columns[1] + 0.24, y), arrowprops={"arrowstyle": "->"})
        ax.set_title("Theorem traceability graph", loc="left", pad=16)
        save_styled_figure(fig, out, style)
    return out


def figure_causal_ablation_heatmap(project_root: Path) -> Path:
    """Render source-backed causal-ablation effects as topology × perturbation heatmap."""
    root = project_root.resolve()
    style = load_figure_style(root)
    report_path = root / "output" / "reports" / "ablation_sensitivity_report.json"
    if not report_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = report.get("rows") or []
    topologies = sorted({str(row.get("topology")) for row in rows if row.get("topology")})
    perturbations = sorted({str(row.get("perturbation")) for row in rows if row.get("perturbation")})
    matrix = np.zeros((len(topologies), len(perturbations)))
    for i, topology in enumerate(topologies):
        for j, perturbation in enumerate(perturbations):
            effects = [
                abs(float(row.get("effect", 0.0) or 0.0))
                for row in rows
                if row.get("topology") == topology and row.get("perturbation") == perturbation
            ]
            matrix[i, j] = max(effects) if effects else 0.0
    out = figure_output_path(root, "causal_ablation_heatmap")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        image = ax.imshow(matrix, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(perturbations)), [label.replace("_", "\n") for label in perturbations], fontsize=8)
        ax.set_yticks(range(len(topologies)), topologies, fontsize=9)
        ax.set_xlabel("Perturbation")
        ax.set_ylabel("Toy topology")
        ax.set_title("Causal-ablation sensitivity")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
        cbar = fig.colorbar(image, ax=ax, shrink=0.86)
        cbar.set_label("|effect|")
        save_styled_figure(fig, out, style)
    return out


def figure_scholarship_source_map(project_root: Path) -> Path:
    """Render bibliography-to-method-source bindings from the scholarship matrix."""
    root = project_root.resolve()
    style = load_figure_style(root)
    matrix_path = root / "output" / "data" / "scholarship_source_matrix.json"
    if not matrix_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    rows = matrix.get("rows") or []
    out = figure_output_path(root, "scholarship_source_map")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(10.4, 5.8))
        ax.axis("off")
        columns = [0.03, 0.28, 0.55, 0.82]
        headers = ["Citation", "Source family", "Method role", "Evidence artifact"]
        for x, header in zip(columns, headers, strict=True):
            ax.text(x, 0.95, header, weight="bold", color=style.color("primary"), fontsize=9)
        y_positions = np.linspace(0.86, 0.12, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
            connected = row.get("connected") is True
            edge_color = style.color("pass") if connected else style.color("fail")
            artifact = str(row.get("artifact", "")).replace("output/", "")
            if len(artifact) > 32:
                artifact = artifact[:29] + "..."
            labels = [
                f"@{row.get('citation_key', '')}",
                str(row.get("source_family", "")).replace("_", "\n"),
                str(row.get("method_role", "")).replace("_", "\n"),
                artifact,
            ]
            for x, label in zip(columns, labels, strict=True):
                ax.text(
                    x,
                    y,
                    label,
                    fontsize=7.4,
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor=edge_color),
                )
            ax.annotate("", xy=(columns[1] - 0.025, y), xytext=(columns[0] + 0.13, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(columns[2] - 0.025, y), xytext=(columns[1] + 0.17, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(columns[3] - 0.025, y), xytext=(columns[2] + 0.17, y), arrowprops={"arrowstyle": "->"})
        summary = (
            f"{matrix.get('source_count', 0)} sources, "
            f"{matrix.get('method_role_count', 0)} method roles, "
            f"connected={matrix.get('all_sources_connected')}"
        )
        ax.text(0.03, 0.04, summary, fontsize=8.5, color=style.color("muted"))
        ax.set_title("Scholarship source map", loc="left", pad=16)
        save_styled_figure(fig, out, style)
    return out


def figure_efe_decomposition(project_root: Path) -> Path:
    """Expected Free Energy term decomposition across T-maze policies.

    Left panel: ``G(pi) = risk + ambiguity`` as a stacked bar per policy, with the
    EFE-minimising policy marked. Right panel: the equal-and-opposite
    ``G(pi) = -(pragmatic_value + epistemic_value)`` decomposition. Computed in
    closed form (no sampling) so the figure is byte-deterministic.
    """
    from simulation.efe_decomposition import decompose_all_policies
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    result = decompose_all_policies(build_tmaze_generative_model())
    rows = result["rows"]
    labels = ["".join(str(a) for a in row["policy"]) for row in rows]
    risk = [float(row["risk"]) for row in rows]
    ambiguity = [float(row["ambiguity"]) for row in rows]
    pragmatic = [float(row["pragmatic_value"]) for row in rows]
    epistemic = [float(row["epistemic_value"]) for row in rows]
    totals = [r + a for r, a in zip(risk, ambiguity)]
    best_label = "".join(str(a) for a in result["efe_minimizing_policy"])
    best_idx = labels.index(best_label)
    x = np.arange(len(labels))

    out = figure_output_path(root, "efe_decomposition")
    with apply_style(style):
        fig, (ax_g, ax_pe) = plt.subplots(1, 2, figsize=(9.5, 4))
        ax_g.bar(x, risk, color=style.color("secondary"), label="risk (pragmatic deviation)")
        ax_g.bar(x, ambiguity, bottom=risk, color=style.color("accent"), label="ambiguity (epistemic)")
        ax_g.scatter(
            [x[best_idx]],
            [totals[best_idx]],
            color=style.color("fail"),
            zorder=3,
            s=45,
            label=f"min G at policy {best_label}",
        )
        ax_g.set_xticks(x)
        ax_g.set_xticklabels(labels)
        ax_g.set_xlabel("Policy (action sequence)")
        ax_g.set_ylabel("Expected free energy (nats)")
        ax_g.set_title(r"$G(\pi)$ = risk + ambiguity")
        style_grid(ax_g, style)
        ax_g.legend(frameon=False, fontsize=7)

        width = 0.4
        ax_pe.bar(x - width / 2, pragmatic, width, color=style.color("primary"), label="pragmatic value")
        ax_pe.bar(x + width / 2, epistemic, width, color=style.color("muted"), label="epistemic value")
        ax_pe.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_pe.set_xticks(x)
        ax_pe.set_xticklabels(labels)
        ax_pe.set_xlabel("Policy (action sequence)")
        ax_pe.set_ylabel("Value (nats)")
        ax_pe.set_title(r"$G(\pi)$ = -(pragmatic + epistemic)")
        style_grid(ax_pe, style)
        ax_pe.legend(frameon=False, fontsize=7)

        save_styled_figure(fig, out, style)
    return out


def figure_precision_sweep(project_root: Path) -> Path:
    """Policy-posterior sharpening as precision (gamma) increases.

    Left axis: Shannon entropy ``H[q]`` of ``q(pi) = softmax(-gamma G)`` vs gamma,
    with the ``ln(|optimal set|)`` saturation floor marked. Right axis: the EFE
    optimal-set mass vs gamma, with the precision at which it crosses the
    selection threshold marked. Computed in closed form (no sampling), so the
    figure is byte-deterministic.
    """
    from simulation.precision_sweep import sweep_precision
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    result = sweep_precision(build_tmaze_generative_model())
    rows = result["rows"]
    gammas = [float(r["gamma"]) for r in rows]
    entropy = [float(r["entropy"]) for r in rows]
    opt_mass = [float(r["optimal_set_mass"]) for r in rows]
    floor = float(result["entropy_floor"])
    threshold = float(result["selection_mass_threshold"])
    gamma_det = result["gamma_deterministic_selection"]

    out = figure_output_path(root, "precision_sweep")
    with apply_style(style):
        fig, ax_h = plt.subplots(figsize=(7.5, 4))
        ax_h.plot(gammas, entropy, color=style.color("secondary"), marker="o", markersize=3, label="entropy H[q]")
        ax_h.axhline(
            floor,
            color=style.color("reference"),
            linewidth=0.9,
            linestyle="--",
            label=r"floor $\ln|\Pi^\star|$",
        )
        ax_h.set_xlabel(r"Precision $\gamma$ (inverse temperature)")
        ax_h.set_ylabel("Posterior entropy (nats)")
        ax_h.set_title(r"Precision sharpens the policy posterior $q(\pi)=\mathrm{softmax}(-\gamma G)$")
        style_grid(ax_h, style)

        ax_m = ax_h.twinx()
        ax_m.plot(gammas, opt_mass, color=style.color("accent"), marker="s", markersize=3, label="optimal-set mass")
        ax_m.axhline(threshold, color=style.color("muted"), linewidth=0.8, linestyle=":")
        ax_m.set_ylabel("EFE optimal-set mass")
        ax_m.set_ylim(0.0, 1.02)
        if gamma_det is not None:
            ax_m.scatter(
                [float(gamma_det)],
                [threshold],
                color=style.color("fail"),
                zorder=3,
                s=45,
                label=rf"mass $\geq$ {threshold:g} at $\gamma$={float(gamma_det):g}",
            )

        lines_h, labels_h = ax_h.get_legend_handles_labels()
        lines_m, labels_m = ax_m.get_legend_handles_labels()
        ax_h.legend(lines_h + lines_m, labels_h + labels_m, frameon=False, fontsize=7, loc="center right")

        save_styled_figure(fig, out, style)
    return out


def figure_cue_tmaze_advantage(project_root: Path) -> Path:
    """Epistemic necessity in the cue-then-reward T-maze.

    Left panel: cue information gain I(context; o_cue) > 0 and the measured
    behavioural advantage (epistemic vs greedy expected reward log-preference).
    Right panel: the documented flat-EFE blind spot -- decompose_policy_efe scores
    the cue-first and greedy policies identically, so the sophisticated evaluator
    is what makes epistemic value strictly necessary. Closed form (no sampling),
    byte-deterministic.
    """
    from simulation.cue_tmaze_model import compare_cue_vs_greedy

    root = project_root.resolve()
    style = load_figure_style(root)
    adv = compare_cue_vs_greedy()

    out = figure_output_path(root, "cue_tmaze_advantage")
    with apply_style(style):
        fig, (ax_adv, ax_flat) = plt.subplots(1, 2, figsize=(9.5, 4))

        adv_labels = ["cue info gain\nI(ctx;o)", "epistemic\nreward", "greedy\nreward"]
        adv_values = [
            adv.cue_information_gain,
            adv.epistemic_reward_log_pref,
            adv.greedy_reward_log_pref,
        ]
        adv_colors = [style.color("accent"), style.color("pass"), style.color("fail")]
        ax_adv.bar(np.arange(3), adv_values, color=adv_colors)
        ax_adv.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_adv.set_xticks(np.arange(3))
        ax_adv.set_xticklabels(adv_labels, fontsize=8)
        ax_adv.set_ylabel("Value (nats)")
        ax_adv.set_title(f"Cue is required: +{adv.behavioral_advantage:.2f} nat advantage", loc="left", fontsize=9)
        style_grid(ax_adv, style)

        flat_values = [adv.flat_efe_cue, adv.flat_efe_greedy]
        ax_flat.bar(
            ["cue-first\npolicy", "greedy\npolicy"],
            flat_values,
            color=[style.color("secondary"), style.color("muted")],
        )
        ax_flat.set_ylabel("Flat EFE $G(\\pi)$ (nats)")
        ax_flat.set_title(
            f"Flat EFE blind spot: {'identical' if adv.flat_efe_indistinguishable else 'differs'}",
            loc="left",
            fontsize=9,
        )
        style_grid(ax_flat, style)

        save_styled_figure(fig, out, style)
    return out


def figure_dirichlet_convergence(project_root: Path) -> Path:
    """KL(true A || learned A) versus Dirichlet update step (log-y).

    The deterministic Dirichlet likelihood-learning run drives the expected
    likelihood toward the true T-maze ``A``; the per-step KL falls monotonically
    toward zero. Computed in closed form (fixed expected-count stream, no
    sampling) so the figure is byte-deterministic.
    """
    from simulation.dirichlet_learning import CONVERGENCE_KL_ATOL, summarize_learning
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    summary = summarize_learning(build_tmaze_generative_model())
    kls = [float(v) for v in summary["kl_trajectory"]]
    steps = np.arange(len(kls))
    converge_step = int(summary["steps_to_converge"])

    out = figure_output_path(root, "dirichlet_convergence")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.semilogy(steps, kls, marker="o", color=style.color("primary"), linewidth=2, label="KL(true || learned)")
        ax.axhline(
            CONVERGENCE_KL_ATOL,
            color=style.color("reference"),
            linewidth=1,
            linestyle="--",
            label=f"convergence tol {CONVERGENCE_KL_ATOL:g}",
        )
        if converge_step < len(kls):
            ax.scatter(
                [steps[converge_step]],
                [kls[converge_step]],
                color=style.color("pass"),
                zorder=3,
                s=45,
                label=f"converged at step {converge_step}",
            )
        ax.set_xlabel("Dirichlet update step")
        ax.set_ylabel("KL to true likelihood (nats)")
        ax.set_title("Dirichlet likelihood learning converges to true A")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        style_grid(ax, style)
        ax.legend(frameon=False, fontsize=8)
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
    "theorem_traceability_graph": figure_theorem_traceability_graph,
    "causal_ablation_heatmap": figure_causal_ablation_heatmap,
    "scholarship_source_map": figure_scholarship_source_map,
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
