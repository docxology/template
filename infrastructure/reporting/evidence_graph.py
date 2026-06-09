#!/usr/bin/env python3
"""Queryable evidence graph data layer (EVIDENCE-GRAPH-1).

A deterministic, read-only graph that unifies the pipeline stage DAG, artifact
registries, claim ledgers, provenance, and manuscript tokens for a single
project into one queryable structure.

The graph is assembled **exclusively from existing sources** — it never writes
to or mutates project/pipeline files. The authoritative structural source is
the stage DAG (``infrastructure/core/pipeline/pipeline.yaml``), which is always
present. Optional sources (manuscript-variable manifests, claim ledgers) are
ingested only when they already exist on disk; when a project exposes no claim
ledger, claim nodes are left empty and a note is recorded rather than
fabricating data.

Node types
----------
``producer``  — a stage that *produces* artifacts (analysis / render / setup).
``consumer``  — a stage that *consumes* artifacts but produces none new.
``validator`` — a stage tagged ``tests`` or named like a validation step.
``artifact``  — an output (or input) artifact path declared in a stage contract.
``claim``     — a verifiable claim drawn from a claim ledger (empty when none).

Edge relations
--------------
``produces``  — producer/consumer/validator stage → artifact it emits.
``consumes``  — stage → artifact it reads.
``validates`` — validator stage → artifact it checks.
``supports``  — artifact → claim it backs (only when a claim ledger exists).

Determinism
-----------
:func:`graph_to_json` emits nodes and edges in sorted order with
``sort_keys=True`` so that the same inputs yield byte-identical output. No
wall-clock time or randomness is baked into any generated artifact.

CLI
---
``python -m infrastructure.reporting.evidence_graph build <project> [--json out]``
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition
from infrastructure.core.project_paths import resolve_project_root

logger = get_logger(__name__)

__all__ = [
    "NodeType",
    "RelationType",
    "EvidenceNode",
    "EvidenceEdge",
    "EvidenceGraph",
    "build_evidence_graph",
    "graph_to_json",
    "main",
]

# Relative to the repository root; the canonical stage DAG source of truth.
_PIPELINE_YAML = Path("infrastructure") / "core" / "pipeline" / "pipeline.yaml"


class NodeType(str, Enum):
    """Typed node kinds in the evidence graph."""

    PRODUCER = "producer"
    CONSUMER = "consumer"
    VALIDATOR = "validator"
    CLAIM = "claim"
    ARTIFACT = "artifact"


class RelationType(str, Enum):
    """Typed edge relations in the evidence graph."""

    PRODUCES = "produces"
    CONSUMES = "consumes"
    VALIDATES = "validates"
    SUPPORTS = "supports"


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    """A typed node carrying an id, type, and source-of-truth reference."""

    id: str
    type: NodeType
    source_of_truth: str
    label: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable, stable dict representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_of_truth": self.source_of_truth,
            "label": self.label,
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceNode:
        """Reconstruct a node from its dict representation."""
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            source_of_truth=data["source_of_truth"],
            label=data.get("label", ""),
            attributes=dict(data.get("attributes", {})),
        )


@dataclass(frozen=True, slots=True)
class EvidenceEdge:
    """A directed, labelled edge between two node ids."""

    source: str
    target: str
    relation: RelationType

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable, stable dict representation."""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceEdge:
        """Reconstruct an edge from its dict representation."""
        return cls(
            source=data["source"],
            target=data["target"],
            relation=RelationType(data["relation"]),
        )


