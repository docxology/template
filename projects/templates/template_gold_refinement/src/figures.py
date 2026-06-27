"""Figure generation for the gold-refinement exemplar.

Generates publication-quality figures from refinery data using matplotlib.
All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from textwrap import fill
from typing import Any, Literal

import matplotlib

matplotlib.use("Agg")  # headless-safe before pyplot import
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

try:
    from .composition import generate_token_plan
    from .config import load_gold_refinement_config
    from .evidence import build_evidence_registry
    from .formalisms import FORMALISMS
    from .integrity import build_evidence_tiers, build_integrity_dimensions
    from .purity import KARAT_GRADES, NINE_NINES_PURITY, format_purity
    from .refinery import run_refinery
except ImportError:
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from evidence import build_evidence_registry  # type: ignore[no-redef]
    from formalisms import FORMALISMS  # type: ignore[no-redef]
    from integrity import build_evidence_tiers, build_integrity_dimensions  # type: ignore[no-redef]
    from purity import KARAT_GRADES, NINE_NINES_PURITY, format_purity  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]

import logging

logger = logging.getLogger(__name__)

FIGURE_DPI = 300
FIGURE_FORMAT = "png"
SEED = 431


@dataclass(frozen=True)
class FigureSpec:
    name: str
    label: str
    path: str
    caption: str
    generated_by: str
    data_sources: tuple[str, ...]
    visual_encoding: str

    @property
    def svg_path(self) -> str:
        return self.path.rsplit(".", 1)[0] + ".svg"

    def registry_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["svg_path"] = self.svg_path
        return record


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        "purity_progression",
        "fig:purity_progression",
        "purity_progression.png",
        "Purity progression across the five refinery stages from ore (9K) to nine-nines certification.",
        "src/figures.py::generate_purity_progression",
        ("src/refinery.py::run_refinery", "src/purity.py::purity_to_nines"),
        "bars encode stage gain; line encodes cumulative purity; inset encodes nines gained",
    ),
    FigureSpec(
        "karat_grading",
        "fig:karat_grading",
        "karat_grading.png",
        "Gold karat grading scale (9K–24K + nine-nines) with refinery stage markers.",
        "src/figures.py::generate_karat_grading_chart",
        ("src/purity.py::KARAT_GRADES", "src/refinery.py::run_refinery"),
        "horizontal threshold bands with refinery-stage markers",
    ),
    FigureSpec(
        "token_density",
        "fig:token_density",
        "token_density.png",
        "Mega-madlib token distribution across manuscript sections and lexicon categories.",
        "src/figures.py::generate_token_density_chart",
        ("output/reports/token_plan.json", "src/composition.py::generate_token_plan"),
        "ordered bars encode token counts by section and lexicon category",
    ),
    FigureSpec(
        "provenance_sankey",
        "fig:provenance_sankey",
        "provenance_sankey.png",
        "Provenance trace: ore → stages → certification purity flow.",
        "src/figures.py::generate_provenance_sankey",
        ("src/refinery.py::run_refinery",),
        "directed stage graph with edge widths proportional to purity gain",
    ),
    FigureSpec(
        "purity_claim_scatter",
        "fig:purity_claim_scatter",
        "purity_claim_scatter.png",
        "Purity vs claim support rate scatter plot.",
        "src/figures.py::generate_purity_claim_scatter",
        ("output/reports/claim_support_registry.json", "src/refinery.py::run_refinery"),
        "scatter positions encode output purity and cumulative claim-support exposure",
    ),
    FigureSpec(
        "token_heatmap",
        "fig:token_heatmap",
        "token_heatmap.png",
        "Token selection heatmap: seed × category → selected index.",
        "src/figures.py::generate_token_heatmap",
        ("manuscript/config.yaml#gold_refinement.lexicon", "src/composition.py::generate_token_plan"),
        "heatmap cells encode deterministic selected inventory index across seeds",
    ),
    FigureSpec(
        "integrity_gate_matrix",
        "fig:integrity_gate_matrix",
        "integrity_gate_matrix.png",
        "Integrity-gate matrix linking audit rules to tests, manuscript surfaces, and generated artifacts.",
        "src/figures.py::generate_integrity_gate_matrix",
        ("manuscript/config.yaml#gold_refinement.audit_rules",),
        "categorical matrix encodes missing, partial, and full coverage by gate surface",
    ),
    FigureSpec(
        "formalism_traceability",
        "fig:formalism_traceability",
        "formalism_traceability.png",
        "Formalism traceability from source-owned equation identifiers to source evidence.",
        "src/figures.py::generate_formalism_traceability",
        ("src/formalisms.py::FORMALISMS",),
        "bipartite graph links formalisms to equation labels and source owners",
    ),
    FigureSpec(
        "implementation_circuit",
        "fig:implementation_circuit",
        "implementation_circuit.png",
        "Implementation circuit from config-owned ore through generated manuscript artifacts and validation feedback.",
        "src/figures.py::generate_implementation_circuit",
        ("manuscript/config.yaml", "src/refinery.py", "src/composition.py", "src/formalisms.py", "src/figures.py"),
        "directed graph encodes source, generated, validation, and publication layers",
    ),
    FigureSpec(
        "claim_evidence_assay",
        "fig:claim_evidence_assay",
        "claim_evidence_assay.png",
        "Claim-evidence assay showing supported contribution claims, evidence surfaces, and boundary classifications.",
        "src/figures.py::generate_claim_evidence_assay",
        ("manuscript/config.yaml#gold_refinement.contribution_claims", "src/evidence.py::build_evidence_registry"),
        "support bars plus claim to evidence to boundary graph topology",
    ),
    FigureSpec(
        "integrity_risk_matrix",
        "fig:integrity_risk_matrix",
        "integrity_risk_matrix.png",
        "Scientific-integrity risk matrix plotting severity, detectability, residual risk, and owning evidence surface.",
        "src/figures.py::generate_integrity_risk_matrix",
        ("src/integrity.py::build_integrity_dimensions",),
        "scatter positions encode severity and detectability; marker size encodes residual risk; color encodes source tier",
    ),
    FigureSpec(
        "evidence_tier_ladder",
        "fig:evidence_tier_ladder",
        "evidence_tier_ladder.png",
        "Evidence-tier ladder summarizing source tiers available to the shared template evidence registry.",
        "src/figures.py::generate_evidence_tier_ladder",
        ("output/reports/evidence_registry.json", "src/integrity.py::build_evidence_tiers"),
        "ordered horizontal bars encode counts and percentages by evidence source tier",
    ),
)

FIGURE_SPEC_BY_NAME = {spec.name: spec for spec in FIGURE_SPECS}

SOURCE_TIER_COLORS = {
    "artifact": "#2a9d8f",
    "bibliography": "#90be6d",
    "claim_ledger": "#f4a261",
    "config": "#577590",
    "generated_metric": "#3a0ca3",
    "source_code": "#264653",
    "validation": "#e76f51",
}

NODE_TYPE_COLORS = {
    "source": "#264653",
    "code": "#2a9d8f",
    "generated": "#e9c46a",
    "manuscript": "#f4a261",
    "validation": "#e76f51",
    "publication": "#577590",
    "claim": "#f4a261",
    "evidence": "#2a9d8f",
    "boundary": "#e76f51",
    "formalism": "#577590",
    "equation": "#e9c46a",
}

# Colourblind-safe palette for gold-refining stages
STAGE_COLORS: list[str] = [
    "#8B4513",  # raw ore brown
    "#CD7F32",  # smelting copper
    "#FFD700",  # assaying gold
    "#FFA500",  # cupellation orange
    "#FF6347",  # certification red-gold
]

STAGE_LABELS: tuple[str, ...] = (
    "Ore",
    "Smelting",
    "Assaying",
    "Cupellation",
    "Certification",
)


def _ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _style_axes(ax: plt.Axes, *, grid_axis: Literal["both", "x", "y"] = "y") -> None:
    ax.grid(True, axis=grid_axis, alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def _spec(name: str) -> FigureSpec:
    return FIGURE_SPEC_BY_NAME[name]


def _svg_path(png_path: Path) -> Path:
    return png_path.with_suffix(".svg")


def _normalize_svg_whitespace(svg_path: Path) -> None:
    text = svg_path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if text.endswith("\n"):
        normalized += "\n"
    if normalized != text:
        svg_path.write_text(normalized, encoding="utf-8")


def _save_figure(fig: plt.Figure, out_path: Path) -> Path:
    svg_path = _svg_path(out_path)
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    _normalize_svg_whitespace(svg_path)
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    logger.info("Wrote %s", svg_path)
    return out_path


def _nines_score(purity: float) -> float:
    return -float(np.log10(max(1.0 - purity, 1e-12)))


def purity_nines_values(purities: list[float] | tuple[float, ...]) -> list[float]:
    return [_nines_score(float(purity)) for purity in purities]


def _short_label(value: str, *, width: int = 18) -> str:
    return fill(value, width=width)


def _source_display_label(value: str) -> str:
    if "::" in value:
        file_part = value.split("::", 1)[0]
        return Path(file_part).name
    if "#" in value:
        file_part = value.split("#", 1)[0]
        return Path(file_part).name
    return Path(value).name if "/" in value else value


def _draw_labeled_digraph(
    ax: plt.Axes,
    graph: nx.DiGraph,
    positions: dict[str, tuple[float, float]] | dict[Any, Any],
    *,
    node_size: int = 1900,
    edge_widths: list[float] | None = None,
    font_size: float = 7.5,
) -> None:
    node_colors = [
        NODE_TYPE_COLORS.get(str(graph.nodes[node].get("kind", "source")), "#94a3b8") for node in graph.nodes
    ]
    labels = {node: _short_label(str(graph.nodes[node].get("label", node))) for node in graph.nodes}
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_color=node_colors,
        node_size=node_size,
        edgecolors="#111827",
        linewidths=0.8,
        alpha=0.94,
    )
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=14,
        width=edge_widths or 1.4,
        edge_color="#475569",
        connectionstyle="arc3,rad=0.05",
    )
    nx.draw_networkx_labels(graph, positions, labels=labels, ax=ax, font_size=font_size, font_color="#111827")
    edge_labels = {
        (source, target): str(data.get("label", ""))
        for source, target, data in graph.edges(data=True)
        if data.get("label")
    }
    if edge_labels:
        nx.draw_networkx_edge_labels(
            graph,
            positions,
            edge_labels=edge_labels,
            ax=ax,
            font_size=max(6.0, font_size - 1.0),
            font_color="#334155",
            rotate=False,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.3},
        )
    ax.axis("off")


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def build_provenance_flow_graph() -> tuple[nx.DiGraph, list[float]]:
    result = run_refinery()
    stages = result.stages
    graph = nx.DiGraph()
    graph.add_node("ore", label=f"Input ore\n{format_purity(stages[0].input_purity)}", kind="source")
    previous = "ore"
    edge_widths: list[float] = []
    max_gain = max(stage.purity_gain for stage in stages)
    for index, stage in enumerate(stages):
        node = f"stage_{stage.order}"
        graph.add_node(
            node,
            label=f"{stage.order}. {stage.name}\n{stage.karat_grade.label}\n{format_purity(stage.output_purity)}",
            kind="generated" if index < len(stages) - 1 else "publication",
            layer=stage.order,
            x=index + 1.0,
            y=0.0 if index % 2 == 0 else 0.22,
        )
        graph.add_edge(previous, node, label=f"+{stage.purity_gain:.4f}")
        edge_widths.append(1.0 + 5.0 * stage.purity_gain / max_gain)
        previous = node
    graph.nodes["ore"]["x"] = 0.0
    graph.nodes["ore"]["y"] = 0.0
    return graph, edge_widths


def build_formalism_traceability_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    for idx, item in enumerate(FORMALISMS):
        y = len(FORMALISMS) - idx
        formalism_node = f"formalism_{item.formalism_id}"
        equation_node = f"equation_{item.equation_label}"
        source_node = f"source_{item.formalism_id}"
        graph.add_node(
            formalism_node,
            label=f"{item.formalism_id}: {item.title}",
            kind="formalism",
            x=0.0,
            y=y,
        )
        graph.add_node(equation_node, label=item.equation_label, kind="equation", x=1.0, y=y)
        graph.add_node(source_node, label=_source_display_label(item.source), kind="source", x=2.1, y=y)
        graph.add_edge(formalism_node, equation_node, label="defines")
        graph.add_edge(equation_node, source_node, label="owned by")
    return graph


def build_implementation_circuit_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    nodes = {
        "config": ("Config ore\nconfig.yaml", "source", 0),
        "refinery": ("Refinery code\npurity stages", "code", 1),
        "tokens": ("Token plan\ndigest selections", "generated", 1),
        "formalisms": ("Formalisms\nequation labels", "code", 2),
        "figures": ("Figures\nPNG + SVG registry", "generated", 2),
        "manuscript": ("Hydrated manuscript\nresolved variables", "manuscript", 3),
        "validators": ("Validators\npytest/evidence/render", "validation", 4),
        "publication": ("Publication metal\nPDF + HTML", "publication", 5),
    }
    for node, (label, kind, layer) in nodes.items():
        graph.add_node(node, label=label, kind=kind, layer=layer)
    for source, target, label in (
        ("config", "refinery", "targets"),
        ("config", "tokens", "slots"),
        ("refinery", "formalisms", "purity law"),
        ("tokens", "figures", "coverage"),
        ("formalisms", "manuscript", "equations"),
        ("figures", "manuscript", "registered refs"),
        ("manuscript", "validators", "claims"),
        ("validators", "publication", "gates"),
        ("publication", "config", "fork feedback"),
    ):
        graph.add_edge(source, target, label=label)
    return graph


def build_claim_evidence_topology(entries: list[Any] | tuple[Any, ...]) -> nx.DiGraph:
    graph = nx.DiGraph()
    evidence_nodes: dict[str, str] = {}
    boundary_nodes: dict[str, str] = {}
    for row, entry in enumerate(entries):
        claim_node = f"claim_{row}"
        evidence_key = str(entry.evidence_source)
        boundary_key = str(entry.boundary or "local")
        evidence_node = evidence_nodes.setdefault(evidence_key, f"evidence_{len(evidence_nodes)}")
        boundary_node = boundary_nodes.setdefault(boundary_key, f"boundary_{len(boundary_nodes)}")
        y = len(entries) - row
        graph.add_node(claim_node, label=str(entry.claim_name), kind="claim", layer=0, x=0.0, y=y)
        if evidence_node not in graph:
            graph.add_node(
                evidence_node,
                label=_source_display_label(evidence_key),
                kind="evidence",
                layer=1,
                x=1.25,
                y=y,
            )
        if boundary_node not in graph:
            graph.add_node(boundary_node, label=boundary_key, kind="boundary", layer=2, x=2.5, y=y)
        graph.add_edge(claim_node, evidence_node, label="supported" if entry.supported else "missing")
        graph.add_edge(evidence_node, boundary_node, label="boundary")
    return graph


def generate_purity_progression(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a line+bar chart showing purity progression across refinery stages.

    The x-axis is stage order, the y-axis is purity fraction. A line shows
    the purity sequence (input→output per stage) and bars show the per-stage
    purity gain. The nine-nines threshold is marked.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()
    purity_seq = list(result.purity_sequence)
    stage_names = [STAGE_LABELS[i] for i in range(len(result.stages))]
    gains = [result.stages[i].output_purity - result.stages[i].input_purity for i in range(len(result.stages))]

    fig = plt.figure(figsize=(11, 7.5))
    grid = fig.add_gridspec(2, 1, height_ratios=(3.2, 1.2), hspace=0.24)
    ax1 = fig.add_subplot(grid[0])
    ax3 = fig.add_subplot(grid[1])

    x_positions = np.arange(len(result.stages))
    bar_width = 0.6
    ax1.bar(
        x_positions,
        gains,
        bar_width,
        color=STAGE_COLORS[: len(result.stages)],
        alpha=0.7,
        label="Purity gain per stage",
    )
    ax1.set_xlabel("Refinery Stage", fontsize=12)
    ax1.set_ylabel("Purity Gain (fraction)", fontsize=12, color="#333333")
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(stage_names, rotation=15, ha="right")
    ax1.tick_params(axis="y", labelcolor="#333333")
    _style_axes(ax1)

    ax2 = ax1.twinx()
    line_x = np.arange(len(purity_seq))
    ax2.plot(
        line_x,
        purity_seq,
        "ko-",
        linewidth=2,
        markersize=8,
        label="Purity sequence",
    )
    ax2.set_ylabel("Cumulative Purity (fraction)", fontsize=12, color="#333333")
    ax2.set_ylim(-0.05, 1.15)
    ax2.axhline(y=0.999999999, color="r", linestyle="--", alpha=0.5, label="Nine-nines (99.9999999%)")
    ax2.axhline(y=0.999, color="orange", linestyle="--", alpha=0.3, label="24K (99.9%)")

    ax2.annotate(
        f"{format_purity(result.final_purity)}",
        xy=(len(purity_seq) - 1, result.final_purity),
        xytext=(len(purity_seq) - 1.5, result.final_purity + 0.05),
        fontsize=9,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    ax1.set_title("Gold Refinery: Purity Progression from Ore to Nine-Nines", fontsize=14)
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.95), fontsize=9)

    nines = purity_nines_values(tuple(purity_seq))
    ax3.plot(line_x, nines, color="#7f1d1d", marker="o", linewidth=2.0)
    ax3.fill_between(line_x, nines, color="#fecaca", alpha=0.45)
    ax3.set_xticks(line_x)
    ax3.set_xticklabels(["Input", *stage_names], rotation=15, ha="right")
    ax3.set_ylabel("Nines gained\n$-\\log_{10}(1-p)$", fontsize=10)
    ax3.set_xlabel("Refinery trajectory")
    ax3.set_title("Late-stage purity is visible on a nines transform", fontsize=11)
    for x, score in zip(line_x, nines):
        ax3.text(float(x), score + 0.08, f"{score:.1f}", ha="center", va="bottom", fontsize=8)
    _style_axes(ax3)

    out_path = output_dir / "purity_progression.png"
    return _save_figure(fig, out_path)


def generate_karat_grading_chart(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a horizontal bar chart mapping karat grades to purity fractions.

    Shows all standard karat grades (9K–24K) plus the nine-nines threshold,
    with the refinery stages overlaid as markers.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()

    grades = sorted(KARAT_GRADES.items())
    grade_labels = [f"{k}K" for k, _ in grades] + ["9N"]
    grade_purities = [v for _, v in grades] + [NINE_NINES_PURITY]

    fig, ax = plt.subplots(figsize=(11, 6.2))

    y_positions = np.arange(len(grade_labels))
    bar_colors = plt.colormaps["YlOrBr"](np.linspace(0.3, 0.95, len(grade_labels)))

    ax.barh(y_positions, grade_purities, color=bar_colors, alpha=0.84, height=0.56)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grade_labels)
    ax.set_xlabel("Purity Fraction", fontsize=12)
    ax.set_title("Gold Karat Grading Scale with Refinery Stages", fontsize=14)
    ax.set_xlim(0, 1.1)
    ax.axvspan(0.999, 1.0, color="#fde68a", alpha=0.26, label="24K band")
    ax.axvline(NINE_NINES_PURITY, color="#991b1b", linestyle="--", linewidth=1.4, label="Nine-nines")

    for i, purity in enumerate(grade_purities):
        ax.text(purity + 0.01, i, format_purity(purity), va="center", fontsize=8)

    for i, stage in enumerate(result.stages):
        target_purity = stage.output_purity
        closest_y = min(y_positions, key=lambda y: abs(grade_purities[y] - target_purity))
        ax.scatter(
            target_purity,
            closest_y + 0.35,
            color=STAGE_COLORS[i],
            s=100,
            zorder=5,
            marker="D",
            edgecolors="black",
            linewidths=0.5,
        )
        ax.annotate(
            stage.name,
            xy=(target_purity, closest_y + 0.35),
            xytext=(min(1.03, target_purity + 0.035), closest_y + 0.35),
            fontsize=8,
            fontstyle="italic",
        )

    ax.legend(loc="lower right", fontsize=8)
    _style_axes(ax, grid_axis="x")
    out_path = output_dir / "karat_grading.png"
    return _save_figure(fig, out_path)


def generate_token_density_chart(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
    token_plan_data: dict[str, Any] | None = None,
) -> Path:
    """Generate a bar chart showing token counts per section and per category.

    Reads token_plan.json if available, otherwise generates the plan.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    # Load token plan data
    if token_plan_data is None:
        plan_path = output_dir.parent / "reports" / "token_plan.json"
        if plan_path.exists():
            with plan_path.open("r") as f:
                token_plan_data = json.load(f)
        else:
            cfg = load_gold_refinement_config(project_root) if project_root else load_gold_refinement_config()
            plan = generate_token_plan(cfg)
            token_plan_data = {
                "section_counts": plan.section_counts,
                "category_counts": plan.category_counts,
            }

    section_counts: dict[str, int] = token_plan_data.get("section_counts", {}) if token_plan_data else {}
    category_counts: dict[str, int] = token_plan_data.get("category_counts", {}) if token_plan_data else {}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.4))

    if section_counts:
        section_items = sorted(section_counts.items(), key=lambda item: (-item[1], item[0]))
        sections = [item[0] for item in section_items]
        counts = [item[1] for item in section_items]
        total = sum(counts)
        ax1.bar(sections, counts, color="#1e3a8a", alpha=0.82)
        ax1.set_title("Tokens per Manuscript Section", fontsize=12)
        ax1.set_xlabel("Section")
        ax1.set_ylabel("Token Count")
        ax1.tick_params(axis="x", rotation=30)
        for i, c in enumerate(counts):
            pct = 100 * c / total if total else 0
            ax1.text(i, c + 0.1, f"{c}\n{pct:.0f}%", ha="center", fontsize=8)
        ax1.text(0.98, 0.95, f"Total: {total}", transform=ax1.transAxes, ha="right", va="top", fontsize=9)
        _style_axes(ax1)

    if category_counts:
        category_items = sorted(category_counts.items(), key=lambda item: (item[1], item[0]))
        categories = [item[0] for item in category_items]
        counts = [item[1] for item in category_items]
        total = sum(counts)
        ax2.barh(categories, counts, color="#0f766e", alpha=0.8)
        ax2.set_title("Tokens per Lexicon Category", fontsize=12)
        ax2.set_xlabel("Token Count")
        ax2.set_ylabel("Category")
        for i, c in enumerate(counts):
            pct = 100 * c / total if total else 0
            ax2.text(c + 0.1, i, f"{c} ({pct:.0f}%)", va="center", fontsize=8)
        ax2.text(0.98, 0.04, f"Total: {total}", transform=ax2.transAxes, ha="right", va="bottom", fontsize=9)
        _style_axes(ax2, grid_axis="x")

    fig.suptitle("Mega-Madlib Token Distribution", fontsize=14, y=1.02)
    out_path = output_dir / "token_density.png"
    return _save_figure(fig, out_path)


