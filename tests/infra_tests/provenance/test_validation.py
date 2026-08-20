"""Tests for Provenance DAG validation logic."""

from __future__ import annotations

from pathlib import Path

from infrastructure.provenance.models import (
    ArtifactNode,
    ClaimNode,
    EdgeRelation,
    RunNode,
    SourceNode,
)
from infrastructure.provenance.store import Provenance
from infrastructure.provenance.validation import validate_provenance_dag


def test_valid_dag_passes(tmp_path: Path) -> None:
    store = Provenance(tmp_path / "dag.json")
    src = SourceNode.create(label="dataset", uri="https://example.com/data.csv")
    run = RunNode.create(label="train", command="python train.py")
    art = ArtifactNode.create(label="model", path="output/model.pkl", content_hash="abc123")
    claim = ClaimNode.create(label="accuracy", claim_text="Acc > 95%", confidence=0.98)

    store.record(src)
    store.record(run)
    store.record(art)
    store.record(claim)

    store.link(src.node_id, run.node_id, EdgeRelation.depends_on)
    store.link(run.node_id, art.node_id, EdgeRelation.produced_by)
    store.link(art.node_id, claim.node_id, EdgeRelation.supports)

    report = validate_provenance_dag(store)
    assert report.is_valid
    assert len(report.errors) == 0
    assert report.total_nodes == 4
    assert report.total_edges == 3


def test_self_loop_detected(tmp_path: Path) -> None:
    store = Provenance(tmp_path / "dag.json")
    run = RunNode.create(label="step", command="step.sh")
    store.record(run)

    # Inject self-referential edge
    store.link(run.node_id, run.node_id, EdgeRelation.depends_on)

    report = validate_provenance_dag(store)
    assert not report.is_valid
    codes = [f.code for f in report.errors]
    assert "PROV_SELF_LOOP" in codes


def test_cycle_detected(tmp_path: Path) -> None:
    store = Provenance(tmp_path / "dag.json")
    a = RunNode.create(label="a", command="a.sh")
    b = RunNode.create(label="b", command="b.sh")
    c = RunNode.create(label="c", command="c.sh")

    store.record(a)
    store.record(b)
    store.record(c)

    store.link(a.node_id, b.node_id, EdgeRelation.depends_on)
    store.link(b.node_id, c.node_id, EdgeRelation.depends_on)
    store.link(c.node_id, a.node_id, EdgeRelation.depends_on)

    report = validate_provenance_dag(store)
    assert not report.is_valid
    codes = [f.code for f in report.errors]
    assert "PROV_CYCLE_DETECTED" in codes


def test_isolated_node_warning(tmp_path: Path) -> None:
    store = Provenance(tmp_path / "dag.json")
    art = ArtifactNode.create(label="unlinked", path="output/data.csv", content_hash="hash")
    store.record(art)

    report = validate_provenance_dag(store)
    assert report.is_valid  # Warnings don't fail valid status
    codes = [f.code for f in report.warnings]
    assert "PROV_ISOLATED_NODE" in codes