@dataclass
class EvidenceGraph:
    """A queryable evidence graph for a single project.

    Nodes and edges are validated on insertion: node ids must be unique and
    every edge endpoint must reference an existing node. ``notes`` records any
    gaps (e.g. an absent claim ledger) so callers never confuse "no data" with
    "fabricated data".
    """

    project: str
    nodes: list[EvidenceNode] = field(default_factory=list)
    edges: list[EvidenceEdge] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    # -- mutation (validated) --------------------------------------------- #
    def add_node(self, node: EvidenceNode) -> None:
        """Append *node*, raising on a duplicate id."""
        if any(existing.id == node.id for existing in self.nodes):
            raise ValueError(f"duplicate node id: {node.id!r}")
        self.nodes.append(node)

    def add_edge(self, edge: EvidenceEdge) -> None:
        """Append *edge*, raising if either endpoint is unknown."""
        ids = {n.id for n in self.nodes}
        if edge.source not in ids:
            raise ValueError(f"edge references unknown source node: {edge.source!r}")
        if edge.target not in ids:
            raise ValueError(f"edge references unknown target node: {edge.target!r}")
        self.edges.append(edge)

    # -- query API --------------------------------------------------------- #
    def nodes_by_type(self, node_type: NodeType) -> list[EvidenceNode]:
        """Return all nodes of *node_type* (sorted by id for determinism)."""
        return sorted((n for n in self.nodes if n.type is node_type), key=lambda n: n.id)

    def neighbors(self, node_id: str) -> list[EvidenceNode]:
        """Return nodes directly connected to *node_id* (in or out).

        Raises ``KeyError`` if *node_id* is not in the graph.
        """
        by_id = {n.id: n for n in self.nodes}
        if node_id not in by_id:
            raise KeyError(node_id)
        connected: set[str] = set()
        for edge in self.edges:
            if edge.source == node_id:
                connected.add(edge.target)
            elif edge.target == node_id:
                connected.add(edge.source)
        return sorted((by_id[i] for i in connected), key=lambda n: n.id)

    def artifacts_missing_metadata(self) -> list[EvidenceNode]:
        """Return artifact nodes lacking any producer/consumer/validator edge."""
        connected: set[str] = set()
        for edge in self.edges:
            connected.add(edge.source)
            connected.add(edge.target)
        return sorted(
            (n for n in self.nodes if n.type is NodeType.ARTIFACT and n.id not in connected),
            key=lambda n: n.id,
        )

    # -- serialization ----------------------------------------------------- #
    def to_dict(self) -> dict[str, Any]:
        """Return a stable, JSON-serializable dict (nodes/edges sorted)."""
        nodes = sorted(self.nodes, key=lambda n: n.id)
        edges = sorted(self.edges, key=lambda e: (e.source, e.target, e.relation.value))
        return {
            "project": self.project,
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceGraph:
        """Reconstruct a graph from its dict representation."""
        graph = cls(project=data["project"], notes=list(data.get("notes", [])))
        for node_data in data.get("nodes", []):
            graph.nodes.append(EvidenceNode.from_dict(node_data))
        for edge_data in data.get("edges", []):
            graph.edges.append(EvidenceEdge.from_dict(edge_data))
        return graph


# --------------------------------------------------------------------------- #
# Generator
# --------------------------------------------------------------------------- #
def _slug(value: str) -> str:
    """Deterministic, filesystem/id-safe slug for a stage name or path."""
    out = []
    for ch in value.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in {" ", "_", "/", "-", "."}:
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _classify_stage(stage: StageDefinition) -> NodeType:
    """Map a stage to a producer/consumer/validator node type.

    A stage tagged ``tests`` or named like a validation step is a *validator*.
    A stage whose contract declares output artifacts beyond a bare project
    output directory is a *producer*. Everything else is a *consumer*.
    """
    name_lower = stage.name.lower()
    if "tests" in stage.tags or "valid" in name_lower or "review" in name_lower:
        return NodeType.VALIDATOR
    if stage.contract is not None and _producing_outputs(stage):
        return NodeType.PRODUCER
    return NodeType.CONSUMER


def _producing_outputs(stage: StageDefinition) -> list[str]:
    """Return output artifacts that represent real production (not bare dirs)."""
    if stage.contract is None:
        return []
    bare = {"projects/{project}/output/", "projects/{project}/"}
    return [a for a in stage.contract.output_artifacts if a not in bare]


def _artifact_node(artifact_ref: str) -> EvidenceNode:
    """Build an artifact node from a contract artifact reference string."""
    return EvidenceNode(
        id=f"artifact:{_slug(artifact_ref)}",
        type=NodeType.ARTIFACT,
        source_of_truth=f"pipeline.yaml::contract::{artifact_ref}",
        label=artifact_ref,
        attributes={"path_template": artifact_ref},
    )


def _ensure_artifact(graph: EvidenceGraph, artifact_ref: str, seen: set[str]) -> str:
    """Add an artifact node once; return its node id."""
    node = _artifact_node(artifact_ref)
    if node.id not in seen:
        graph.add_node(node)
        seen.add(node.id)
    return node.id


def build_evidence_graph(repo_root: Path | str, project_name: str) -> EvidenceGraph:
    """Assemble the evidence graph for *project_name* from existing sources.

    Reads (never writes):
      * the stage DAG at ``infrastructure/core/pipeline/pipeline.yaml`` (and a
        project-specific override at ``projects/{name}/pipeline.yaml`` if present),
      * an optional claim ledger / manuscript-variable manifest under the
        project's ``output/data`` tree, when present.

    Args:
        repo_root: repository root containing ``infrastructure/`` and ``projects/``.
        project_name: project to build the graph for (e.g. ``template_code_project``).

    Returns:
        A populated :class:`EvidenceGraph`. ``notes`` records any absent
        optional sources rather than fabricating their data.
    """
    root = Path(repo_root)
    project_root = resolve_project_root(root, project_name)

    # Project-specific DAG override wins; fall back to the canonical default.
    override = project_root / "pipeline.yaml"
    dag_path = override if override.is_file() else root / _PIPELINE_YAML
    dag = PipelineDAG.from_yaml(dag_path)

    graph = EvidenceGraph(project=project_name)
    seen_artifacts: set[str] = set()

    for stage in dag.sorted_stages():
        stage_type = _classify_stage(stage)
        stage_id = f"stage:{_slug(stage.name)}"
        graph.add_node(
            EvidenceNode(
                id=stage_id,
                type=stage_type,
                source_of_truth=f"{dag_path.name}::{stage.name}",
                label=stage.name,
                attributes={"tags": list(stage.tags)},
            )
        )

        if stage.contract is None:
            continue

        # Stage -> produced artifacts.
        for out_ref in _producing_outputs(stage):
            art_id = _ensure_artifact(graph, out_ref, seen_artifacts)
            relation = RelationType.VALIDATES if stage_type is NodeType.VALIDATOR else RelationType.PRODUCES
            graph.add_edge(EvidenceEdge(source=stage_id, target=art_id, relation=relation))

        # Stage -> consumed artifacts (real artifact paths, not bare project dirs).
        bare = {"projects/{project}/output/", "projects/{project}/"}
        for in_ref in stage.contract.input_artifacts:
            if in_ref in bare:
                continue
            art_id = _ensure_artifact(graph, in_ref, seen_artifacts)
            graph.add_edge(EvidenceEdge(source=stage_id, target=art_id, relation=RelationType.CONSUMES))

    _ingest_claims(graph, project_root)
    return graph


# Well-known claim-ledger locations, searched in priority order. The first
# matching file wins. Globs are expanded (sorted) so an exemplar that writes a
# project-specific ledger name is still discovered. The AutoResearch exemplar
# writes its deterministic claim list to ``output/data/n.json`` (a bare JSON
# list of ``AutoResearchClaim`` dicts: ``identifier``, ``statement``,
# ``evidence_path``, ``supported``), so that exact name is included.
_CLAIM_LEDGER_CANDIDATES: tuple[str, ...] = (
    "output/data/claims.json",
    "output/data/*claims*.json",
    "output/data/n.json",
    "manuscript/claims.json",
    "claims.json",
)


def _find_claim_ledger(project_root: Path) -> Path | None:
    """Return the first existing claim ledger under *project_root*, or ``None``.

    Plain relative paths are probed directly; entries containing a glob
    metacharacter are expanded with :meth:`Path.glob` and matched in sorted
    order for deterministic selection.
    """
    for candidate in _CLAIM_LEDGER_CANDIDATES:
        if any(ch in candidate for ch in "*?[]"):
            for match in sorted(project_root.glob(candidate)):
                if match.is_file():
                    return match
        else:
            path = project_root / candidate
            if path.is_file():
                return path
    return None


def _claim_id(entry: dict[str, Any]) -> str | None:
    """Return a claim's stable identifier from either ``id`` or ``identifier``."""
    for key in ("id", "identifier"):
        value = entry.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _claim_status(entry: dict[str, Any]) -> str:
    """Derive a claim status from ``status`` or a boolean ``supported`` flag."""
    if "status" in entry and entry["status"] not in (None, ""):
        return str(entry["status"])
    if "supported" in entry:
        return "supported" if bool(entry["supported"]) else "unsupported"
    return "unknown"


def _ingest_claims(graph: EvidenceGraph, project_root: Path) -> None:
    """Ingest a claim ledger if one exists; otherwise record a gap note.

    Looks for a JSON claim ledger at well-known locations (see
    :data:`_CLAIM_LEDGER_CANDIDATES`). Both a bare JSON list of claim dicts and
    the wrapped ``{"claims": [...]}`` shape are accepted, and each claim's id is
    read from either an ``id`` or an ``identifier`` key. When a claim names an
    ``evidence_path``, an artifact node for that evidence file is ensured and a
    ``supports`` edge (artifact → claim) is recorded. When no ledger is found
    (as with ``template_code_project``), claim nodes are left empty and a note
    is appended — the graph never fabricates claim data.
    """
    ledger = _find_claim_ledger(project_root)
    if ledger is None:
        graph.notes.append(
            "No claim ledger found for this project; claim nodes are empty. "
            "Searched: output/data/claims.json, output/data/*claims*.json, "
            "output/data/n.json, manuscript/claims.json, claims.json."
        )
        return

    try:
        raw = json.loads(ledger.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive
        graph.notes.append(f"Claim ledger {ledger.name} unreadable ({exc}); skipped.")
        return

    claims = raw.get("claims", raw) if isinstance(raw, dict) else raw
    if not isinstance(claims, list):
        graph.notes.append(f"Claim ledger {ledger.name} has unexpected shape; claims left empty.")
        return

    claim_artifacts: set[str] = {n.id for n in graph.nodes if n.type is NodeType.ARTIFACT}
    for entry in claims:
        if not isinstance(entry, dict):
            continue
        identifier = _claim_id(entry)
        if identifier is None:
            continue
        claim_id = f"claim:{_slug(identifier)}"
        graph.add_node(
            EvidenceNode(
                id=claim_id,
                type=NodeType.CLAIM,
                source_of_truth=f"{ledger.name}::{identifier}",
                label=str(entry.get("statement", identifier)),
                attributes={"status": _claim_status(entry)},
            )
        )
        evidence_path = entry.get("evidence_path")
        if isinstance(evidence_path, str) and evidence_path:
            artifact_id = _ensure_artifact(graph, evidence_path, claim_artifacts)
            graph.add_edge(EvidenceEdge(source=artifact_id, target=claim_id, relation=RelationType.SUPPORTS))


def graph_to_json(graph: EvidenceGraph) -> str:
    """Serialize *graph* to a deterministic, byte-stable JSON string.

    Uses ``sort_keys=True`` and pre-sorted node/edge ordering so the same
    input always yields identical bytes. No timestamps or randomness.
    """
    return json.dumps(graph.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.reporting.evidence_graph",
        description="Build a queryable evidence graph for a project.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Build the evidence graph for a project.")
    build.add_argument("project", help="Project name (e.g. template_code_project).")
    build.add_argument(
        "--json",
        dest="json_out",
        metavar="PATH",
        help="Write JSON to PATH instead of stdout.",
    )
    build.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    if args.command == "build":
        graph = build_evidence_graph(args.repo_root, args.project)
        payload = graph_to_json(graph)
        if args.json_out:
            out_path = Path(args.json_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
            logger.info("Wrote evidence graph to %s", out_path)
        else:
            print(payload)
        return 0
    return 1  # pragma: no cover - argparse enforces a valid subcommand


if __name__ == "__main__":
    sys.exit(main())
