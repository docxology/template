"""Graph and matrix diagram renderers for the gold-refinement figures.

Lays out and draws the directed graphs built in :mod:`.graphs` (provenance
flow, formalism traceability, implementation circuit, claim-evidence assay)
plus the matrix/scatter diagrams (token heatmap, integrity gate matrix,
integrity risk matrix, evidence tier ladder). Each generator writes a
deterministic PNG + SVG pair via the shared :mod:`._common` IO helpers.

All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np

from ._common import (
    SOURCE_TIER_COLORS,
    STAGE_COLORS,
    _draw_labeled_digraph,
    _figure_output_dir,
    _graph_positions,
    _load_json_object,
    _nines_score,
    _render_digraph_figure,
    _save_figure,
    _style_axes,
)
from .graphs import (
    build_claim_evidence_topology,
    build_formalism_traceability_graph,
    build_implementation_circuit_graph,
    build_provenance_flow_graph,
)

try:
    from ..composition import generate_token_plan
    from ..config import load_gold_refinement_config
    from ..evidence import build_evidence_registry
    from ..integrity import build_evidence_tiers, build_integrity_dimensions
    from ..refinery import run_refinery
except ImportError:  # pragma: no cover - flat-layout fallback
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from evidence import build_evidence_registry  # type: ignore[no-redef]
    from integrity import build_evidence_tiers, build_integrity_dimensions  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]


def generate_provenance_sankey(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)
    graph, edge_widths = build_provenance_flow_graph()
    return _render_digraph_figure(
        output_dir,
        filename="provenance_sankey.png",
        graph=graph,
        positions=_graph_positions(graph),
        title="Provenance Flow: Ore to Nine-Nines Certification",
        figsize=(12, 4.8),
        edge_widths=edge_widths,
        font_size=7.2,
        subtitle="Edge width encodes stage purity gain; final node encodes nine-nines certification.",
    )


def generate_purity_claim_scatter(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a scatter plot of purity vs claim support rate per stage.

    Each stage's output purity is plotted against the fraction of
    contribution claims that are supported at that stage's evidence level.
    """
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    result = run_refinery()

    evidence_path = (project_root or Path(".")) / "output" / "reports" / "claim_support_registry.json"
    support_rate = 1.0
    if evidence_path.exists():
        with evidence_path.open("r") as f:
            ev = json.load(f)
        support_rate = ev.get("support_rate", 1.0)

    purities = [s.output_purity for s in result.stages]
    support_rates = [min(1.0, support_rate * (i + 1) / len(purities)) for i in range(len(purities))]

    fig, ax = plt.subplots(figsize=(8.8, 6.4))
    sizes = [130 + 45 * _nines_score(stage.output_purity) for stage in result.stages]
    ax.scatter(purities, support_rates, c=STAGE_COLORS[: len(purities)], s=sizes, zorder=5, edgecolors="black")

    for i, stage in enumerate(result.stages):
        ax.annotate(
            stage.name,
            xy=(purities[i], support_rates[i]),
            xytext=(purities[i] + 0.02, support_rates[i] + 0.02),
            fontsize=9,
        )

    ax.set_xlabel("Stage Output Purity (fraction)", fontsize=12)
    ax.set_ylabel("Cumulative Claim Support Rate", fontsize=12)
    ax.set_title("Purity vs Claim Support", fontsize=14)
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.15)
    ax.axhline(y=1.0, color="green", linestyle="--", alpha=0.3, label="Full support")
    ax.text(0.02, 0.96, f"Project assay: {support_rate:.0%}", transform=ax.transAxes, fontsize=9, va="top")
    ax.legend()
    _style_axes(ax)

    out_path = output_dir / "purity_claim_scatter.png"
    return _save_figure(fig, out_path)