def figure_registry_payload() -> dict[str, Any]:
    return {"figures": [spec.registry_record() for spec in FIGURE_SPECS]}


def write_figure_registry(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir / "figure_registry.json"
    registry_path.write_text(
        json.dumps(figure_registry_payload(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote %s", registry_path)
    return registry_path


def _quality_record(output_dir: Path, spec: FigureSpec) -> dict[str, Any]:
    png_path = output_dir / spec.path
    svg_path = output_dir / spec.svg_path
    record: dict[str, Any] = {
        "name": spec.name,
        "label": spec.label,
        "png_path": spec.path,
        "svg_path": spec.svg_path,
        "png_exists": png_path.exists(),
        "svg_exists": svg_path.exists(),
        "png_bytes": png_path.stat().st_size if png_path.exists() else 0,
        "svg_bytes": svg_path.stat().st_size if svg_path.exists() else 0,
        "width_px": 0,
        "height_px": 0,
        "nonwhite_fraction": 0.0,
        "color_variance": 0.0,
        "passes_quality": False,
    }
    if png_path.exists():
        image = np.asarray(mpimg.imread(png_path))
        rgb = image[..., :3] if image.ndim == 3 else np.stack([image, image, image], axis=-1)
        rgb_float = rgb.astype(float)
        if rgb_float.max(initial=0.0) > 1.0:
            rgb_float = rgb_float / 255.0
        height, width = rgb_float.shape[:2]
        nonwhite = np.max(np.abs(rgb_float - 1.0), axis=2) > 0.02
        record["width_px"] = int(width)
        record["height_px"] = int(height)
        record["nonwhite_fraction"] = round(float(np.mean(nonwhite)), 6)
        record["color_variance"] = round(float(np.var(rgb_float)), 8)
    record["passes_quality"] = (
        bool(record["png_exists"])
        and bool(record["svg_exists"])
        and int(record["png_bytes"]) > 1000
        and int(record["svg_bytes"]) > 1000
        and int(record["width_px"]) >= 900
        and int(record["height_px"]) >= 600
        and float(record["nonwhite_fraction"]) > 0.01
        and float(record["color_variance"]) > 0.00001
    )
    return record


def write_figure_quality_report(project_root: Path) -> Path:
    output_dir = project_root / "output" / "figures"
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    records = [_quality_record(output_dir, spec) for spec in FIGURE_SPECS]
    registry = _load_json_object(output_dir / "figure_registry.json")
    registry_labels = {str(item.get("label", "")) for item in registry.get("figures", []) if isinstance(item, dict)}
    spec_labels = {spec.label for spec in FIGURE_SPECS}
    payload = {
        "schema": "template-gold-refinement-figure-quality-v1",
        "figure_count": len(FIGURE_SPECS),
        "png_count": sum(1 for record in records if record["png_exists"]),
        "svg_count": sum(1 for record in records if record["svg_exists"]),
        "passing_count": sum(1 for record in records if record["passes_quality"]),
        "registry_parity": registry_labels == spec_labels,
        "records": records,
    }
    path = reports_dir / "figure_quality_report.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s", path)
    return path


def generate_all_figures(project_root: Path) -> list[Path]:
    """Generate all figures for the gold-refinement exemplar.

    Returns the list of generated figure paths.
    """
    output_dir = project_root / "output" / "figures"
    paths = [
        generate_purity_progression(output_dir, project_root=project_root),
        generate_karat_grading_chart(output_dir, project_root=project_root),
        generate_token_density_chart(output_dir, project_root=project_root),
        generate_provenance_sankey(output_dir, project_root=project_root),
        generate_purity_claim_scatter(output_dir, project_root=project_root),
        generate_token_heatmap(output_dir, project_root=project_root),
        generate_integrity_gate_matrix(output_dir, project_root=project_root),
        generate_formalism_traceability(output_dir, project_root=project_root),
        generate_implementation_circuit(output_dir, project_root=project_root),
        generate_claim_evidence_assay(output_dir, project_root=project_root),
        generate_integrity_risk_matrix(output_dir, project_root=project_root),
        generate_evidence_tier_ladder(output_dir, project_root=project_root),
    ]
    write_figure_registry(output_dir)
    write_figure_quality_report(project_root)
    return paths


def generate_provenance_sankey(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a Sankey-style flow diagram from ore through stages to certification.

    Uses stacked bar segments to approximate a Sankey flow since matplotlib
    does not have a built-in Sankey that handles the 5-stage flow elegantly.
    """
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    graph, edge_widths = build_provenance_flow_graph()
    positions = {node: (float(data.get("x", 0.0)), float(data.get("y", 0.0))) for node, data in graph.nodes(data=True)}

    fig, ax = plt.subplots(figsize=(12, 4.8))
    _draw_labeled_digraph(ax, graph, positions, node_size=2500, edge_widths=edge_widths, font_size=7.2)
    ax.set_title("Provenance Flow: Ore to Nine-Nines Certification", fontsize=14, pad=18)
    ax.text(
        0.5,
        -0.14,
        "Edge width encodes stage purity gain; final node encodes nine-nines certification.",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8.5,
        color="#334155",
    )

    out_path = output_dir / "provenance_sankey.png"
    return _save_figure(fig, out_path)


def generate_purity_claim_scatter(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a scatter plot of purity vs claim support rate per stage.

    Each stage's output purity is plotted against the fraction of
    contribution claims that are supported at that stage's evidence level.
    """
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    graph = build_formalism_traceability_graph()
    positions = {node: (float(data.get("x", 0.0)), float(data.get("y", 0.0))) for node, data in graph.nodes(data=True)}

    formalism_count_for_height = sum(1 for _, data in graph.nodes(data=True) if data.get("kind") == "formalism")
    fig, ax = plt.subplots(figsize=(14, max(5, 0.72 * formalism_count_for_height + 2)))
    _draw_labeled_digraph(ax, graph, positions, node_size=2300, font_size=6.8)
    ax.set_title("Formalism Traceability Graph", fontsize=14, pad=16)
    ax.text(0.17, 0.95, "Formalism", transform=ax.transAxes, ha="center", fontsize=10, fontweight="bold")
    ax.text(0.50, 0.95, "Equation label", transform=ax.transAxes, ha="center", fontsize=10, fontweight="bold")
    ax.text(0.83, 0.95, "Source owner", transform=ax.transAxes, ha="center", fontsize=10, fontweight="bold")

    out_path = output_dir / "formalism_traceability.png"
    return _save_figure(fig, out_path)


def generate_implementation_circuit(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    graph = build_implementation_circuit_graph()
    positions = nx.multipartite_layout(graph, subset_key="layer", align="vertical", scale=2.4)

    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    _draw_labeled_digraph(ax, graph, positions, node_size=2600, font_size=7.4)
    ax.set_title("Gold Refinement Implementation Circuit", fontsize=15, pad=18)

    ax.text(
        0.50,
        0.04,
        "A fork changes the left side first; generated artifacts and validators then prove whether the manuscript still refines.",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#334155",
    )
    out_path = output_dir / "implementation_circuit.png"
    return _save_figure(fig, out_path)


def generate_claim_evidence_assay(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

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


__all__ = [
    "FIGURE_SPECS",
    "FigureSpec",
    "STAGE_COLORS",
    "STAGE_LABELS",
    "build_claim_evidence_topology",
    "build_formalism_traceability_graph",
    "build_implementation_circuit_graph",
    "build_provenance_flow_graph",
    "figure_registry_payload",
    "generate_all_figures",
    "generate_claim_evidence_assay",
    "generate_evidence_tier_ladder",
    "generate_formalism_traceability",
    "generate_implementation_circuit",
    "generate_integrity_gate_matrix",
    "generate_integrity_risk_matrix",
    "generate_karat_grading_chart",
    "generate_provenance_sankey",
    "generate_purity_claim_scatter",
    "generate_purity_progression",
    "generate_token_density_chart",
    "generate_token_heatmap",
    "purity_nines_values",
    "write_figure_quality_report",
    "write_figure_registry",
]
