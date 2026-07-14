"""Tests for reproducibility.models module.

Covers WorkflowNode/WorkflowEdge/WorkflowGraph construction, the pure
build_workflow_graph resolution function (resolved vs. dangling
dependencies), dict round-trip serialization, and JSONL
serialize/append/deserialize/merge with real file I/O.
No mocks -- all tests use real data and real file I/O.
"""

from __future__ import annotations

from pathlib import Path

from reproducibility.models import (
    NodeType,
    WorkflowNode,
    WorkflowEdge,
    WorkflowGraph,
    build_workflow_graph,
    serialize_workflow_graphs,
    deserialize_workflow_graphs,
    merge_workflow_graphs,
    get_processed_paper_ids,
    append_workflow_graphs,
)


def _make_node(
    node_id: str = "n1",
    node_name: str = "Raw Dataset",
    node_type: NodeType = NodeType.SOURCE,
    source_quote: str = "We used the publicly available dataset X.",
    description: str = "The raw input dataset.",
    reproducibility_rating: int = 3,
    rationale: str = "Dataset is named but no version pinned.",
    depends_on: list[str] | None = None,
    paper_id: str = "doi:10.1234/repro",
) -> WorkflowNode:
    """Helper to build a WorkflowNode with sensible defaults."""
    return WorkflowNode(
        node_id=node_id,
        node_name=node_name,
        node_type=node_type,
        source_quote=source_quote,
        description=description,
        reproducibility_rating=reproducibility_rating,
        rationale=rationale,
        depends_on=list(depends_on) if depends_on is not None else [],
        paper_id=paper_id,
    )


class TestNodeType:
    """Validate NodeType enum values."""

    def test_values(self) -> None:
        """NodeType members should have the documented string values."""
        assert NodeType.SOURCE.value == "source"
        assert NodeType.METHOD.value == "method"
        assert NodeType.EXPERIMENT.value == "experiment"
        assert NodeType.SINK.value == "sink"

    def test_is_str_enum(self) -> None:
        """NodeType should be usable directly as a string."""
        assert NodeType.SOURCE == "source"
        assert str(NodeType.METHOD.value) == "method"


class TestWorkflowNodeDataclass:
    """Validate WorkflowNode construction and defaults."""

    def test_all_fields_set(self) -> None:
        """All fields should be accessible after construction."""
        n = _make_node()
        assert n.node_id == "n1"
        assert n.node_name == "Raw Dataset"
        assert n.node_type == NodeType.SOURCE
        assert n.source_quote == "We used the publicly available dataset X."
        assert n.description == "The raw input dataset."
        assert n.reproducibility_rating == 3
        assert n.rationale == "Dataset is named but no version pinned."
        assert n.depends_on == []
        assert n.paper_id == "doi:10.1234/repro"

    def test_defaults(self) -> None:
        """rationale, depends_on, and paper_id should have sensible defaults."""
        n = WorkflowNode(
            node_id="n2",
            node_name="Analysis Method",
            node_type=NodeType.METHOD,
            source_quote="We applied a t-test.",
            description="Statistical test.",
            reproducibility_rating=4,
        )
        assert n.rationale == ""
        assert n.depends_on == []
        assert n.paper_id == ""

    def test_depends_on_defaults_are_independent(self) -> None:
        """Each WorkflowNode's default depends_on list must be its own instance."""
        n1 = WorkflowNode(
            node_id="a",
            node_name="A",
            node_type=NodeType.SOURCE,
            source_quote="q",
            description="d",
            reproducibility_rating=1,
        )
        n2 = WorkflowNode(
            node_id="b",
            node_name="B",
            node_type=NodeType.SOURCE,
            source_quote="q",
            description="d",
            reproducibility_rating=1,
        )
        n1.depends_on.append("x")
        assert n2.depends_on == []


class TestWorkflowEdgeDataclass:
    """Validate WorkflowEdge construction and defaults."""

    def test_all_fields_set(self) -> None:
        """All fields should be accessible after construction."""
        e = WorkflowEdge(source_node_id="n1", target_node_id="n2", relation="feeds")
        assert e.source_node_id == "n1"
        assert e.target_node_id == "n2"
        assert e.relation == "feeds"

    def test_default_relation(self) -> None:
        """relation should default to 'dependency'."""
        e = WorkflowEdge(source_node_id="n1", target_node_id="n2")
        assert e.relation == "dependency"