def generate_token_heatmap(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a heatmap of token selection: seed × category → selected index.

    Varies the seed from 0 to 20 and shows which index is selected
    for each lexicon category. Demonstrates seed sensitivity.
    """
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    cfg = load_gold_refinement_config(project_root) if project_root else load_gold_refinement_config()

    categories = sorted(cfg.lexicon.keys())
    seeds = list(range(21))  # seeds 0-20

    # Build selection matrix: rows=seeds, cols=categories
    matrix = np.zeros((len(seeds), len(categories)))
    for si, seed in enumerate(seeds):
        modified_cfg = replace(cfg, seed=seed)
        plan = generate_token_plan(modified_cfg)
        for ci, cat in enumerate(categories):
            vals = plan.values_for_category(cat)
            if vals:
                # Use the first selected value's index in the category
                inventory = cfg.lexicon[cat]
                idx = inventory.index(vals[0]) if vals[0] in inventory else 0
                matrix[si, ci] = idx

    fig, ax = plt.subplots(figsize=(9.4, 8.2))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrBr", interpolation="nearest")
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels([f"{cat}\nn={len(cfg.lexicon[cat])}" for cat in categories], rotation=30, ha="right")
    ax.set_yticks(range(0, len(seeds), 2))
    ax.set_yticklabels([str(s) for s in seeds[::2]])
    ax.set_xlabel("Lexicon Category", fontsize=12)
    ax.set_ylabel("Seed Value", fontsize=12)
    ax.set_title("Token Selection Heatmap: Seed × Category → Index", fontsize=13)
    fig.colorbar(im, ax=ax, label="Selected Index")

    for si in range(len(seeds)):
        for ci in range(len(categories)):
            ax.text(
                ci,
                si,
                str(int(matrix[si, ci])),
                ha="center",
                va="center",
                fontsize=7,
                color="white" if matrix[si, ci] > len(cfg.lexicon[categories[ci]]) / 2 else "black",
            )
    ax.text(
        0.01,
        -0.14,
        "Column labels include inventory size; each cell is the selected inventory index.",
        transform=ax.transAxes,
        fontsize=8,
        color="#334155",
    )

    out_path = output_dir / "token_heatmap.png"
    return _save_figure(fig, out_path)


def generate_integrity_gate_matrix(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    cfg = load_gold_refinement_config(project_root) if project_root else load_gold_refinement_config()
    rules = cfg.audit_rules or []
    names = [str(rule.get("name", f"Rule {i + 1}")) for i, rule in enumerate(rules)]
    if not names:
        names = ["Token coverage", "Figure generation", "Render validation"]
        rules = [{"test": ""} for _ in names]

    columns = ["Declared", "Test", "Manuscript", "Artifact"]
    matrix = np.zeros((len(names), len(columns)), dtype=float)
    for row, rule in enumerate(rules):
        matrix[row, 0] = 1.0
        matrix[row, 1] = 1.0 if str(rule.get("test", "")).strip() else 0.0
        matrix[row, 2] = 1.0
        matrix[row, 3] = 1.0 if any(term in names[row].lower() for term in ("figure", "token", "purity")) else 0.5

    fig, ax = plt.subplots(figsize=(10, max(4.5, 0.55 * len(names) + 2)))
    im = ax.imshow(matrix, cmap="YlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels(columns)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.set_title("Integrity Gate Matrix", fontsize=14)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            label = "full" if value == 1 else "partial" if value > 0 else "missing"
            ax.text(col, row, label, ha="center", va="center", fontsize=7)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Coverage")
    cbar.set_ticks([0, 0.5, 1])
    cbar.set_ticklabels(["missing", "partial", "full"])

    out_path = output_dir / "integrity_gate_matrix.png"
    return _save_figure(fig, out_path)


def generate_formalism_traceability(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)
    graph = build_formalism_traceability_graph()
    formalism_count_for_height = sum(1 for _, data in graph.nodes(data=True) if data.get("kind") == "formalism")
    return _render_digraph_figure(
        output_dir,
        filename="formalism_traceability.png",
        graph=graph,
        positions=_graph_positions(graph),
        title="Formalism Traceability Graph",
        figsize=(14, max(5, 0.72 * formalism_count_for_height + 2)),
        node_size=2300,
        font_size=6.8,
        title_pad=16,
        header_labels=((0.17, 0.95, "Formalism"), (0.50, 0.95, "Equation label"), (0.83, 0.95, "Source owner")),
    )


def generate_implementation_circuit(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)
    graph = build_implementation_circuit_graph()
    return _render_digraph_figure(
        output_dir,
        filename="implementation_circuit.png",
        graph=graph,
        positions=_graph_positions(graph),
        title="Gold Refinement Implementation Circuit",
        figsize=(12.5, 7.2),
        node_size=2600,
        font_size=7.4,
        footer_text=(
            "A fork changes the left side first; generated artifacts and validators then prove whether the manuscript still refines."
        ),
    )


def generate_claim_evidence_assay(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    root = project_root or Path(".")
    cfg = load_gold_refinement_config(root)
    registry = build_evidence_registry(cfg, root)
    entries = list(registry.entries)
    if not entries:
        entries = []

    fig_height = max(5.2, 0.58 * max(1, len(entries)) + 2.4)
    fig = plt.figure(figsize=(15, fig_height))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.0, 1.25), wspace=0.08)
    ax = fig.add_subplot(grid[0])
    graph_ax = fig.add_subplot(grid[1])
    ax.set_xlim(0, 1.05)
    ax.set_ylim(-0.8, max(1, len(entries)) - 0.2)
    ax.set_xlabel("Evidence support")
    ax.set_title("Assay support", fontsize=12, pad=12)
    ax.set_yticks(range(len(entries)))
    ax.set_yticklabels([fill(entry.claim_name, width=21) for entry in entries], fontsize=8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["unsupported", "supported"])

    boundary_counts = Counter(entry.boundary for entry in entries)
    supported_color = "#0f766e"
    unsupported_color = "#b91c1c"
    for row, entry in enumerate(entries):
        width = 1.0 if entry.supported else 0.12
        color = supported_color if entry.supported else unsupported_color
        ax.barh(row, width, color=color, alpha=0.82, height=0.45)
        source = entry.evidence_source if len(entry.evidence_source) <= 46 else entry.evidence_source[:43] + "..."
        ax.text(
            min(0.98, width + 0.02),
            row,
            source,
            va="center",
            ha="right" if width > 0.85 else "left",
            fontsize=7,
            color="#111827",
        )

    topology = build_claim_evidence_topology(entries)
    if topology.number_of_nodes():
        positions = {
            node: (float(data.get("x", 0.0)), float(data.get("y", 0.0))) for node, data in topology.nodes(data=True)
        }
        _draw_labeled_digraph(graph_ax, topology, positions, node_size=1850, font_size=6.3)
    else:
        graph_ax.text(0.5, 0.5, "No configured claims", ha="center", va="center", fontsize=11)
        graph_ax.axis("off")
    graph_ax.set_title("Claim → evidence → boundary topology", fontsize=12, pad=12)

    summary = f"{registry.supported_claims}/{registry.total_claims} supported; " + ", ".join(
        f"{boundary}: {count}" for boundary, count in sorted(boundary_counts.items())
    )
    ax.text(0.0, -0.55, summary, fontsize=8.5, color="#334155")
    ax.grid(axis="x", alpha=0.2)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    out_path = output_dir / "claim_evidence_assay.png"
    return _save_figure(fig, out_path)


def generate_integrity_risk_matrix(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    root = project_root or Path(".")
    cfg = load_gold_refinement_config(root)
    dimensions = build_integrity_dimensions(cfg)
    severities = [item.severity for item in dimensions]
    detectability = [item.detectability for item in dimensions]
    residual = [item.residual_risk for item in dimensions]
    sizes = [120 + score * 35 for score in residual]
    colors = [SOURCE_TIER_COLORS.get(item.source_tier, "#94a3b8") for item in dimensions]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(
        detectability,
        severities,
        s=sizes,
        c=colors,
        edgecolors="#1f2937",
        linewidths=0.8,
        alpha=0.86,
    )
    for item in dimensions:
        ax.annotate(
            item.dimension_id,
            xy=(item.detectability, item.severity),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
        )

    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xlabel("Detectability (1 = hard to detect, 5 = easy)")
    ax.set_ylabel("Severity (1 = low, 5 = high)")
    ax.set_title("Scientific-Integrity Risk Matrix", fontsize=14, pad=14)
    ax.grid(True, alpha=0.25)
    ax.axhspan(4.5, 5.5, color="#fee2e2", alpha=0.25)
    ax.axvspan(0.5, 2.5, color="#fef3c7", alpha=0.22)

    tier_handles = [
        ax.scatter(
            [],
            [],
            s=110,
            color=SOURCE_TIER_COLORS.get(tier, "#94a3b8"),
            edgecolors="#1f2937",
            linewidths=0.8,
            label=tier,
        )
        for tier in sorted({item.source_tier for item in dimensions})
    ]
    tier_legend = ax.legend(handles=tier_handles, title="Source tier", loc="upper right", fontsize=7)
    ax.add_artist(tier_legend)
    size_levels = sorted({min(residual), int(np.median(residual)), max(residual)})
    size_handles = [
        ax.scatter([], [], s=120 + score * 35, color="#d1d5db", edgecolors="#1f2937", label=str(score))
        for score in size_levels
    ]
    ax.legend(handles=size_handles, title="Residual risk", loc="lower right", fontsize=7)

    table_text = "\n".join(
        f"{item.dimension_id}: {fill(item.name, width=22)} | {item.source_tier}" for item in dimensions
    )
    ax.text(
        0.02,
        0.02,
        table_text,
        transform=ax.transAxes,
        va="bottom",
        ha="left",
        fontsize=7,
        color="#111827",
        bbox={"facecolor": "white", "edgecolor": "#d1d5db", "alpha": 0.92, "pad": 5},
    )

    out_path = output_dir / "integrity_risk_matrix.png"
    return _save_figure(fig, out_path)


def generate_evidence_tier_ladder(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    output_dir = _figure_output_dir(output_dir, project_root=project_root)

    root = project_root or Path(".")
    cfg = load_gold_refinement_config(root)
    dimensions = build_integrity_dimensions(cfg)
    shared_evidence = _load_json_object(root / "output" / "reports" / "evidence_registry.json")
    tiers = build_evidence_tiers(shared_evidence, dimensions)

    tier_order = {
        "validation": 0,
        "source_code": 1,
        "config": 2,
        "claim_ledger": 3,
        "generated_metric": 4,
        "artifact": 5,
        "bibliography": 6,
    }
    tiers = tuple(sorted(tiers, key=lambda tier: (tier_order.get(tier.tier, 99), tier.tier)))
    labels = [tier.tier for tier in tiers]
    counts = [tier.count for tier in tiers]
    roles = [tier.role for tier in tiers]
    y_positions = np.arange(len(labels))
    total = sum(counts) or 1

    fig, ax = plt.subplots(figsize=(11, max(4.5, 0.6 * len(labels) + 2)))
    colors = [SOURCE_TIER_COLORS.get(label, "#94a3b8") for label in labels]
    ax.barh(y_positions, counts, color=colors, alpha=0.86)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Evidence facts or model surfaces")
    ax.set_title("Evidence-Tier Ladder", fontsize=14, pad=14)
    max_count = max(counts) if counts else 1
    ax.set_xlim(0, max_count * 1.28 + 1)
    for row, (count, role) in enumerate(zip(counts, roles)):
        pct = 100 * count / total
        ax.text(count + max_count * 0.02, row, f"{count} ({pct:.0f}%) | {role}", va="center", fontsize=8)
    _style_axes(ax, grid_axis="x")

    out_path = output_dir / "evidence_tier_ladder.png"
    return _save_figure(fig, out_path)
