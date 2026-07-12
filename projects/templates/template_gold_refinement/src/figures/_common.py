"""Shared infrastructure for the gold-refinement figure subpackage.

Holds the matplotlib headless backend setup, logging, the ``FigureSpec``
dataclass, the figure specs / colour palettes / stage labels, and all private
drawing and IO helpers used by the chart, graph, diagram, and registry modules.

All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import fill
from typing import Any, Literal

import matplotlib
import networkx as nx
import numpy as np

try:
    from ..parsing import load_json_object as _load_json_object  # noqa: F401
except ImportError:  # pragma: no cover - flat-layout fallback
    import json

    def _load_json_object(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}


matplotlib.use("Agg")  # headless-safe before pyplot import
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

FIGURE_DPI = 300
FIGURE_FORMAT = "png"
SEED = 431
SVG_HASH_SALT = "template-gold-refinement-v1"
SVG_METADATA = {"Date": None, "Creator": "template_gold_refinement"}
PNG_METADATA = {"Software": "template_gold_refinement"}

matplotlib.rcParams["svg.hashsalt"] = SVG_HASH_SALT


@dataclass(frozen=True)
class FigureSpec:
    """Data container for FigureSpec."""

    name: str
    label: str
    path: str
    caption: str
    generated_by: str
    data_sources: tuple[str, ...]
    visual_encoding: str

    @property
    def svg_path(self) -> str:
        """Process svg path."""
        return self.path.rsplit(".", 1)[0] + ".svg"

    def registry_record(self) -> dict[str, Any]:
        """Process registry record."""
        record = asdict(self)
        record["svg_path"] = self.svg_path
        return record


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        "purity_progression",
        "fig:purity_progression",
        "purity_progression.png",
        "Purity progression across the five refinery stages from ore (9K) to nine-nines certification.",
        "src/figures/charts.py::generate_purity_progression",
        ("src/refinery.py::run_refinery", "src/purity.py::purity_to_nines"),
        "bars encode stage gain; line encodes cumulative purity; inset encodes nines gained",
    ),
    FigureSpec(
        "karat_grading",
        "fig:karat_grading",
        "karat_grading.png",
        "Gold karat grading scale (9K–24K + nine-nines) with refinery stage markers.",
        "src/figures/charts.py::generate_karat_grading_chart",
        ("src/purity.py::KARAT_GRADES", "src/refinery.py::run_refinery"),
        "horizontal threshold bands with refinery-stage markers",
    ),
    FigureSpec(
        "token_density",
        "fig:token_density",
        "token_density.png",
        "Mega-madlib token distribution across manuscript sections and lexicon categories.",
        "src/figures/charts.py::generate_token_density_chart",
        ("output/reports/token_plan.json", "src/composition.py::generate_token_plan"),
        "ordered bars encode token counts by section and lexicon category",
    ),
    FigureSpec(
        "provenance_sankey",
        "fig:provenance_sankey",
        "provenance_sankey.png",
        "Provenance trace: ore → stages → certification purity flow.",
        "src/figures/diagrams.py::generate_provenance_sankey",
        ("src/refinery.py::run_refinery",),
        "directed stage graph with edge widths proportional to purity gain",
    ),
    FigureSpec(
        "purity_claim_scatter",
        "fig:purity_claim_scatter",
        "purity_claim_scatter.png",
        "Stage purity plotted against the single project-level claim-support assay.",
        "src/figures/diagrams.py::generate_purity_claim_scatter",
        ("output/reports/claim_support_registry.json", "src/refinery.py::run_refinery"),
        "x positions encode stage output purity; the shared y position encodes the project-level claim-support rate",
    ),
    FigureSpec(
        "token_heatmap",
        "fig:token_heatmap",
        "token_heatmap.png",
        "Token selection heatmap: seed × category → selected index.",
        "src/figures/diagrams.py::generate_token_heatmap",
        ("manuscript/config.yaml#gold_refinement.lexicon", "src/composition.py::generate_token_plan"),
        "heatmap cells encode deterministic selected inventory index across seeds",
    ),
    FigureSpec(
        "integrity_gate_matrix",
        "fig:integrity_gate_matrix",
        "integrity_gate_matrix.png",
        "Integrity-gate matrix linking audit rules to tests, manuscript surfaces, and generated artifacts.",
        "src/figures/diagrams.py::generate_integrity_gate_matrix",
        ("manuscript/config.yaml#gold_refinement.audit_rules",),
        "categorical matrix encodes missing, partial, and full coverage by gate surface",
    ),
    FigureSpec(
        "formalism_traceability",
        "fig:formalism_traceability",
        "formalism_traceability.png",
        "Formalism traceability from source-owned equation identifiers to source evidence.",
        "src/figures/diagrams.py::generate_formalism_traceability",
        ("src/formalisms.py::FORMALISMS",),
        "bipartite graph links formalisms to equation labels and source owners",
    ),
    FigureSpec(
        "implementation_circuit",
        "fig:implementation_circuit",
        "implementation_circuit.png",
        "Implementation circuit from config-owned ore through generated manuscript artifacts and validation feedback.",
        "src/figures/diagrams.py::generate_implementation_circuit",
        (
            "manuscript/config.yaml",
            "src/refinery.py",
            "src/composition.py",
            "src/formalisms.py",
            "src/figures/diagrams.py",
        ),
        "directed graph encodes source, generated, validation, and publication layers",
    ),
    FigureSpec(
        "claim_evidence_assay",
        "fig:claim_evidence_assay",
        "claim_evidence_assay.png",
        "Claim-evidence assay showing supported contribution claims, evidence surfaces, and boundary classifications.",
        "src/figures/diagrams.py::generate_claim_evidence_assay",
        ("manuscript/config.yaml#gold_refinement.contribution_claims", "src/evidence.py::build_evidence_registry"),
        "support bars plus claim to evidence to boundary graph topology",
    ),
    FigureSpec(
        "integrity_risk_matrix",
        "fig:integrity_risk_matrix",
        "integrity_risk_matrix.png",
        "Scientific-integrity risk matrix plotting severity, detectability, residual risk, and owning evidence surface.",
        "src/figures/diagrams.py::generate_integrity_risk_matrix",
        ("src/integrity.py::build_integrity_dimensions",),
        "scatter positions encode severity and detectability; marker size encodes residual risk; color encodes source tier",
    ),
    FigureSpec(
        "evidence_tier_ladder",
        "fig:evidence_tier_ladder",
        "evidence_tier_ladder.png",
        "Evidence-tier ladder summarizing source tiers available to the shared template evidence registry.",
        "src/figures/diagrams.py::generate_evidence_tier_ladder",
        ("output/reports/evidence_registry.json", "src/integrity.py::build_evidence_tiers"),
        "ordered horizontal bars encode counts and percentages by evidence source tier",
    ),
)

FIGURE_SPEC_BY_NAME = {spec.name: spec for spec in FIGURE_SPECS}


def figure_markdown_block(spec: FigureSpec) -> str:
    """Process figure markdown block."""
    return f"![{spec.caption}](../output/figures/{spec.path}){{#{spec.label}}}"


def figure_markdown_variables() -> dict[str, str]:
    """Process figure markdown variables."""
    return {f"FIGURE_{spec.name.upper()}": figure_markdown_block(spec) for spec in FIGURE_SPECS}


def _graph_positions(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    return {node: (float(data.get("x", 0.0)), float(data.get("y", 0.0))) for node, data in graph.nodes(data=True)}


def _figure_output_dir(output_dir: Path | None, *, project_root: Path | None) -> Path:
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    return _ensure_output_dir(output_dir)


def _render_digraph_figure(
    output_dir: Path,
    *,
    filename: str,
    graph: nx.DiGraph,
    positions: dict[str, tuple[float, float]],
    title: str,
    figsize: tuple[float, float],
    node_size: int = 2500,
    edge_widths: list[float] | None = None,
    font_size: float = 7.2,
    subtitle: str | None = None,
    header_labels: tuple[tuple[float, float, str], ...] | None = None,
    footer_text: str | None = None,
    title_pad: float = 18,
) -> Path:
    fig, ax = plt.subplots(figsize=figsize)
    _draw_labeled_digraph(ax, graph, positions, node_size=node_size, edge_widths=edge_widths, font_size=font_size)
    ax.set_title(title, fontsize=14, pad=title_pad)
    if header_labels:
        for x_pos, y_pos, label in header_labels:
            ax.text(x_pos, y_pos, label, transform=ax.transAxes, ha="center", fontsize=10, fontweight="bold")
    if subtitle:
        ax.text(0.5, -0.14, subtitle, transform=ax.transAxes, ha="center", va="center", fontsize=8.5, color="#334155")
    if footer_text:
        ax.text(0.50, 0.04, footer_text, ha="center", va="center", fontsize=8.5, color="#334155")
    return _save_figure(fig, output_dir / filename)


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
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight", metadata=PNG_METADATA)
    fig.savefig(svg_path, format="svg", bbox_inches="tight", metadata=SVG_METADATA)
    _normalize_svg_whitespace(svg_path)
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    logger.info("Wrote %s", svg_path)
    return out_path


def _nines_score(purity: float) -> float:
    return -float(np.log10(max(1.0 - purity, 1e-12)))


def purity_nines_values(purities: list[float] | tuple[float, ...]) -> list[float]:
    """Process purity nines values."""
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