class TestBuildWorkflowGraph:
    """Validate the pure build_workflow_graph resolution function."""

    def test_resolved_dependency_produces_edge(self) -> None:
        """A node depending on a known upstream node produces a resolved edge."""
        source = _make_node(node_id="source1", node_type=NodeType.SOURCE, depends_on=[])
        method = _make_node(
            node_id="method1",
            node_name="Preprocessing",
            node_type=NodeType.METHOD,
            depends_on=["source1"],
        )
        graph = build_workflow_graph("doi:10.1234/repro", [source, method])

        assert graph.paper_id == "doi:10.1234/repro"
        assert graph.dangling_reference_count == 0
        assert len(graph.edges) == 1
        edge = graph.edges[0]
        # Edge points FROM the depended-on (upstream) node TO the
        # depending (downstream) node -- see models.py module docstring.
        assert edge.source_node_id == "source1"
        assert edge.target_node_id == "method1"
        assert edge.relation == "dependency"

    def test_dangling_reference_produces_no_edge(self) -> None:
        """A depends_on entry that does not resolve is dropped and counted."""
        sink = _make_node(
            node_id="sink1",
            node_name="Final Output",
            node_type=NodeType.SINK,
            depends_on=["nonexistent_node"],
        )
        graph = build_workflow_graph("doi:10.1234/repro", [sink])

        assert graph.edges == []
        assert graph.dangling_reference_count == 1

    def test_mixed_resolved_and_dangling(self) -> None:
        """Resolved and dangling references in the same node are both handled."""
        source = _make_node(node_id="source1", node_type=NodeType.SOURCE)
        experiment = _make_node(
            node_id="exp1",
            node_name="Main Experiment",
            node_type=NodeType.EXPERIMENT,
            depends_on=["source1", "ghost_node"],
        )
        graph = build_workflow_graph("doi:10.1234/repro", [source, experiment])

        assert len(graph.edges) == 1
        assert graph.edges[0].source_node_id == "source1"
        assert graph.edges[0].target_node_id == "exp1"
        assert graph.dangling_reference_count == 1

    def test_source_out_degree_reflects_fan_out(self) -> None:
        """A SOURCE node that many nodes depend on accumulates out-edges."""
        source = _make_node(node_id="source1", node_type=NodeType.SOURCE)
        method_a = _make_node(node_id="method_a", node_type=NodeType.METHOD, depends_on=["source1"])
        method_b = _make_node(node_id="method_b", node_type=NodeType.METHOD, depends_on=["source1"])
        graph = build_workflow_graph("doi:10.1234/repro", [source, method_a, method_b])

        out_edges = [e for e in graph.edges if e.source_node_id == "source1"]
        assert len(out_edges) == 2
        assert {e.target_node_id for e in out_edges} == {"method_a", "method_b"}

    def test_sink_in_degree_reflects_fan_in(self) -> None:
        """A SINK node depending on a chain of upstream steps accumulates in-edges."""
        source = _make_node(node_id="source1", node_type=NodeType.SOURCE)
        method = _make_node(node_id="method1", node_type=NodeType.METHOD, depends_on=["source1"])
        sink = _make_node(
            node_id="sink1",
            node_type=NodeType.SINK,
            depends_on=["source1", "method1"],
        )
        graph = build_workflow_graph("doi:10.1234/repro", [source, method, sink])

        in_edges = [e for e in graph.edges if e.target_node_id == "sink1"]
        assert len(in_edges) == 2
        assert {e.source_node_id for e in in_edges} == {"source1", "method1"}

    def test_empty_nodes_produces_empty_graph(self) -> None:
        """Building from an empty node list should produce an empty graph."""
        graph = build_workflow_graph("doi:10.1234/empty", [])
        assert graph.nodes == []
        assert graph.edges == []
        assert graph.dangling_reference_count == 0

    def test_no_dependencies_produces_no_edges(self) -> None:
        """Nodes with empty depends_on produce no edges and no dangling count."""
        n1 = _make_node(node_id="n1", depends_on=[])
        n2 = _make_node(node_id="n2", depends_on=[])
        graph = build_workflow_graph("doi:10.1234/repro", [n1, n2])
        assert graph.edges == []
        assert graph.dangling_reference_count == 0

    def test_is_pure_does_not_mutate_input_nodes(self) -> None:
        """build_workflow_graph must not mutate the input node objects."""
        n1 = _make_node(node_id="n1", depends_on=["ghost"])
        original_depends_on = list(n1.depends_on)
        build_workflow_graph("doi:10.1234/repro", [n1])
        assert n1.depends_on == original_depends_on


