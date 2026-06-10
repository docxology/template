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
    add_value_labels,
    configure_axis,
    draw_arrow,
    draw_column_headers,
    load_json_artifact,
    save_styled_figure,
    style_grid,
    text_box,
    wrap_text,
)
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
        ax_main.legend(frameon=False, fontsize=8)
        max_idx = int(np.argmax(closed))
        ax_main.annotate(
            f"max {closed[max_idx]:.3f} nats",
            xy=(lambdas[max_idx], closed[max_idx]),
            xytext=(0.52, 0.18),
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "color": style.color("muted")},
            fontsize=8,
        )
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        ax_resid.plot(lambdas, residuals, color=style.color("accent"), linewidth=1.5)
        configure_axis(
            ax_resid, style, title="recompute − closed", xlabel=r"$\lambda$", ylabel="residual", title_size=9
        )
        ax_resid.text(
            0.05,
            0.93,
            f"max |resid|={max(abs(v) for v in residuals):.1e}",
            transform=ax_resid.transAxes,
            va="top",
            fontsize=8,
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
                fontsize=8,
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
        ax.legend(frameon=False, fontsize=8)
        add_note(ax, "Mean-field prior comparison: coupling raises F away from the independence point.", style)
        save_styled_figure(fig, out, style)
    return out


def figure_semantic_gluing_graph(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    graph = build_validation_dependency_graph(root)
    selected = [
        "output/data/sheaf_gluing_certificate.json",
        "output/data/sheaf_evidence_crosswalk.json",
        "output/data/validation_dependency_graph.json",
        "output/data/artifact_provenance.json",
        "output/reports/replay_matrix.json",
        "output/data/sensitivity_sweep.json",
        "output/data/uncertainty_summary.json",
        "output/data/toy_benchmark_matrix.json",
        "output/data/interop_roundtrip_report.json",
        "output/reports/model_checking_witnesses.json",
        "output/reports/adversarial_audit.json",
        "output/data/evidence_field_index.json",
        "output/reports/release_bundle_manifest.json",
        "output/data/theorem_traceability_matrix.json",
    ]
    artifacts = graph.get("artifacts") or {}
    out = figure_output_path(root, "semantic_gluing_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(10.2, 6.0))
        ax.axis("off")
        producer_x, artifact_x, consumer_x = 0.03, 0.38, 0.75
        y_positions = np.linspace(0.86, 0.13, len(selected))
        draw_column_headers(
            ax,
            [producer_x, artifact_x, consumer_x],
            ["Producer script", "Evidence artifact", "Consumer / gate"],
            style,
            y=0.955,
        )
        produced_count = 0
        for y, rel in zip(y_positions, selected, strict=True):
            record = artifacts.get(rel, {})
            producer = wrap_text(str(record.get("producer", "?")), 26)
            consumers = ", ".join(record.get("consumers") or record.get("validation_gates") or ["validate_outputs"])
            ok = bool(record.get("produced_by_configured_analysis"))
            produced_count += int(ok)
            text_box(
                ax,
                producer_x,
                y,
                producer,
                style,
                width=26,
                edge_role="pass" if ok else "fail",
                facecolor="#f8fafc",
                fontsize=7,
            )
            text_box(ax, artifact_x, y, rel.replace("output/", ""), style, width=30, edge_role="secondary", fontsize=7)
            text_box(ax, consumer_x, y, consumers, style, width=28, edge_role="accent", facecolor="#f8fafc", fontsize=7)
            draw_arrow(ax, producer_x + 0.25, artifact_x - 0.025, y, style)
            draw_arrow(ax, artifact_x + 0.28, consumer_x - 0.025, y, style)
        ax.text(
            0.03,
            0.045,
            f"{produced_count}/{len(selected)} selected artifacts produced by configured analysis; rows feed sheaf restrictions.",
            fontsize=8,
            color=style.color("muted"),
        )
        ax.set_title("Semantic sheaf gluing dependency graph", loc="left", pad=16)
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
    theorem = load_json_artifact(root, "output/data/theorem_traceability_matrix.json")
    dependency = load_json_artifact(root, "output/data/proof_dependency_graph.json")
    rows = (theorem.get("rows") or [])[:6]
    edges = dependency.get("edges") or []
    edge_count_by_theorem = {
        row.get("theorem", ""): sum(1 for edge in edges if edge.get("source") == row.get("theorem")) for row in rows
    }
    out = figure_output_path(root, "theorem_traceability_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.8, 5.2))
        ax.axis("off")
        columns = [0.04, 0.40, 0.75]
        headers = ["Lean theorem", "Proof dependency rows", "Finite witnesses"]
        draw_column_headers(ax, columns, headers, style)
        y_positions = np.linspace(0.82, 0.14, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
            theorem_id = str(row.get("theorem", ""))
            theorem_label = wrap_text(theorem_id.replace("_", " "), 30)
            witness_count = len(row.get("model_witnesses") or [])
            linked = row.get("linked") is True
            proof_label = f"{edge_count_by_theorem.get(theorem_id, 0)} dependency edges"
            witness_label = f"{witness_count} finite witnesses"
            text_box(
                ax,
                columns[0],
                y,
                theorem_label,
                style,
                width=30,
                edge_role="pass" if linked else "fail",
                facecolor="#f8fafc",
            )
            text_box(ax, columns[1], y, proof_label, style, width=24, edge_role="secondary", fontsize=8)
            text_box(
                ax, columns[2], y, witness_label, style, width=24, edge_role="accent", facecolor="#f8fafc", fontsize=8
            )
            draw_arrow(ax, columns[0] + 0.24, columns[1] - 0.03, y, style)
            draw_arrow(ax, columns[1] + 0.24, columns[2] - 0.03, y, style)
        linked_count = sum(1 for row in rows if row.get("linked") is True)
        ax.text(
            0.04,
            0.045,
            f"{linked_count}/{len(rows)} displayed theorem rows linked; witnesses come from generated JSON evidence.",
            fontsize=8,
            color=style.color("muted"),
        )
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
    report = load_json_artifact(root, "output/reports/ablation_sensitivity_report.json")
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
        fig, ax = plt.subplots(figsize=(8.8, 5.0))
        image = ax.imshow(matrix, cmap="magma", aspect="auto")
        ax.set_xticks(
            range(len(perturbations)), [wrap_text(label.replace("_", " "), 14) for label in perturbations], fontsize=8
        )
        ax.set_yticks(range(len(topologies)), [wrap_text(label, 18) for label in topologies], fontsize=9)
        configure_axis(ax, style, title="Causal-ablation sensitivity", xlabel="Perturbation", ylabel="Toy topology")
        threshold = float(matrix.max()) * 0.55 if matrix.size else 0.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                color = "white" if matrix[i, j] >= threshold else "#111827"
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color=color, fontsize=8)
        cbar = fig.colorbar(image, ax=ax, shrink=0.86)
        cbar.set_label("|effect|")
        max_effect = float(matrix.max()) if matrix.size else 0.0
        ax.text(
            0.0,
            -0.22,
            f"{len(rows)} source rows; max absolute effect {max_effect:.3f}.",
            transform=ax.transAxes,
            fontsize=8,
            color=style.color("muted"),
        )
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
    matrix = load_json_artifact(root, "output/data/scholarship_source_matrix.json")
    rows = matrix.get("rows") or []
    out = figure_output_path(root, "scholarship_source_map")
    with apply_style(style):
        fig_h = max(6.2, 0.42 * len(rows) + 1.6)
        fig, ax = plt.subplots(figsize=(11.2, fig_h))
        ax.axis("off")
        columns = [0.025, 0.27, 0.51, 0.76]
        headers = ["Citation", "Source family", "Method role", "Evidence artifact"]
        draw_column_headers(ax, columns, headers, style, y=0.95)
        y_positions = np.linspace(0.86, 0.12, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
            connected = row.get("connected") is True
            artifact = str(row.get("artifact", "")).replace("output/", "")
            labels = [
                wrap_text(f"@{row.get('citation_key', '')}", 22),
                wrap_text(str(row.get("source_family", "")).replace("_", " "), 22),
                wrap_text(str(row.get("method_role", "")).replace("_", " "), 23),
                wrap_text(artifact, 30),
            ]
            for x, label in zip(columns, labels, strict=True):
                text_box(ax, x, y, label, style, width=30, edge_role="pass" if connected else "fail", fontsize=7)
            draw_arrow(ax, columns[0] + 0.17, columns[1] - 0.025, y, style)
            draw_arrow(ax, columns[1] + 0.18, columns[2] - 0.025, y, style)
            draw_arrow(ax, columns[2] + 0.18, columns[3] - 0.025, y, style)
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
        configure_axis(
            ax_g,
            style,
            title=r"$G(\pi)$ = risk + ambiguity",
            xlabel="Policy (action sequence)",
            ylabel="Expected free energy (nats)",
        )
        for idx, total in enumerate(totals):
            ax_g.text(idx, total + 0.015, f"{total:.2f}", ha="center", va="bottom", fontsize=7.5)
        ax_g.legend(frameon=False, fontsize=7)

        width = 0.4
        ax_pe.bar(x - width / 2, pragmatic, width, color=style.color("primary"), label="pragmatic value")
        ax_pe.bar(x + width / 2, epistemic, width, color=style.color("muted"), label="epistemic value")
        ax_pe.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_pe.set_xticks(x)
        ax_pe.set_xticklabels(labels)
        configure_axis(
            ax_pe,
            style,
            title=r"$G(\pi)$ = -(pragmatic + epistemic)",
            xlabel="Policy (action sequence)",
            ylabel="Value (nats)",
        )
        ax_pe.legend(frameon=False, fontsize=7)
        add_note(ax_pe, f"identity residual <= {float(result['max_identity_residual']):.1e}", style, x=0.05, y=0.95)

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
        configure_axis(
            ax_h,
            style,
            title=r"Precision sharpens policy posterior $q(\pi)=\mathrm{softmax}(-\gamma G)$",
            xlabel=r"Precision $\gamma$ (inverse temperature)",
            ylabel="Posterior entropy (nats)",
        )

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
            ax_h.axvline(float(gamma_det), color=style.color("fail"), linewidth=0.8, linestyle=":")

        lines_h, labels_h = ax_h.get_legend_handles_labels()
        lines_m, labels_m = ax_m.get_legend_handles_labels()
        ax_h.legend(lines_h + lines_m, labels_h + labels_m, frameon=False, fontsize=7, loc="upper right")
        add_note(ax_h, f"{result['optimal_set_size']} tied optima create the entropy floor.", style, x=0.04, y=0.23)

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
        bars = ax_adv.bar(np.arange(3), adv_values, color=adv_colors)
        ax_adv.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_adv.set_xticks(np.arange(3))
        ax_adv.set_xticklabels(adv_labels, fontsize=8)
        configure_axis(
            ax_adv,
            style,
            title=f"Cue is required: +{adv.behavioral_advantage:.2f} nat advantage",
            ylabel="Value (nats)",
            title_loc="left",
            title_size=9,
        )
        add_value_labels(ax_adv, bars)

        flat_values = [adv.flat_efe_cue, adv.flat_efe_greedy]
        flat_bars = ax_flat.bar(
            ["cue-first\npolicy", "greedy\npolicy"],
            flat_values,
            color=[style.color("secondary"), style.color("muted")],
        )
        configure_axis(
            ax_flat,
            style,
            title=(f"Flat EFE blind spot: {'identical' if adv.flat_efe_indistinguishable else 'differs'}",),
            ylabel="Flat EFE $G(\\pi)$ (nats)",
            title_loc="left",
            title_size=9,
        )
        add_value_labels(ax_flat, flat_bars)

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
        configure_axis(
            ax,
            style,
            title="Dirichlet likelihood learning converges to true A",
            xlabel="Dirichlet update step",
            ylabel="KL to true likelihood (nats)",
            integer_x=True,
        )
        ax.legend(frameon=False, fontsize=8)
        add_note(ax, f"final KL={kls[-1]:.2e}; deterministic expected-count stream", style, x=0.48, y=0.95, width=36)
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
