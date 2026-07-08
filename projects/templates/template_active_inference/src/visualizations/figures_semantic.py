"""Semantic, release, and contract-map publication figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from .figure_helpers import (
    configure_axis,
    draw_arrow,
    draw_column_headers,
    load_json_artifact,
    save_styled_figure,
    text_box,
    wrap_text,
)
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def figure_semantic_gluing_graph(project_root: Path) -> Path:
    """Process figure semantic gluing graph."""
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
                fontsize=style.text_size("matrix_label"),
            )
            text_box(
                ax,
                artifact_x,
                y,
                rel.replace("output/", ""),
                style,
                width=30,
                edge_role="secondary",
                fontsize=style.text_size("matrix_label"),
            )
            text_box(
                ax,
                consumer_x,
                y,
                consumers,
                style,
                width=28,
                edge_role="accent",
                facecolor="#f8fafc",
                fontsize=style.text_size("matrix_label"),
            )
            draw_arrow(ax, producer_x + 0.25, artifact_x - 0.025, y, style)
            draw_arrow(ax, artifact_x + 0.28, consumer_x - 0.025, y, style)
        ax.text(
            0.03,
            0.045,
            f"{produced_count}/{len(selected)} selected artifacts produced by configured analysis; rows feed sheaf restrictions.",
            fontsize=style.text_size("source_note"),
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
            text_box(ax, columns[1], y, proof_label, style, width=24, edge_role="secondary")
            text_box(ax, columns[2], y, witness_label, style, width=24, edge_role="accent", facecolor="#f8fafc")
            draw_arrow(ax, columns[0] + 0.24, columns[1] - 0.03, y, style)
            draw_arrow(ax, columns[1] + 0.24, columns[2] - 0.03, y, style)
        linked_count = sum(1 for row in rows if row.get("linked") is True)
        ax.text(
            0.04,
            0.045,
            f"{linked_count}/{len(rows)} displayed theorem rows linked; witnesses come from generated JSON evidence.",
            fontsize=style.text_size("source_note"),
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
            range(len(perturbations)),
            [wrap_text(label.replace("_", " "), 14) for label in perturbations],
            fontsize=style.text_size("matrix_label"),
        )
        ax.set_yticks(
            range(len(topologies)),
            [wrap_text(label, 18) for label in topologies],
            fontsize=style.text_size("tick"),
        )
        configure_axis(ax, style, title="Causal-ablation sensitivity", xlabel="Perturbation", ylabel="Toy topology")
        threshold = float(matrix.max()) * 0.55 if matrix.size else 0.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                color = "white" if matrix[i, j] >= threshold else "#111827"
                ax.text(
                    j,
                    i,
                    f"{matrix[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=style.text_size("matrix_label"),
                )
        cbar = fig.colorbar(image, ax=ax, shrink=0.86)
        cbar.set_label("|effect|")
        max_effect = float(matrix.max()) if matrix.size else 0.0
        ax.text(
            0.0,
            -0.22,
            f"{len(rows)} source rows; max absolute effect {max_effect:.3f}.",
            transform=ax.transAxes,
            fontsize=style.text_size("source_note"),
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
        fig, ax = plt.subplots(figsize=(12.4, fig_h))
        ax.axis("off")
        columns = [0.025, 0.225, 0.405, 0.59, 0.785]
        headers = ["Citation", "Locator", "Scope boundary", "Method role", "Evidence artifact"]
        draw_column_headers(ax, columns, headers, style, y=0.95)
        y_positions = np.linspace(0.86, 0.12, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
            connected = row.get("connected") is True
            artifact = str(row.get("artifact", "")).replace("output/", "")
            boundary_status = "guarded" if row.get("claim_boundary_scope_guarded") else "unguarded"
            citation_status = "cited in manuscript" if row.get("cited_in_manuscript") else "citation missing"
            labels = [
                wrap_text(f"@{row.get('citation_key', '')}", 22),
                wrap_text(f"{row.get('source_locator_kind', '')}\n{citation_status}", 20),
                wrap_text(f"{boundary_status}\n{str(row.get('source_family', '')).replace('_', ' ')}", 22),
                wrap_text(str(row.get("method_role", "")).replace("_", " "), 23),
                wrap_text(artifact, 30),
            ]
            for x, label in zip(columns, labels, strict=True):
                text_box(
                    ax,
                    x,
                    y,
                    label,
                    style,
                    width=30,
                    edge_role="pass" if connected else "fail",
                    fontsize=style.text_size("matrix_label"),
                )
            for left, right in zip(columns, columns[1:], strict=False):
                draw_arrow(ax, left + 0.145, right - 0.025, y, style)
        summary = (
            f"{matrix.get('source_count', 0)} sources, "
            f"{matrix.get('method_role_count', 0)} method roles, "
            f"connected={matrix.get('all_sources_connected')}; "
            f"rederived={matrix.get('all_rows_rederived')}"
        )
        ax.text(0.03, 0.04, summary, fontsize=style.text_size("source_note"), color=style.color("muted"))
        ax.set_title("Scholarship source map with citation and scope guards", loc="left", pad=16)
        save_styled_figure(fig, out, style)
    return out


def figure_security_posture_map(project_root: Path) -> Path:
    """Render the local security posture controls and evidence bindings."""
    root = project_root.resolve()
    style = load_figure_style(root)
    audit_path = root / "output" / "reports" / "security_posture_audit.json"
    if not audit_path.is_file():
        from roadmap_tracks.security import write_security_posture_audit

        write_security_posture_audit(root)
    audit = load_json_artifact(root, "output/reports/security_posture_audit.json")
    rows = audit.get("rows") or []
    if not rows:
        raise FileNotFoundError("missing rows in output/reports/security_posture_audit.json")
    columns = [
        ("evidence_present", "Evidence"),
        ("validator_bound", "Validator"),
        ("negative_control_declared", "Negative"),
        ("deferred_scoped", "Scoped"),
        ("control_ok", "OK"),
    ]
    matrix = np.array([[1 if row.get(key) else 0 for key, _ in columns] for row in rows], dtype=int)
    out = figure_output_path(root, "security_posture_map")
    with apply_style(style):
        fig_h = max(5.8, 0.48 * len(rows) + 1.8)
        fig, (label_ax, matrix_ax) = plt.subplots(
            1,
            2,
            figsize=(13.8, fig_h),
            gridspec_kw={"width_ratios": [2.25, 1.0], "wspace": 0.08},
        )
        label_ax.axis("off")
        y_positions = np.linspace(0.88, 0.12, len(rows))
        draw_column_headers(label_ax, [0.02, 0.46, 0.74], ["Control", "Pillar", "Evidence path"], style, y=0.96)
        for y, row in zip(y_positions, rows, strict=True):
            edge_role = "pass" if row.get("control_ok") else "fail"
            text_box(
                label_ax,
                0.02,
                y,
                wrap_text(
                    f"{str(row.get('control_id', '')).replace('_', ' ')}\n{row.get('status', '')}",
                    26,
                ),
                style,
                width=28,
                edge_role=edge_role,
                fontsize=style.text_size("matrix_label"),
            )
            text_box(
                label_ax,
                0.46,
                y,
                wrap_text(str(row.get("pillar", "")).replace("_", " "), 20),
                style,
                width=22,
                edge_role="secondary",
                fontsize=style.text_size("matrix_label"),
            )
            evidence = ", ".join(str(value).replace("output/", "") for value in row.get("evidence_artifacts") or [])
            text_box(
                label_ax,
                0.72,
                y,
                wrap_text(evidence, 31),
                style,
                width=33,
                edge_role="accent",
                fontsize=style.text_size("matrix_label_dense"),
            )
        matrix_ax.imshow(
            matrix,
            cmap=ListedColormap([style.color("fail"), style.color("pass")]),
            vmin=0,
            vmax=1,
            aspect="auto",
        )
        matrix_ax.set_xticks(np.arange(len(columns)))
        matrix_ax.set_xticklabels(
            [label for _, label in columns],
            rotation=45,
            ha="right",
            fontsize=style.text_size("matrix_label"),
        )
        matrix_ax.set_yticks(np.arange(len(rows)))
        matrix_ax.set_yticklabels([])
        matrix_ax.tick_params(axis="y", length=0)
        matrix_ax.set_title("Security proof obligations", fontsize=style.text_size("subtitle"))
        matrix_ax.set_xticks(np.arange(-0.5, matrix.shape[1], 1), minor=True)
        matrix_ax.set_yticks(np.arange(-0.5, matrix.shape[0], 1), minor=True)
        matrix_ax.grid(
            which="minor",
            color=style.color("grid"),
            linestyle="-",
            linewidth=style.layout_value("matrix_grid_width", 0.35),
        )
        matrix_ax.tick_params(which="minor", bottom=False, left=False)
        fig.suptitle(
            (
                f"Security posture map: {audit.get('control_count', len(rows))} controls; "
                f"enforced={audit.get('enforced_count', 0)}, deferred={audit.get('deferred_count', 0)}, "
                f"secret findings={audit.get('secret_finding_count', 0)}"
            ),
            fontsize=style.text_size("title"),
            y=0.99,
        )
        fig.text(
            0.5,
            0.015,
            "Generated from output/reports/security_posture_audit.json; deferred controls are scoped, not claimed as production coverage.",
            ha="center",
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out
