"""Registry-backed schematic and dashboard figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from gnn.concordance import BERNOULLI_SYMBOL_MAP
from gnn.parser import parse_gnn_file
from manuscript.sheaf.counts import structural_counts
from ontology.bindings import load_section_ontology
from simulation.tmaze_model import TMazeSpec
from .figure_helpers import (
    configure_axis,
    draw_arrow,
    draw_column_headers,
    load_json_artifact,
    save_styled_figure,
    styled_figure,
    text_box,
    wrap_text,
)
from .lean_boundary import load_lean_boundary_rows


def _load_invariant_blocks(project_root: Path) -> list[tuple[str, str, bool]]:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        return []
    payload = load_json_artifact(project_root, "output/reports/invariants.json")
    rows: list[tuple[str, str, bool]] = []
    for name, passed in sorted((payload.get("invariants") or {}).items()):
        rows.append(("analytical", str(name), bool(passed)))
    for name, passed in sorted((payload.get("simulation") or {}).items()):
        rows.append(("simulation", str(name), bool(passed)))
    return rows


def figure_invariant_dashboard(project_root: Path) -> Path:
    """Process figure invariant dashboard."""
    root = project_root.resolve()
    rows = _load_invariant_blocks(root)
    if not rows:
        raise FileNotFoundError("missing invariant rows in output/reports/invariants.json")
    labels = [wrap_text(f"{domain}: {name}", 42) for domain, name, _ in rows]
    values = [1.0 if passed else 0.0 for _, _, passed in rows]
    with styled_figure(root, "invariant_dashboard") as (style, out):
        colors = [style.color("pass") if passed else style.color("fail") for _, _, passed in rows]
        fig_h = max(3.8, 0.34 * len(rows) + 1.3)
        fig, ax = plt.subplots(figsize=(8.8, fig_h))
        y_pos = np.arange(len(rows))
        ax.barh(y_pos, values, color=colors, height=0.65)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=style.text_size("tick"))
        ax.set_xlim(0, 1.15)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["fail", "pass"])
        configure_axis(
            ax,
            style,
            title=f"Analytical and simulation invariant dashboard ({sum(values):.0f}/{len(values)} pass)",
            xlabel="Invariant status",
        )
        for idx, (_, _, passed) in enumerate(rows):
            ax.text(
                1.02,
                idx,
                "PASS" if passed else "FAIL",
                va="center",
                fontsize=style.text_size("annotation"),
                color=style.color("primary"),
            )
        ax.grid(axis="x", alpha=0.25)
        ax.text(
            0.0,
            -0.16,
            "Merged from output/reports/invariants.json; row labels preserve source domain.",
            transform=ax.transAxes,
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_tmaze_schematic(project_root: Path) -> Path:
    """Process figure tmaze schematic."""
    root = project_root.resolve()
    spec = TMazeSpec()
    with styled_figure(root, "tmaze_schematic") as (style, out):
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-0.5, 1.8)
        ax.axis("off")
        start = (0.0, 0.5)
        goal = (2.0, 0.5)
        for center, label, color in (
            (start, f"start (s=0)\n{spec.num_states} states", style.color("secondary")),
            (goal, "goal (s=1)\nobs match state", style.color("accent")),
        ):
            box = FancyBboxPatch(
                (center[0] - 0.45, center[1] - 0.35),
                0.9,
                0.7,
                boxstyle="round,pad=0.05",
                linewidth=1.5,
                edgecolor=color,
                facecolor="white",
            )
            ax.add_patch(box)
            ax.text(center[0], center[1], label, ha="center", va="center", fontsize=style.text_size("annotation"))
        arrow = FancyArrowPatch(
            start,
            goal,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=2,
            color=style.color("primary"),
        )
        ax.add_patch(arrow)
        ax.text(
            1.0,
            0.85,
            f"policy_len={spec.policy_len}, actions={spec.num_actions}, obs={spec.num_obs}",
            ha="center",
            fontsize=style.text_size("annotation"),
            color=style.color("muted"),
        )
        obs_box = FancyBboxPatch(
            (0.35, -0.32),
            1.3,
            0.45,
            boxstyle="round,pad=0.05",
            linewidth=1,
            edgecolor=style.color("grid"),
            facecolor=style.color("panel_bg"),
        )
        ax.add_patch(obs_box)
        ax.text(
            1.0,
            -0.10,
            "finite toy: observations equal latent state; no stochastic sampling",
            ha="center",
            va="center",
            fontsize=style.text_size("source_note"),
            color=style.color("primary"),
        )
        ax.set_title("Minimal T-maze POMDP schematic")
        save_styled_figure(fig, out, style)
    return out


def _load_pipeline_track_labels(project_root: Path) -> list[str]:
    path = project_root / "tracks.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return [str(track.get("label") or track.get("id")) for track in tracks if track.get("required", True)]


def _load_sheaf_track_labels(project_root: Path) -> list[str]:
    path = project_root / "manuscript" / "sheaf" / "tracks.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or {}
    ordered = sorted(tracks.items(), key=lambda item: int((item[1] or {}).get("order", 0)))
    return [str((meta or {}).get("label") or track_id) for track_id, meta in ordered]


def figure_multi_track_architecture(project_root: Path) -> Path:
    """Process figure multi track architecture."""
    root = project_root.resolve()
    counts = structural_counts(root)
    pipeline_labels = _load_pipeline_track_labels(root)
    sheaf_labels = _load_sheaf_track_labels(root)
    with styled_figure(root, "multi_track_architecture") as (style, out):
        fig, ax = plt.subplots(figsize=(11.8, 7.4))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 7)
        ax.axis("off")

        def chunks(items: list[str], size: int) -> list[list[str]]:
            """Process chunks."""
            return [items[index : index + size] for index in range(0, len(items), size)]

        def draw_group_column(x: float, title: str, groups: list[tuple[str, list[str]]], width: float = 2.55) -> None:
            """Process draw group column."""
            ax.text(
                x + width / 2,
                6.45,
                title,
                ha="center",
                va="bottom",
                fontsize=style.text_size("header"),
                fontweight="bold",
            )
            for idx, (group_title, items) in enumerate(groups):
                y = 5.88 - idx * 0.86
                body = "\n".join(wrap_text(item, 24) for item in items[:2])
                if len(items) > 2:
                    body = f"{body}\n+{len(items) - 2} more"
                label = f"{group_title} ({len(items)})\n{body}"
                patch = FancyBboxPatch(
                    (x, y - 0.34),
                    width,
                    0.68,
                    boxstyle="round,pad=0.04",
                    linewidth=1,
                    edgecolor=style.color("grid"),
                    facecolor=style.color("panel_bg"),
                )
                ax.add_patch(patch)
                ax.text(x + 0.08, y, label, va="center", fontsize=style.text_size("matrix_label"), linespacing=1.05)

        scientific = [
            "Analytical oracle (Bernoulli–Ising)",
            "pymdp T-maze harness",
            "Sheaf composition contract",
        ]
        pipeline_groups = [(f"Gate group {idx + 1}", group) for idx, group in enumerate(chunks(pipeline_labels, 5))]
        sheaf_groups = [(f"Fragment group {idx + 1}", group) for idx, group in enumerate(chunks(sheaf_labels, 6))]
        draw_group_column(0.35, "Scientific tracks (3)", [("Model lanes", scientific)], width=2.5)
        draw_group_column(3.45, f"Pipeline gates ({len(pipeline_labels)})", pipeline_groups, width=2.55)
        draw_group_column(6.75, f"Sheaf fragments ({counts['sheaf_track_count']})", sheaf_groups, width=2.75)
        for y in (3.0, 3.8, 4.6):
            draw_arrow(ax, 2.95, 3.35, y, style)
            draw_arrow(ax, 6.15, 6.65, y, style)
        ax.text(
            5.0,
            0.42,
            (
                f"{counts['imrad_manifest_rows']} manifest rows · "
                f"{counts['coverage_present']} present / {counts['coverage_bound']} bound"
            ),
            ha="center",
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        ax.set_title("Multi-track architecture: science to gates to sheaf fragments")
        save_styled_figure(fig, out, style)
    return out


def figure_track_lane_promotion_map(project_root: Path) -> Path:
    """Render the pipeline-track promotion obligations and sheaf-lane bindings."""
    root = project_root.resolve()
    try:
        matrix = load_json_artifact(root, "output/data/track_lane_matrix.json")
    except FileNotFoundError:
        from roadmap_tracks.sheaf_tracks import build_track_lane_matrix

        matrix = build_track_lane_matrix(root)
    rows = matrix.get("rows") or []
    if not rows:
        raise FileNotFoundError("missing rows in output/data/track_lane_matrix.json")
    requirement_columns = [
        ("producer", "Producer"),
        ("artifact", "Artifact"),
        ("manuscript_consumer", "Manuscript"),
        ("typed_claim_evidence", "Claim"),
        ("semantic_restriction", "Semantic"),
        ("validation_gate", "Gate"),
        ("negative_control", "Negative"),
    ]
    sheaf_tracks = sorted({str(track) for row in rows for track in row.get("sheaf_tracks") or []})
    requirement_values = np.array(
        [
            [1 if (row.get("promotion_requirements") or {}).get(key) else 0 for key, _ in requirement_columns]
            for row in rows
        ],
        dtype=int,
    )
    sheaf_values = np.array(
        [[1 if track in set(row.get("sheaf_tracks") or []) else 0 for track in sheaf_tracks] for row in rows],
        dtype=int,
    )
    row_labels = [wrap_text(row.get("track_id", ""), 18) for row in rows]
    with styled_figure(root, "track_lane_promotion_map") as (style, out):
        fig_h = max(7.8, 0.36 * len(rows) + 2.4)
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(15.4, fig_h),
            gridspec_kw={"width_ratios": [1.05, 2.3], "wspace": 0.05},
        )
        req_ax, lane_ax = axes
        req_ax.imshow(
            requirement_values,
            cmap=ListedColormap([style.color("fail"), style.color("pass")]),
            vmin=0,
            vmax=1,
            aspect="auto",
        )
        req_ax.set_xticks(np.arange(len(requirement_columns)))
        req_ax.set_xticklabels(
            [label for _, label in requirement_columns],
            rotation=45,
            ha="right",
            fontsize=style.text_size("matrix_label"),
        )
        req_ax.set_yticks(np.arange(len(row_labels)))
        req_ax.set_yticklabels(row_labels, fontsize=style.text_size("matrix_label_dense"))
        req_ax.set_title("Promotion obligations", fontsize=style.text_size("subtitle"))

        lane_ax.imshow(
            sheaf_values,
            cmap=ListedColormap(["#ffffff", style.color("secondary")]),
            vmin=0,
            vmax=1,
            aspect="auto",
        )
        lane_ax.set_xticks(np.arange(len(sheaf_tracks)))
        lane_ax.set_xticklabels(
            [wrap_text(track, 10) for track in sheaf_tracks],
            rotation=90,
            ha="center",
            fontsize=style.text_size("matrix_label_dense"),
        )
        lane_ax.set_yticks(np.arange(len(row_labels)))
        lane_ax.set_yticklabels([])
        lane_ax.set_title("Sheaf lane bindings", fontsize=style.text_size("subtitle"))
        for ax in (req_ax, lane_ax):
            ax.set_xticks(np.arange(-0.5, ax.images[0].get_array().shape[1], 1), minor=True)
            ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
            ax.grid(
                which="minor",
                color=style.color("grid"),
                linestyle="-",
                linewidth=style.layout_value("matrix_grid_width", 0.35),
            )
            ax.tick_params(which="minor", bottom=False, left=False)
        fig.suptitle(
            (
                f"Track-lane promotion map: {matrix.get('row_count', len(rows))} pipeline rows; "
                f"complete={matrix.get('all_pipeline_tracks_complete')}"
            ),
            fontsize=style.text_size("title"),
            y=0.99,
        )
        fig.text(
            0.5,
            0.012,
            "Generated from output/data/track_lane_matrix.json and the Lean promotion-proof boundary.",
            ha="center",
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_artifact_contract_map(project_root: Path) -> Path:
    """Render artifact-level producer, validator, freshness, and copy-parity obligations."""
    root = project_root.resolve()
    try:
        index = load_json_artifact(root, "output/data/artifact_contract_index.json")
    except FileNotFoundError:
        from roadmap_tracks.sheaf_tracks import build_artifact_contract_index

        index = build_artifact_contract_index(root)
    rows = index.get("rows") or []
    if not rows:
        raise FileNotFoundError("missing rows in output/data/artifact_contract_index.json")
    columns = [
        ("producer_configured", "Producer"),
        ("source_exists", "Source"),
        ("claim_bound_or_exempt", "Claim"),
        ("validation_bound", "Gate"),
        ("negative_bound", "Negative"),
        ("source_hash_fresh", "Fresh"),
        ("copied_parity_ok", "Copy"),
        ("contract_complete", "Complete"),
    ]
    matrix = np.array(
        [
            [
                1
                if (
                    ((not row.get("claim_required")) or bool(row.get("claim_ids")))
                    if key == "claim_bound_or_exempt"
                    else bool(row.get("validation_gates"))
                    if key == "validation_bound"
                    else bool(row.get("negative_control"))
                    if key == "negative_bound"
                    else row.get(key)
                )
                else 0
                for key, _ in columns
            ]
            for row in rows
        ],
        dtype=int,
    )
    labels = []
    for row in rows:
        label = str(row.get("artifact", "")).replace("output/", "")
        labels.append(label if len(label) <= 46 else f"...{label[-43:]}")
    with styled_figure(root, "artifact_contract_map") as (style, out):
        fig_h = max(10.0, 0.24 * len(rows) + 2.6)
        fig, matrix_ax = plt.subplots(figsize=(14.4, fig_h))
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
        matrix_ax.set_yticklabels(labels, fontsize=style.text_size("matrix_label_dense"))
        matrix_ax.tick_params(axis="y", pad=2, length=0)
        for tick, row in zip(matrix_ax.get_yticklabels(), rows, strict=True):
            tick.set_color(style.color("pass") if row.get("contract_complete") else style.color("fail"))
        matrix_ax.set_title("Artifacts x contract obligations", fontsize=style.text_size("subtitle"))
        matrix_ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
        matrix_ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
        matrix_ax.grid(
            which="minor",
            color=style.color("grid"),
            linestyle="-",
            linewidth=style.layout_value("matrix_grid_width", 0.35),
        )
        matrix_ax.tick_params(which="minor", bottom=False, left=False)
        fig.suptitle(
            (
                f"Artifact contract map: {index.get('row_count', len(rows))} artifact rows; "
                f"complete={index.get('all_rows_complete')}; "
                f"copy parity={index.get('all_copied_parity_complete')}"
            ),
            fontsize=style.text_size("title"),
            y=0.995,
        )
        fig.text(
            0.5,
            0.01,
            "Generated from output/data/artifact_contract_index.json; cycle rows are marked in JSON rather than hidden.",
            ha="center",
            fontsize=style.text_size("source_note"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_lean_boundary_status(project_root: Path) -> Path:
    """Process figure lean boundary status."""
    root = project_root.resolve()
    rows = load_lean_boundary_rows(root)
    if not rows:
        raise FileNotFoundError("no Lean boundary modules under lean/TemplateActiveInference/")
    table_data = [[wrap_text(row.module, 22), row.kind, wrap_text(row.name, 28), row.status] for row in rows]
    with styled_figure(root, "lean_boundary_status") as (style, out):
        fig_h = max(2.8, 0.35 * len(rows) + 1.0)
        fig, ax = plt.subplots(figsize=(9.2, fig_h))
        ax.axis("off")
        table = ax.table(
            cellText=table_data,
            colLabels=["Module", "Kind", "Name", "Status"],
            loc="center",
            cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(style.text_size("table_cell"))
        table.scale(1, 1.42)
        for (row_idx, col_idx), cell in table.get_celld().items():
            if row_idx == 0:
                cell.set_facecolor(style.color("header_bg"))
                continue
            if col_idx == 3:
                status = table_data[row_idx - 1][3]
                cell.set_facecolor(style.color("proved") if status == "proved" else style.color("sorry"))
        ax.set_title("Lean formalization boundary status", pad=12)
        save_styled_figure(fig, out, style)
    return out


def figure_gnn_ontology_concordance(project_root: Path) -> Path:
    """Process figure gnn ontology concordance."""
    root = project_root.resolve()
    gnn_path = root / "gnn" / "bernoulli_toy.gnn.md"
    ontology_path = root / "manuscript" / "sections" / "imrad" / "methods_analytical" / "ontology.yaml"
    model = parse_gnn_file(gnn_path)
    section_ontology = load_section_ontology(ontology_path)
    pairs: list[tuple[str, str, str]] = []
    for symbol, var in BERNOULLI_SYMBOL_MAP.items():
        if var not in model.variables:
            continue
        onto = model.ontology.get(var) or section_ontology.get(var, "—")
        pairs.append((symbol, var, onto))
    if not pairs:
        raise ValueError("no GNN ↔ ontology pairs to plot")
    with styled_figure(root, "gnn_ontology_concordance") as (style, out):
        fig_h = max(3.5, 0.45 * len(pairs) + 1.0)
        fig, ax = plt.subplots(figsize=(9.4, fig_h))
        ax.set_xlim(0, 10)
        ax.set_ylim(-0.5, len(pairs))
        ax.axis("off")
        draw_column_headers(
            ax,
            [1.2, 4.0, 7.0],
            ["Analytical symbol", "GNN variable", "Ontology term"],
            style,
            y=len(pairs) - 0.1,
        )
        for idx, (symbol, var, onto) in enumerate(pairs):
            y = len(pairs) - idx - 1
            text_box(ax, 1.2, y, symbol, style, width=16, edge_role="grid")
            text_box(ax, 4.0, y, var, style, width=20, edge_role="secondary")
            text_box(ax, 7.0, y, onto, style, width=22, edge_role="accent")
            draw_arrow(ax, 2.0, 3.6, y, style)
            draw_arrow(ax, 4.8, 6.6, y, style)
        ax.set_title(f"GNN ↔ ontology concordance ({model.version})")
        save_styled_figure(fig, out, style)
    return out
