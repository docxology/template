"""Tests for infrastructure.provenance.store and models."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.provenance import (
    ArtifactNode,
    ClaimNode,
    Edge,
    EdgeRelation,
    NodeKind,
    Provenance,
    RunNode,
    SourceNode,
    node_from_dict,
)


# ---------------------------------------------------------------------------
# model helpers
# ---------------------------------------------------------------------------

class TestNodeKind:
    def test_values(self):
        assert set(NodeKind) == {
            NodeKind.artifact,
            NodeKind.run,
            NodeKind.source,
            NodeKind.claim,
        }

    def test_str_enum(self):
        assert NodeKind.artifact == "artifact"


class TestEdgeRelation:
    def test_values_exist(self):
        rels = {r.value for r in EdgeRelation}
        assert "derived_from" in rels
        assert "produced_by" in rels
        assert "supports" in rels


class TestArtifactNode:
    def test_create(self):
        n = ArtifactNode.create("fig1.pdf", path="output/fig1.pdf")
        assert n.kind == NodeKind.artifact
        assert n.path == "output/fig1.pdf"
        assert len(n.node_id) == 32

    def test_content_address_stable(self):
        n1 = ArtifactNode.create("fig1.pdf", path="output/fig1.pdf")
        n2 = ArtifactNode.create("fig1.pdf", path="output/fig1.pdf")
        assert n1.node_id == n2.node_id

    def test_different_paths_different_ids(self):
        n1 = ArtifactNode.create("fig1.pdf", path="a.pdf")
        n2 = ArtifactNode.create("fig1.pdf", path="b.pdf")
        assert n1.node_id != n2.node_id

    def test_to_dict(self):
        n = ArtifactNode.create("fig", path="x.pdf", content_hash="abc123")
        d = n.to_dict()
        assert d["kind"] == "artifact"
        assert d["path"] == "x.pdf"
        assert d["content_hash"] == "abc123"


class TestRunNode:
    def test_create(self):
        n = RunNode.create("analysis", command="python analysis.py", exit_code=0)
        assert n.kind == NodeKind.run
        assert n.command == "python analysis.py"
        assert n.exit_code == 0

    def test_to_dict(self):
        n = RunNode.create("r", command="cmd", duration_seconds=5.5)
        d = n.to_dict()
        assert d["duration_seconds"] == 5.5


class TestSourceNode:
    def test_create(self):
        n = SourceNode.create("paper1", uri="https://doi.org/10.1234/abc")
        assert n.kind == NodeKind.source
        assert n.uri == "https://doi.org/10.1234/abc"

    def test_source_type_default(self):
        n = SourceNode.create("s", uri="http://x.com")
        assert n.source_type == "generic"


class TestClaimNode:
    def test_create(self):
        n = ClaimNode.create("claim1", "CRISPR increases efficiency by 20%", confidence=0.8)
        assert n.kind == NodeKind.claim
        assert n.confidence == 0.8

    def test_to_dict(self):
        n = ClaimNode.create("c", "Text", confidence=0.5)
        d = n.to_dict()
        assert d["confidence"] == 0.5
        assert d["claim_text"] == "Text"


class TestEdge:
    def test_frozen(self):
        e = Edge(from_id="a", to_id="b", relation=EdgeRelation.derived_from)
        with pytest.raises((AttributeError, TypeError)):
            e.from_id = "x"  # type: ignore[misc]

    def test_to_dict(self):
        e = Edge(from_id="a", to_id="b", relation=EdgeRelation.supports)
        d = e.to_dict()
        assert d["relation"] == "supports"


class TestNodeFromDict:
    def test_artifact_round_trip(self):
        n = ArtifactNode.create("f", path="x.pdf", content_hash="h")
        n.created_at = "2024-01-01T00:00:00+00:00"
        restored = node_from_dict(n.to_dict())
        assert isinstance(restored, ArtifactNode)
        assert restored.path == "x.pdf"

    def test_run_round_trip(self):
        n = RunNode.create("r", command="cmd", exit_code=1)
        n.created_at = "2024-01-01T00:00:00+00:00"
        restored = node_from_dict(n.to_dict())
        assert isinstance(restored, RunNode)
        assert restored.exit_code == 1

    def test_source_round_trip(self):
        n = SourceNode.create("s", uri="http://x.com", source_type="paper")
        n.created_at = "2024-01-01T00:00:00+00:00"
        restored = node_from_dict(n.to_dict())
        assert isinstance(restored, SourceNode)
        assert restored.source_type == "paper"

    def test_claim_round_trip(self):
        n = ClaimNode.create("c", "claim text", confidence=0.7)
        n.created_at = "2024-01-01T00:00:00+00:00"
        restored = node_from_dict(n.to_dict())
        assert isinstance(restored, ClaimNode)
        assert restored.confidence == 0.7

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="Unknown node kind"):
            node_from_dict({"kind": "bogus", "node_id": "x", "label": "y"})


# ---------------------------------------------------------------------------
# store.py
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_record_and_get(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ArtifactNode.create("fig", path="fig.pdf")
        prov.record(n)
        retrieved = prov.get(n.node_id)
        assert retrieved is not None
        assert retrieved.node_id == n.node_id

    def test_record_idempotent(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ArtifactNode.create("fig", path="fig.pdf")
        prov.record(n)
        prov.record(n)  # second call should not raise
        assert len(prov) == 1

    def test_link(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        run = RunNode.create("r", command="cmd")
        art = ArtifactNode.create("a", path="a.pdf")
        prov.record(run)
        prov.record(art)
        edge = prov.link(run.node_id, art.node_id, EdgeRelation.produced_by)
        assert edge.relation == EdgeRelation.produced_by

    def test_link_missing_from_raises(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        art = ArtifactNode.create("a", path="a.pdf")
        prov.record(art)
        with pytest.raises(KeyError, match="ghost"):
            prov.link("ghost", art.node_id, EdgeRelation.derived_from)

    def test_link_missing_to_raises(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        run = RunNode.create("r", command="cmd")
        prov.record(run)
        with pytest.raises(KeyError, match="ghost"):
            prov.link(run.node_id, "ghost", EdgeRelation.produced_by)

    def test_link_idempotent(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n1 = ArtifactNode.create("a", path="a.pdf")
        n2 = ArtifactNode.create("b", path="b.pdf")
        prov.record(n1)
        prov.record(n2)
        prov.link(n1.node_id, n2.node_id, EdgeRelation.derived_from)
        prov.link(n1.node_id, n2.node_id, EdgeRelation.derived_from)
        edges = prov.query(from_id=n1.node_id)
        assert len(edges) == 1

    def test_list_all(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        prov.record(ArtifactNode.create("a", path="a"))
        prov.record(RunNode.create("r", command="c"))
        nodes = prov.list()
        assert len(nodes) == 2

    def test_list_by_kind(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        prov.record(ArtifactNode.create("a", path="a"))
        prov.record(RunNode.create("r", command="c"))
        artifacts = prov.list(kind=NodeKind.artifact)
        assert len(artifacts) == 1
        assert all(n.kind == NodeKind.artifact for n in artifacts)

    def test_query_by_relation(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n1 = SourceNode.create("s", uri="http://x.com")
        n2 = ClaimNode.create("c", "claim")
        prov.record(n1)
        prov.record(n2)
        prov.link(n1.node_id, n2.node_id, EdgeRelation.supports)
        prov.link(n1.node_id, n2.node_id, EdgeRelation.cites)
        supports = prov.query(relation=EdgeRelation.supports)
        assert len(supports) == 1
        assert supports[0].relation == EdgeRelation.supports

    def test_clear(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        prov.record(ArtifactNode.create("a", path="a"))
        n1, n2 = (
            ArtifactNode.create("x", path="x"),
            ArtifactNode.create("y", path="y"),
        )
        prov.record(n1)
        prov.record(n2)
        prov.link(n1.node_id, n2.node_id, EdgeRelation.derived_from)
        removed = prov.clear()
        assert removed == (3, 1)
        assert len(prov) == 0

    def test_persistence_round_trip(self, tmp_path):
        dag_path = tmp_path / "dag.json"
        prov1 = Provenance(dag_path)
        n = ArtifactNode.create("fig", path="f.pdf")
        prov1.record(n)

        # Reload from disk
        prov2 = Provenance(dag_path)
        assert prov2.get(n.node_id) is not None
        assert len(prov2) == 1

    def test_atomic_write_creates_parent(self, tmp_path):
        nested = tmp_path / "deep" / "nested"
        prov = Provenance.with_path(nested)
        prov.record(ArtifactNode.create("x", path="x"))
        assert (nested / "dag.json").exists()

    def test_created_at_set_on_first_record(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ArtifactNode.create("a", path="a")
        assert n.created_at == ""  # not yet set
        prov.record(n)
        assert n.created_at != ""

    def test_get_missing_returns_none(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        assert prov.get("nonexistent") is None

    def test_iter(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        prov.record(ArtifactNode.create("a", path="a"))
        prov.record(RunNode.create("r", command="c"))
        nodes = list(prov)
        assert len(nodes) == 2

    def test_repr(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        r = repr(prov)
        assert "Provenance" in r

    def test_path_property(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        assert isinstance(prov.path, Path)

    def test_corrupted_json_loads_empty(self, tmp_path):
        dag = tmp_path / "dag.json"
        dag.write_text("{not valid json")
        prov = Provenance(dag)
        assert len(prov) == 0
