"""Directed-graph builders for the gold-refinement figures.

Each builder returns a NetworkX ``DiGraph`` (and, where relevant, edge widths)
that the diagram renderers in :mod:`.diagrams` lay out and draw. Builders are
pure: they read project data via the refinery / formalism providers and never
touch matplotlib.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from ._common import _source_display_label

try:
    from ..formalisms import FORMALISMS
    from ..purity import format_purity
    from ..refinery import run_refinery
except ImportError:  # pragma: no cover - flat-layout fallback
    from formalisms import FORMALISMS  # type: ignore[no-redef]
    from purity import format_purity  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]


def build_provenance_flow_graph() -> tuple[nx.DiGraph, list[float]]:
    """Build provenance flow graph."""
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
    """Build formalism traceability graph."""
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
    """Build implementation circuit graph."""
    graph = nx.DiGraph()
    nodes = {
        "config": ("Config ore\nconfig.yaml", "source", 0, -2.4, 0.0),
        "refinery": ("Refinery code\npurity stages", "code", 1, -1.45, 0.48),
        "tokens": ("Token plan\ndigest selections", "generated", 1, -1.45, -0.48),
        "formalisms": ("Formalisms\nequation labels", "code", 2, -0.35, 0.48),
        "figures": ("Figures\nPNG + SVG registry", "generated", 2, -0.35, -0.48),
        "manuscript": ("Hydrated manuscript\nresolved variables", "manuscript", 3, 0.85, 0.0),
        "validators": ("Validators\npytest/evidence/render", "validation", 4, 1.85, 0.0),
        "publication": ("Publication metal\nPDF + HTML", "publication", 5, 2.75, 0.0),
    }
    for node, (label, kind, layer, x, y) in nodes.items():
        graph.add_node(node, label=label, kind=kind, layer=layer, x=x, y=y)
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
    """Build claim evidence topology."""
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
