#!/usr/bin/env python3
"""Tests for the evidence graph data layer (EVIDENCE-GRAPH-1).

No mocks: every test builds the graph from the *real* repository sources
(``infrastructure/core/pipeline/pipeline.yaml`` and the on-disk
``template_code_project`` exemplar) and exercises the schema with real
dataclasses and real JSON round-trips.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.reporting.evidence_graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    NodeType,
    RelationType,
    build_evidence_graph,
    graph_to_json,
    main,
)
from infrastructure.reporting.evidence_graph import _ingest_claims

REPO_ROOT = Path(__file__).resolve().parents[3]
EXEMPLAR = "template_code_project"


# --------------------------------------------------------------------------- #
# Schema-level tests (no I/O)
# --------------------------------------------------------------------------- #
def test_node_round_trips_through_dict() -> None:
    node = EvidenceNode(
        id="producer:project-analysis",
        type=NodeType.PRODUCER,
        source_of_truth="pipeline.yaml::Project Analysis",
        label="Project Analysis",
        attributes={"tags": ["core"]},
    )
    restored = EvidenceNode.from_dict(node.to_dict())
    assert restored == node
    assert restored.type is NodeType.PRODUCER


def test_edge_round_trips_through_dict() -> None:
    edge = EvidenceEdge(
        source="producer:project-analysis",
        target="artifact:output-data",
        relation=RelationType.PRODUCES,
    )
    restored = EvidenceEdge.from_dict(edge.to_dict())
    assert restored == edge
    assert restored.relation is RelationType.PRODUCES


def test_graph_round_trips_through_dict() -> None:
    graph = EvidenceGraph(project=EXEMPLAR)
    graph.add_node(
        EvidenceNode(
            id="artifact:reports",
            type=NodeType.ARTIFACT,
            source_of_truth="pipeline.yaml",
        )
    )
    graph.add_node(
        EvidenceNode(
            id="validator:output-validation",
            type=NodeType.VALIDATOR,
            source_of_truth="pipeline.yaml::Output Validation",
        )
    )
    graph.add_edge(
        EvidenceEdge(
            source="validator:output-validation",
            target="artifact:reports",
            relation=RelationType.VALIDATES,
        )
    )
    restored = EvidenceGraph.from_dict(graph.to_dict())
    assert restored == graph


def test_add_duplicate_node_id_raises() -> None:
    graph = EvidenceGraph(project=EXEMPLAR)
    node = EvidenceNode(id="x", type=NodeType.ARTIFACT, source_of_truth="src")
    graph.add_node(node)
    with pytest.raises(ValueError, match="duplicate node id"):
        graph.add_node(node)


def test_add_edge_with_unknown_endpoint_raises() -> None:
    graph = EvidenceGraph(project=EXEMPLAR)
    graph.add_node(EvidenceNode(id="a", type=NodeType.PRODUCER, source_of_truth="s"))
    with pytest.raises(ValueError, match="unknown"):
        graph.add_edge(EvidenceEdge(source="a", target="missing", relation=RelationType.PRODUCES))


# --------------------------------------------------------------------------- #
# Generator tests against the real exemplar
# --------------------------------------------------------------------------- #
def test_builds_for_real_exemplar() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    assert graph.project == EXEMPLAR
    assert graph.nodes, "graph must contain nodes"
    assert graph.edges, "graph must contain edges"


def test_has_producers_validators_and_artifacts() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    assert graph.nodes_by_type(NodeType.PRODUCER), "expected producer nodes"
    assert graph.nodes_by_type(NodeType.VALIDATOR), "expected validator nodes"
    assert graph.nodes_by_type(NodeType.ARTIFACT), "expected artifact nodes"


def test_claims_empty_for_code_project_with_note() -> None:
    """template_code_project has no claim ledger; claims must be empty + noted."""
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    assert graph.nodes_by_type(NodeType.CLAIM) == []
    assert any("claim" in note.lower() for note in graph.notes)


def test_edges_reference_existing_nodes() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    ids = {n.id for n in graph.nodes}
    for edge in graph.edges:
        assert edge.source in ids
        assert edge.target in ids


def test_produces_and_validates_relations_present() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    relations = {e.relation for e in graph.edges}
    assert RelationType.PRODUCES in relations
    assert RelationType.VALIDATES in relations


def test_neighbors_returns_connected_nodes() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    producers = graph.nodes_by_type(NodeType.PRODUCER)
    # at least one producer must have a neighbor (its produced artifact)
    assert any(graph.neighbors(p.id) for p in producers)


def test_neighbors_unknown_id_raises() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    with pytest.raises(KeyError):
        graph.neighbors("does-not-exist")


def test_artifacts_missing_metadata_is_computable() -> None:
    graph = build_evidence_graph(REPO_ROOT, EXEMPLAR)
    missing = graph.artifacts_missing_metadata()
    # result is a list of artifact nodes; every entry must be an artifact
    assert all(n.type is NodeType.ARTIFACT for n in missing)
    # and none of them have a producer/consumer/validator edge
    for node in missing:
        assert not graph.neighbors(node.id)


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_json_is_byte_identical_across_builds() -> None:
    first = graph_to_json(build_evidence_graph(REPO_ROOT, EXEMPLAR))
    second = graph_to_json(build_evidence_graph(REPO_ROOT, EXEMPLAR))
    assert first == second


def test_json_is_sorted_and_parseable() -> None:
    payload = graph_to_json(build_evidence_graph(REPO_ROOT, EXEMPLAR))
    parsed = json.loads(payload)
    assert parsed["project"] == EXEMPLAR
    # nodes are emitted in sorted-id order for byte stability
    ids = [n["id"] for n in parsed["nodes"]]
    assert ids == sorted(ids)


def test_graph_to_json_has_no_wall_clock() -> None:
    """Deterministic artifact: serializer must not bake in a timestamp."""
    payload = graph_to_json(build_evidence_graph(REPO_ROOT, EXEMPLAR))
    parsed = json.loads(payload)
    assert "generated_at" not in parsed
    assert "timestamp" not in parsed


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_build_writes_json(tmp_path: Path) -> None:
    out = tmp_path / "graph.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.reporting.evidence_graph",
            "build",
            EXEMPLAR,
            "--json",
            str(out),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["project"] == EXEMPLAR
    assert parsed["nodes"]


def test_cli_build_to_stdout() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.reporting.evidence_graph",
            "build",
            EXEMPLAR,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    # Shared infrastructure logging may prepend a "Loading ..." line on stdout;
    # the JSON payload is the trailing object, so slice from the first brace.
    brace = result.stdout.index("{")
    parsed = json.loads(result.stdout[brace:])
    assert parsed["project"] == EXEMPLAR


def test_main_writes_json_in_process(tmp_path: Path) -> None:
    """In-process CLI call (exercises main + parser branches)."""
    out = tmp_path / "g.json"
    rc = main(
        [
            "build",
            EXEMPLAR,
            "--json",
            str(out),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )
    assert rc == 0
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["project"] == EXEMPLAR
    assert parsed["nodes"]


# --------------------------------------------------------------------------- #
# Claim-ledger ingestion (real temp ledger — no mocks)
# --------------------------------------------------------------------------- #
def test_ingest_claims_reads_real_ledger(tmp_path: Path) -> None:
    """A real on-disk claim ledger yields claim nodes (no fabrication)."""
    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    ledger = {
        "claims": [
            {"id": "C1", "statement": "Optimizer converges", "status": "supported"},
            {"id": "C2", "statement": "Sensitivity bounded", "status": "open"},
            {"no_id": "skipped"},
        ]
    }
    (data_dir / "claims.json").write_text(json.dumps(ledger), encoding="utf-8")

    graph = EvidenceGraph(project="fixture")
    _ingest_claims(graph, tmp_path)

    claims = graph.nodes_by_type(NodeType.CLAIM)
    assert {c.id for c in claims} == {"claim:c1", "claim:c2"}
    assert graph.notes == []  # ledger present -> no gap note


def test_ingest_claims_handles_bare_list_ledger(tmp_path: Path) -> None:
    ledger = [{"id": "X1", "statement": "bare list claim"}]
    (tmp_path / "claims.json").write_text(json.dumps(ledger), encoding="utf-8")

    graph = EvidenceGraph(project="fixture")
    _ingest_claims(graph, tmp_path)
    assert [c.id for c in graph.nodes_by_type(NodeType.CLAIM)] == ["claim:x1"]


def test_ingest_claims_unexpected_shape_notes_gap(tmp_path: Path) -> None:
    (tmp_path / "claims.json").write_text(json.dumps({"claims": 5}), encoding="utf-8")
    graph = EvidenceGraph(project="fixture")
    _ingest_claims(graph, tmp_path)
    assert graph.nodes_by_type(NodeType.CLAIM) == []
    assert any("unexpected shape" in n for n in graph.notes)
