"""Registry-backed schematic and dashboard figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from gnn.concordance import BERNOULLI_SYMBOL_MAP
from gnn.parser import parse_gnn_file
from manuscript.sheaf.counts import structural_counts
from ontology.bindings import load_section_ontology
from simulation.tmaze_model import TMazeSpec
from .figure_helpers import save_styled_figure, styled_figure, style_grid
from .lean_boundary import load_lean_boundary_rows


def _load_invariant_blocks(project_root: Path) -> list[tuple[str, str, bool]]:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, bool]] = []
    for name, passed in sorted((payload.get("invariants") or {}).items()):
        rows.append(("analytical", str(name), bool(passed)))
    for name, passed in sorted((payload.get("simulation") or {}).items()):
        rows.append(("simulation", str(name), bool(passed)))
    return rows


def figure_invariant_dashboard(project_root: Path) -> Path:
    root = project_root.resolve()
    rows = _load_invariant_blocks(root)
    if not rows:
        raise FileNotFoundError("missing invariant rows in output/reports/invariants.json")
    labels = [f"{domain}: {name}" for domain, name, _ in rows]
    values = [1.0 if passed else 0.0 for _, _, passed in rows]
    with styled_figure(root, "invariant_dashboard") as (style, out):
        colors = [style.color("pass") if passed else style.color("fail") for _, _, passed in rows]
        fig_h = max(3.5, 0.28 * len(rows) + 1.2)
        fig, ax = plt.subplots(figsize=(8.5, fig_h))
        y_pos = np.arange(len(rows))
        ax.barh(y_pos, values, color=colors, height=0.65)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlim(0, 1.15)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["fail", "pass"])
        ax.set_xlabel("Invariant status")
        ax.set_title("Analytical and simulation invariant dashboard")
        for idx, (_, _, passed) in enumerate(rows):
            ax.text(
                1.02,
                idx,
                "PASS" if passed else "FAIL",
                va="center",
                fontsize=7,
                color=style.color("primary"),
            )
        style_grid(ax, style)
        ax.grid(axis="x", alpha=0.25)
        save_styled_figure(fig, out, style)
    return out


def figure_tmaze_schematic(project_root: Path) -> Path:
    root = project_root.resolve()
    spec = TMazeSpec()
    with styled_figure(root, "tmaze_schematic") as (style, out):
        fig, ax = plt.subplots(figsize=(6.5, 3.8))
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
            ax.text(center[0], center[1], label, ha="center", va="center", fontsize=8)
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
            fontsize=8,
            color=style.color("muted"),
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
    root = project_root.resolve()
    counts = structural_counts(root)
    pipeline_labels = _load_pipeline_track_labels(root)
    sheaf_labels = _load_sheaf_track_labels(root)
    scientific = [
        "Analytical oracle (Bernoulli–Ising)",
        "pymdp T-maze harness",
        "Sheaf composition contract",
    ]
    # Scale the canvas to the tallest column so no row runs off the axes or
    # collides with the footer, no matter how many gates/fragments exist.
    row_height = 0.42
    max_rows = max(len(scientific), len(pipeline_labels), len(sheaf_labels))
    top_y = 0.6  # space reserved above for column titles
    footer_y = 0.45  # space reserved below for the summary footer
    body_height = max_rows * row_height
    ymax = top_y + body_height + footer_y
    fig_h = max(5.5, ymax * 0.9)
    with styled_figure(root, "multi_track_architecture") as (style, out):
        fig, ax = plt.subplots(figsize=(10, fig_h))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, ymax)
        ax.axis("off")
        title_y = ymax - top_y / 2
        first_row_y = ymax - top_y

        def draw_column(x: float, title: str, items: list[str], width: float = 2.2) -> None:
            ax.text(x + width / 2, title_y, title, ha="center", va="bottom", fontsize=10, fontweight="bold")
            for idx, label in enumerate(items):
                y = first_row_y - idx * row_height
                patch = FancyBboxPatch(
                    (x, y - 0.16),
                    width,
                    0.32,
                    boxstyle="round,pad=0.02",
                    linewidth=1,
                    edgecolor=style.color("grid"),
                    facecolor=style.color("panel_bg"),
                )
                ax.add_patch(patch)
                ax.text(x + 0.08, y, label, va="center", fontsize=7)

        draw_column(0.4, "Scientific tracks (3)", scientific, width=2.6)
        draw_column(3.5, f"Pipeline gates ({len(pipeline_labels)})", pipeline_labels, width=2.5)
        draw_column(
            6.6,
            f"Sheaf fragment types ({counts['sheaf_track_count']})",
            sheaf_labels,
            width=2.8,
        )
        # Inter-column flow arrows centred in the body band.
        band_center = first_row_y - body_height / 2
        for offset in (-row_height, 0.0, row_height):
            y = band_center + offset
            ax.annotate(
                "",
                xy=(3.4, y),
                xytext=(3.0, y),
                arrowprops=dict(arrowstyle="-|>", color=style.color("muted")),
            )
            ax.annotate(
                "",
                xy=(6.5, y),
                xytext=(6.1, y),
                arrowprops=dict(arrowstyle="-|>", color=style.color("muted")),
            )
        ax.text(
            5.0,
            footer_y / 2,
            (
                f"{counts['imrad_manifest_rows']} manifest rows · "
                f"{counts['coverage_present']} present / {counts['coverage_bound']} bound"
            ),
            ha="center",
            fontsize=8,
            color=style.color("muted"),
        )
        ax.set_title("Multi-track architecture: science → gates → sheaf fragments")
        save_styled_figure(fig, out, style)
    return out


def figure_lean_boundary_status(project_root: Path) -> Path:
    root = project_root.resolve()
    rows = load_lean_boundary_rows(root)
    if not rows:
        raise FileNotFoundError("no Lean boundary modules under lean/TemplateActiveInference/")
    table_data = [[row.module, row.kind, row.name, row.status] for row in rows]
    with styled_figure(root, "lean_boundary_status") as (style, out):
        fig_h = max(2.8, 0.35 * len(rows) + 1.0)
        fig, ax = plt.subplots(figsize=(8.5, fig_h))
        ax.axis("off")
        table = ax.table(
            cellText=table_data,
            colLabels=["Module", "Kind", "Name", "Status"],
            loc="center",
            cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.35)
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
        fig, ax = plt.subplots(figsize=(9, fig_h))
        ax.set_xlim(0, 10)
        ax.set_ylim(-0.5, len(pairs))
        ax.axis("off")
        ax.text(1.2, len(pairs) - 0.1, "Analytical symbol", fontweight="bold", fontsize=9)
        ax.text(4.0, len(pairs) - 0.1, "GNN variable", fontweight="bold", fontsize=9)
        ax.text(7.0, len(pairs) - 0.1, "Ontology term", fontweight="bold", fontsize=9)
        for idx, (symbol, var, onto) in enumerate(pairs):
            y = len(pairs) - idx - 1
            ax.text(1.2, y, symbol, fontsize=8, va="center")
            ax.text(4.0, y, var, fontsize=8, va="center", color=style.color("secondary"))
            ax.text(7.0, y, onto, fontsize=8, va="center", color=style.color("accent"))
            ax.annotate(
                "",
                xy=(3.6, y),
                xytext=(2.0, y),
                arrowprops=dict(arrowstyle="-", color=style.color("grid")),
            )
            ax.annotate(
                "",
                xy=(6.6, y),
                xytext=(4.8, y),
                arrowprops=dict(arrowstyle="-", color=style.color("grid")),
            )
        ax.set_title(f"GNN ↔ ontology concordance ({model.version})")
        save_styled_figure(fig, out, style)
    return out