class TestWorkflowGraphDictRoundTrip:
    """Validate WorkflowGraph.to_dict / from_dict round-trip."""

    def test_round_trip_preserves_all_fields(self) -> None:
        """Serializing then deserializing should recover all fields."""
        source = _make_node(node_id="source1", node_type=NodeType.SOURCE)
        sink = _make_node(
            node_id="sink1",
            node_type=NodeType.SINK,
            depends_on=["source1", "ghost"],
        )
        graph = build_workflow_graph("doi:10.1234/rt", [source, sink])

        d = graph.to_dict()
        restored = WorkflowGraph.from_dict(d)

        assert restored.paper_id == graph.paper_id
        assert restored.dangling_reference_count == graph.dangling_reference_count
        assert len(restored.nodes) == len(graph.nodes)
        assert len(restored.edges) == len(graph.edges)
        for original, r in zip(graph.nodes, restored.nodes):
            assert r.node_id == original.node_id
            assert r.node_name == original.node_name
            assert r.node_type == original.node_type
            assert isinstance(r.node_type, NodeType)
            assert r.source_quote == original.source_quote
            assert r.description == original.description
            assert r.reproducibility_rating == original.reproducibility_rating
            assert r.rationale == original.rationale
            assert r.depends_on == original.depends_on
            assert r.paper_id == original.paper_id
        for original, r in zip(graph.edges, restored.edges):
            assert r.source_node_id == original.source_node_id
            assert r.target_node_id == original.target_node_id
            assert r.relation == original.relation

    def test_to_dict_returns_dict_with_string_node_type(self) -> None:
        """to_dict should return a plain dict with node_type as a plain string."""
        node = _make_node(node_id="n1", node_type=NodeType.EXPERIMENT)
        graph = build_workflow_graph("doi:10.1/x", [node])
        d = graph.to_dict()
        assert isinstance(d, dict)
        assert d["nodes"][0]["node_type"] == "experiment"
        assert isinstance(d["nodes"][0]["node_type"], str)

    def test_from_dict_with_missing_optional_defaults(self) -> None:
        """Omitted optional node fields should fall back to defaults."""
        data = {
            "paper_id": "doi:10.1/manual",
            "nodes": [
                {
                    "node_id": "n1",
                    "node_name": "Manual Node",
                    "node_type": "method",
                    "source_quote": "quote",
                    "description": "desc",
                    "reproducibility_rating": 2,
                }
            ],
            "edges": [],
        }
        restored = WorkflowGraph.from_dict(data)
        assert restored.nodes[0].rationale == ""
        assert restored.nodes[0].depends_on == []
        assert restored.nodes[0].paper_id == ""
        assert restored.dangling_reference_count == 0

    def test_from_dict_missing_edge_relation_defaults(self) -> None:
        """Omitted edge 'relation' field should default to 'dependency'."""
        data = {
            "paper_id": "doi:10.1/manual2",
            "nodes": [],
            "edges": [{"source_node_id": "a", "target_node_id": "b"}],
        }
        restored = WorkflowGraph.from_dict(data)
        assert restored.edges[0].relation == "dependency"


class TestJSONLSerialization:
    """Validate serialize_workflow_graphs / deserialize_workflow_graphs with real files."""

    def test_round_trip_multiple(self, tmp_path: Path) -> None:
        """Serialize and deserialize multiple graphs via JSONL."""
        graphs = [
            build_workflow_graph(
                f"doi:10.1/ser{i}",
                [_make_node(node_id=f"n{i}", paper_id=f"doi:10.1/ser{i}")],
            )
            for i in range(5)
        ]

        filepath = tmp_path / "graphs.jsonl"
        lines = serialize_workflow_graphs(graphs)
        assert len(lines) == 5
        with open(filepath, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")

        loaded = deserialize_workflow_graphs(filepath)
        assert len(loaded) == 5
        for original, restored in zip(graphs, loaded):
            assert original.paper_id == restored.paper_id
            assert original.nodes[0].node_id == restored.nodes[0].node_id

    def test_empty_list(self, tmp_path: Path) -> None:
        """Serializing an empty list should produce a readable empty file."""
        filepath = tmp_path / "empty.jsonl"
        lines = serialize_workflow_graphs([])
        assert lines == []
        filepath.write_text("")
        loaded = deserialize_workflow_graphs(filepath)
        assert loaded == []

    def test_file_is_line_delimited(self, tmp_path: Path) -> None:
        """Each workflow graph should occupy exactly one line."""
        graphs = [
            build_workflow_graph(f"doi:10.1/line{i}", [_make_node(node_id=f"n{i}")]) for i in range(3)
        ]
        filepath = tmp_path / "lines.jsonl"
        lines = serialize_workflow_graphs(graphs)
        filepath.write_text("\n".join(lines) + "\n")
        text = filepath.read_text()
        non_empty = [ln for ln in text.strip().split("\n") if ln.strip()]
        assert len(non_empty) == 3


class TestMergeWorkflowGraphs:
    """Validate merge_workflow_graphs deduplication and accumulation."""

    def test_disjoint_lists_are_concatenated(self) -> None:
        """Merging disjoint lists should keep all entries."""
        g1 = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        g2 = build_workflow_graph("doi:10.2/b", [_make_node(node_id="n2")])
        merged = merge_workflow_graphs([g1], [g2])
        assert len(merged) == 2

    def test_duplicate_paper_id_new_wins(self) -> None:
        """When both lists contain the same paper_id, the new entry wins."""
        old = build_workflow_graph("doi:10.1/a", [_make_node(node_id="old_node")])
        new = build_workflow_graph("doi:10.1/a", [_make_node(node_id="new_node")])
        merged = merge_workflow_graphs([old], [new])
        assert len(merged) == 1
        assert merged[0].nodes[0].node_id == "new_node"

    def test_empty_existing_returns_new(self) -> None:
        """Merging into empty existing should return all new entries."""
        g = build_workflow_graph("doi:10.1/x", [_make_node(node_id="n1")])
        merged = merge_workflow_graphs([], [g])
        assert len(merged) == 1

    def test_empty_new_returns_existing(self) -> None:
        """Merging empty new into existing should return existing."""
        g = build_workflow_graph("doi:10.1/x", [_make_node(node_id="n1")])
        merged = merge_workflow_graphs([g], [])
        assert len(merged) == 1


class TestGetProcessedPaperIds:
    """Validate get_processed_paper_ids extracts unique paper IDs."""

    def test_extracts_unique_ids(self) -> None:
        """Should return set of unique paper IDs across all graphs."""
        g1 = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        g2 = build_workflow_graph("doi:10.2/b", [_make_node(node_id="n2")])
        ids = get_processed_paper_ids([g1, g2])
        assert ids == {"doi:10.1/a", "doi:10.2/b"}

    def test_empty_returns_empty_set(self) -> None:
        """Empty list should return empty set."""
        assert get_processed_paper_ids([]) == set()


class TestAppendWorkflowGraphs:
    """Validate append_workflow_graphs atomic incremental persistence."""

    def test_creates_fresh_file(self, tmp_path: Path) -> None:
        """append_workflow_graphs on a non-existent file creates it."""
        p = tmp_path / "new.jsonl"
        g = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        result = append_workflow_graphs([g], p)
        assert p.exists()
        assert result is None

        loaded = deserialize_workflow_graphs(p)
        assert len(loaded) == 1
        assert loaded[0].paper_id == "doi:10.1/a"

    def test_appends_to_existing(self, tmp_path: Path) -> None:
        """append_workflow_graphs merges with pre-existing entries on disk."""
        p = tmp_path / "existing.jsonl"
        g1 = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        with open(p, "w", encoding="utf-8") as fh:
            for line in serialize_workflow_graphs([g1]):
                fh.write(line + "\n")

        g2 = build_workflow_graph("doi:10.2/b", [_make_node(node_id="n2")])
        append_workflow_graphs([g2], p)

        reloaded = deserialize_workflow_graphs(p)
        assert len(reloaded) == 2
        ids = {g.paper_id for g in reloaded}
        assert ids == {"doi:10.1/a", "doi:10.2/b"}

    def test_deduplicates_new_wins(self, tmp_path: Path) -> None:
        """append_workflow_graphs deduplicates by paper_id; new wins."""
        p = tmp_path / "dedup.jsonl"
        old = build_workflow_graph("doi:10.1/a", [_make_node(node_id="old_node")])
        with open(p, "w", encoding="utf-8") as fh:
            for line in serialize_workflow_graphs([old]):
                fh.write(line + "\n")

        new = build_workflow_graph("doi:10.1/a", [_make_node(node_id="new_node")])
        append_workflow_graphs([new], p)

        reloaded = deserialize_workflow_graphs(p)
        assert len(reloaded) == 1
        assert reloaded[0].nodes[0].node_id == "new_node"

    def test_atomicity_no_tmp_left(self, tmp_path: Path) -> None:
        """After append_workflow_graphs completes, no .tmp file should remain."""
        p = tmp_path / "atomic.jsonl"
        g = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        append_workflow_graphs([g], p)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """append_workflow_graphs should create missing parent directories."""
        p = tmp_path / "sub" / "dir" / "graphs.jsonl"
        g = build_workflow_graph("doi:10.1/a", [_make_node(node_id="n1")])
        append_workflow_graphs([g], p)
        assert p.exists()
        loaded = deserialize_workflow_graphs(p)
        assert len(loaded) == 1

    def test_logs_file_path_and_count(self, tmp_path: Path, caplog) -> None:
        """append_workflow_graphs logs the graph count and file path."""
        import logging

        p = tmp_path / "logged.jsonl"
        g = build_workflow_graph("doi:10.1/log", [_make_node(node_id="n1")])
        with caplog.at_level(logging.INFO, logger="reproducibility.models"):
            append_workflow_graphs([g], p)
        assert any("Wrote 1 workflow graphs" in m for m in caplog.messages)
        assert any(str(p) in m for m in caplog.messages)


class TestFullPipelineRealPaperShape:
    """End-to-end shaped scenario resembling a real paper's extracted workflow."""

    def test_source_method_experiment_sink_chain(self, tmp_path: Path) -> None:
        """A realistic 4-node chain resolves edges correctly and round-trips."""
        source = _make_node(
            node_id="raw_data",
            node_name="Raw EEG Recordings",
            node_type=NodeType.SOURCE,
            source_quote="EEG data were collected from 24 participants.",
            description="Raw multi-channel EEG recordings.",
            reproducibility_rating=2,
            rationale="Sample size given but no raw-data repository link.",
            paper_id="doi:10.1/chain",
        )
        method = _make_node(
            node_id="preprocessing",
            node_name="Bandpass Filtering",
            node_type=NodeType.METHOD,
            source_quote="Signals were bandpass filtered between 1-40 Hz.",
            description="Standard preprocessing pipeline.",
            reproducibility_rating=4,
            depends_on=["raw_data"],
            paper_id="doi:10.1/chain",
        )
        experiment = _make_node(
            node_id="classification",
            node_name="SVM Classification",
            node_type=NodeType.EXPERIMENT,
            source_quote="We trained an SVM classifier with RBF kernel.",
            description="Binary classification experiment.",
            reproducibility_rating=3,
            depends_on=["preprocessing", "missing_hyperparam_doc"],
            paper_id="doi:10.1/chain",
        )
        sink = _make_node(
            node_id="results_table",
            node_name="Accuracy Table",
            node_type=NodeType.SINK,
            source_quote="Table 2 reports classification accuracy.",
            description="Final reported results.",
            reproducibility_rating=4,
            depends_on=["classification"],
            paper_id="doi:10.1/chain",
        )

        graph = build_workflow_graph("doi:10.1/chain", [source, method, experiment, sink])

        assert len(graph.nodes) == 4
        assert len(graph.edges) == 3
        assert graph.dangling_reference_count == 1

        # Source fan-out: raw_data feeds exactly one downstream node here.
        source_out = [e for e in graph.edges if e.source_node_id == "raw_data"]
        assert len(source_out) == 1
        assert source_out[0].target_node_id == "preprocessing"

        # Sink fan-in: results_table depends on exactly one upstream node.
        sink_in = [e for e in graph.edges if e.target_node_id == "results_table"]
        assert len(sink_in) == 1
        assert sink_in[0].source_node_id == "classification"

        # Persist, append a second paper, and reload from disk.
        p = tmp_path / "pipeline.jsonl"
        append_workflow_graphs([graph], p)

        other_source = _make_node(node_id="s2", paper_id="doi:10.2/other")
        other_graph = build_workflow_graph("doi:10.2/other", [other_source])
        append_workflow_graphs([other_graph], p)

        reloaded = deserialize_workflow_graphs(p)
        assert get_processed_paper_ids(reloaded) == {"doi:10.1/chain", "doi:10.2/other"}
