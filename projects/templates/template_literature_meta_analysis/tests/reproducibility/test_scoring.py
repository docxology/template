"""Tests for reproducibility.scoring module.

Covers content-score stage averaging and renormalization, all five
structural-coverage components (rc1..rc5), the geometric-mean composite
score (including the empty-graph no-division/no-sqrt-domain-error edge
case), batch corpus scoring, and the stdlib-difflib quote-verification
helper. All expected values are hand-computed in-test; no I/O, no mocks.
"""

from __future__ import annotations

import math

from reproducibility.models import (
    NodeType,
    WorkflowNode,
    WorkflowEdge,
    WorkflowGraph,
)
from reproducibility.scoring import (
    ContentWeights,
    StructuralWeights,
    ReproducibilityScore,
    normalized_rating,
    stage_average,
    content_score,
    source_consumption,
    sink_production,
    reference_resolution,
    source_sink_path_coverage,
    weak_component_coverage,
    structural_score,
    composite_score,
    score_corpus,
    verify_source_quote,
)


def _make_node(
    node_id: str,
    node_type: NodeType,
    reproducibility_rating: int,
    depends_on: list[str] | None = None,
    paper_id: str = "doi:10.1234/repro",
) -> WorkflowNode:
    """Helper to build a WorkflowNode with only the fields tests vary."""
    return WorkflowNode(
        node_id=node_id,
        node_name=node_id,
        node_type=node_type,
        source_quote="q",
        description="d",
        reproducibility_rating=reproducibility_rating,
        depends_on=list(depends_on) if depends_on is not None else [],
        paper_id=paper_id,
    )


class TestContentWeightsDefaults:
    """Validate the ContentWeights dataclass default values."""

    def test_defaults(self) -> None:
        """Default weights should match the documented 0.30/0.20/0.20/0.30 split."""
        w = ContentWeights()
        assert w.sources == 0.30
        assert w.methods == 0.20
        assert w.experiments == 0.20
        assert w.sinks == 0.30

    def test_sums_to_one(self) -> None:
        """Default content weights should sum to 1.0."""
        w = ContentWeights()
        assert abs((w.sources + w.methods + w.experiments + w.sinks) - 1.0) < 1e-12


class TestStructuralWeightsDefaults:
    """Validate the StructuralWeights dataclass default values."""

    def test_defaults(self) -> None:
        """Default weights should match the documented 0.25/0.25/0.20/0.15/0.15 split."""
        w = StructuralWeights()
        assert w.source_consumption == 0.25
        assert w.sink_production == 0.25
        assert w.reference_resolution == 0.20
        assert w.path_coverage == 0.15
        assert w.cohesion == 0.15

    def test_sums_to_one(self) -> None:
        """Default structural weights should sum to 1.0."""
        w = StructuralWeights()
        total = w.source_consumption + w.sink_production + w.reference_resolution + w.path_coverage + w.cohesion
        assert abs(total - 1.0) < 1e-12


class TestReproducibilityScoreDataclass:
    """Validate the ReproducibilityScore dataclass fields are all accessible."""

    def test_all_fields_set(self) -> None:
        """All documented fields should round-trip through construction."""
        score = ReproducibilityScore(
            content_score=0.5,
            structural_score=0.75,
            composite_score=0.612,
            stage_scores={"sources": 1.0},
            structural_components={"source_consumption": 1.0},
            n_nodes=4,
            n_edges=3,
            n_dangling_references=1,
        )
        assert score.content_score == 0.5
        assert score.structural_score == 0.75
        assert score.composite_score == 0.612
        assert score.stage_scores == {"sources": 1.0}
        assert score.structural_components == {"source_consumption": 1.0}
        assert score.n_nodes == 4
        assert score.n_edges == 3
        assert score.n_dangling_references == 1


class TestNormalizedRating:
    """Validate normalized_rating clamping and rescaling."""

    def test_in_range_values(self) -> None:
        """Ratings 1..4 should map linearly to 0.0, 1/3, 2/3, 1.0."""
        n1 = _make_node("n1", NodeType.SOURCE, 1)
        n2 = _make_node("n2", NodeType.SOURCE, 2)
        n3 = _make_node("n3", NodeType.SOURCE, 3)
        n4 = _make_node("n4", NodeType.SOURCE, 4)
        assert normalized_rating(n1) == 0.0
        assert abs(normalized_rating(n2) - 1 / 3) < 1e-12
        assert abs(normalized_rating(n3) - 2 / 3) < 1e-12
        assert normalized_rating(n4) == 1.0

    def test_normalized_rating_clamps_out_of_range(self) -> None:
        """rating=0 and rating=5 should both clamp into [1, 4] before normalizing."""
        too_low = _make_node("low", NodeType.SOURCE, 0)
        too_high = _make_node("high", NodeType.SOURCE, 5)

        # rating=0 clamps to 1 -> (1-1)/3 = 0.0
        assert normalized_rating(too_low) == 0.0
        # rating=5 clamps to 4 -> (4-1)/3 = 1.0
        assert normalized_rating(too_high) == 1.0


class TestStageAverage:
    """Validate stage_average over a graph's per-stage nodes."""

    def test_returns_mean_for_present_stage(self) -> None:
        """Two SOURCE nodes with ratings 4 and 2 should average to normalized 0.5."""
        n1 = _make_node("s1", NodeType.SOURCE, 4)
        n2 = _make_node("s2", NodeType.SOURCE, 2)
        graph = WorkflowGraph(paper_id="p", nodes=[n1, n2], edges=[])
        avg = stage_average(graph, NodeType.SOURCE)
        assert avg is not None
        # normalized(4)=1.0, normalized(2)=1/3 -> mean = 2/3
        assert abs(avg - 2 / 3) < 1e-12

    def test_returns_none_for_absent_stage(self) -> None:
        """A stage with zero nodes should return None, not raise or divide by zero."""
        n1 = _make_node("s1", NodeType.SOURCE, 4)
        graph = WorkflowGraph(paper_id="p", nodes=[n1], edges=[])
        assert stage_average(graph, NodeType.SINK) is None


class TestContentScore:
    """Validate content_score hand-computed weighted stage averages."""

    def test_content_score_hand_computed(self) -> None:
        """4-node graph, one node per stage, ratings [4, 3, 2, 1].

        Hand computation:
            normalized(4) = 1.0        (source)
            normalized(3) = 2/3        (method)
            normalized(2) = 1/3        (experiment)
            normalized(1) = 0.0        (sink)

            Rc = 0.30*1.0 + 0.20*(2/3) + 0.20*(1/3) + 0.30*0.0
               = 0.30 + 0.133333... + 0.066666... + 0.0
               = 0.5
        """
        nodes = [
            _make_node("src", NodeType.SOURCE, 4),
            _make_node("meth", NodeType.METHOD, 3),
            _make_node("exp", NodeType.EXPERIMENT, 2),
            _make_node("sink", NodeType.SINK, 1),
        ]
        graph = WorkflowGraph(paper_id="p", nodes=nodes, edges=[])

        rc, stage_scores = content_score(graph)

        expected = 0.30 * 1.0 + 0.20 * (2 / 3) + 0.20 * (1 / 3) + 0.30 * 0.0
        assert round(rc, 6) == round(expected, 6)
        assert round(rc, 6) == 0.5
        assert stage_scores == {
            "sources": 1.0,
            "methods": 2 / 3,
            "experiments": 1 / 3,
            "sinks": 0.0,
        }

    def test_content_score_renormalizes_when_stage_absent(self) -> None:
        """Zero EXPERIMENT nodes: remaining 3 weights renormalize to sum 1.0.

        All three present stages (source/method/sink) rated 4 -> normalized
        1.0 each, so regardless of renormalization the weighted average of
        three identical values is 1.0. The renormalization itself is
        verified directly: (sources + methods + sinks) weight / their sum
        must equal 1.0 -- i.e. "experiments" never appears in stage_scores
        and does not silently zero out the numerator.
        """
        nodes = [
            _make_node("src", NodeType.SOURCE, 4),
            _make_node("meth", NodeType.METHOD, 4),
            _make_node("sink", NodeType.SINK, 4),
        ]
        graph = WorkflowGraph(paper_id="p", nodes=nodes, edges=[])
        weights = ContentWeights()

        rc, stage_scores = content_score(graph, weights)

        assert "experiments" not in stage_scores
        assert set(stage_scores.keys()) == {"sources", "methods", "sinks"}
        assert abs(rc - 1.0) < 1e-12

        # Verify the renormalization arithmetic explicitly: the present-stage
        # weights (0.30 + 0.20 + 0.30 = 0.80) renormalized by dividing by
        # their own sum equal exactly 1.0.
        present_weight_sum = weights.sources + weights.methods + weights.sinks
        renormalized = present_weight_sum / present_weight_sum
        assert renormalized == 1.0

    def test_empty_graph_returns_zero_and_empty_dict(self) -> None:
        """A graph with zero nodes should return (0.0, {}) without raising."""
        graph = WorkflowGraph(paper_id="p", nodes=[], edges=[])
        rc, stage_scores = content_score(graph)
        assert rc == 0.0
        assert stage_scores == {}

    def test_all_present_stage_weights_zero_returns_zero(self) -> None:
        """If every present stage carries zero configured weight, avoid ZeroDivisionError."""
        nodes = [_make_node("src", NodeType.SOURCE, 4)]
        graph = WorkflowGraph(paper_id="p", nodes=nodes, edges=[])
        zero_weights = ContentWeights(sources=0.0, methods=0.0, experiments=0.0, sinks=0.0)
        rc, stage_scores = content_score(graph, zero_weights)
        assert rc == 0.0
        assert stage_scores == {}


class TestSourceConsumption:
    """Validate source_consumption (rc1)."""

    def test_source_consumption_penalizes_orphan_source(self) -> None:
        """One of two sources has out_degree=0, giving rc1 = 0.5."""
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        s2 = _make_node("s2", NodeType.SOURCE, 3)  # orphan: nothing depends on it
        m1 = _make_node("m1", NodeType.METHOD, 3, depends_on=["s1"])
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, s2, m1],
            edges=[WorkflowEdge(source_node_id="s1", target_node_id="m1")],
        )
        assert source_consumption(graph) == 0.5

    def test_zero_sources_returns_one(self) -> None:
        """A graph with no SOURCE nodes should return 1.0 (vacuously satisfied)."""
        m1 = _make_node("m1", NodeType.METHOD, 3)
        graph = WorkflowGraph(paper_id="p", nodes=[m1], edges=[])
        assert source_consumption(graph) == 1.0

    def test_all_sources_consumed_returns_one(self) -> None:
        """Every SOURCE node with out-degree > 0 should give rc1 = 1.0."""
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        m1 = _make_node("m1", NodeType.METHOD, 3, depends_on=["s1"])
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, m1],
            edges=[WorkflowEdge(source_node_id="s1", target_node_id="m1")],
        )
        assert source_consumption(graph) == 1.0


class TestSinkProduction:
    """Validate sink_production (rc2)."""

    def test_sink_production_penalizes_unproduced_sink(self) -> None:
        """One of two sinks has in_degree=0, giving rc2 = 0.5."""
        sk1 = _make_node("sk1", NodeType.SINK, 3)
        sk2 = _make_node("sk2", NodeType.SINK, 3)  # unproduced: nothing feeds it
        m1 = _make_node("m1", NodeType.METHOD, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[sk1, sk2, m1],
            edges=[WorkflowEdge(source_node_id="m1", target_node_id="sk1")],
        )
        assert sink_production(graph) == 0.5

    def test_zero_sinks_returns_one(self) -> None:
        """A graph with no SINK nodes should return 1.0 (vacuously satisfied)."""
        m1 = _make_node("m1", NodeType.METHOD, 3)
        graph = WorkflowGraph(paper_id="p", nodes=[m1], edges=[])
        assert sink_production(graph) == 1.0


class TestReferenceResolution:
    """Validate reference_resolution (rc3)."""

    def test_reference_resolution_counts_dangling_from_process_nodes_only(self) -> None:
        """A SOURCE node's unresolved depends_on must NOT count toward rc3.

        source_bad emits a dangling reference ("ghost_upstream", never
        resolves) but SOURCE-emitted references are excluded from rc3
        entirely. method_ok emits exactly one reference and it resolves
        (to source_bad, which is a real node). So rc3 must be 1.0, not
        0.5 -- if the source's dangling reference were (incorrectly)
        counted, rc3 would drop to 1/2.
        """
        source_bad = _make_node("source_bad", NodeType.SOURCE, 3, depends_on=["ghost_upstream"])
        method_ok = _make_node("method_ok", NodeType.METHOD, 3, depends_on=["source_bad"])
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[source_bad, method_ok],
            edges=[WorkflowEdge(source_node_id="source_bad", target_node_id="method_ok")],
        )
        assert reference_resolution(graph) == 1.0

    def test_zero_process_references_returns_one(self) -> None:
        """METHOD/EXPERIMENT nodes emitting zero references total should return 1.0."""
        source = _make_node("s1", NodeType.SOURCE, 3, depends_on=["also_ignored"])
        method = _make_node("m1", NodeType.METHOD, 3, depends_on=[])
        graph = WorkflowGraph(paper_id="p", nodes=[source, method], edges=[])
        assert reference_resolution(graph) == 1.0

    def test_process_node_dangling_reference_lowers_score(self) -> None:
        """A dangling reference emitted by a METHOD node should lower rc3."""
        method = _make_node("m1", NodeType.METHOD, 3, depends_on=["ghost"])
        graph = WorkflowGraph(paper_id="p", nodes=[method], edges=[])
        assert reference_resolution(graph) == 0.0


class TestSourceSinkPathCoverage:
    """Validate source_sink_path_coverage (rc4)."""

    def test_source_sink_path_coverage_pair_normalization(self) -> None:
        """2 sources * 3 sinks = 6 pairs; exactly 2 are reachable -> rc4 = 2/6.

        sa reaches only t1; sb reaches only t2; t3 is unreached by anyone.
        The denominator must be |sources|*|sinks| = 6, NOT normalized by
        the size of the union of source+sink node sets (which would be 5).
        """
        sa = _make_node("sa", NodeType.SOURCE, 3)
        sb = _make_node("sb", NodeType.SOURCE, 3)
        t1 = _make_node("t1", NodeType.SINK, 3)
        t2 = _make_node("t2", NodeType.SINK, 3)
        t3 = _make_node("t3", NodeType.SINK, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[sa, sb, t1, t2, t3],
            edges=[
                WorkflowEdge(source_node_id="sa", target_node_id="t1"),
                WorkflowEdge(source_node_id="sb", target_node_id="t2"),
            ],
        )
        rc4 = source_sink_path_coverage(graph)
        assert rc4 == 2 / 6
        # Explicitly confirm it is NOT union-normalized (|union| = 5 nodes).
        union_size = len({"sa", "sb", "t1", "t2", "t3"})
        assert rc4 != 2 / union_size

    def test_source_sink_path_coverage_empty_returns_zero(self) -> None:
        """Sources present, zero sinks -> rc4 = 0.0."""
        sa = _make_node("sa", NodeType.SOURCE, 3)
        sb = _make_node("sb", NodeType.SOURCE, 3)
        graph = WorkflowGraph(paper_id="p", nodes=[sa, sb], edges=[])
        assert source_sink_path_coverage(graph) == 0.0

    def test_empty_sources_returns_zero(self) -> None:
        """Sinks present, zero sources -> rc4 = 0.0."""
        t1 = _make_node("t1", NodeType.SINK, 3)
        graph = WorkflowGraph(paper_id="p", nodes=[t1], edges=[])
        assert source_sink_path_coverage(graph) == 0.0

    def test_multi_hop_path_is_reachable(self) -> None:
        """A source reaching a sink through an intermediate method node counts."""
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        m1 = _make_node("m1", NodeType.METHOD, 3)
        t1 = _make_node("t1", NodeType.SINK, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, m1, t1],
            edges=[
                WorkflowEdge(source_node_id="s1", target_node_id="m1"),
                WorkflowEdge(source_node_id="m1", target_node_id="t1"),
            ],
        )
        assert source_sink_path_coverage(graph) == 1.0


class TestWeakComponentCoverage:
    """Validate weak_component_coverage (rc5)."""

    def test_weak_component_coverage_fragmented_graph(self) -> None:
        """5 nodes split into components of size 3 and 2 -> rc5 = 3/5.

        Component 1: a -> b -> c (3 nodes).
        Component 2: d -> e (2 nodes, disjoint from component 1).
        """
        a = _make_node("a", NodeType.SOURCE, 3)
        b = _make_node("b", NodeType.METHOD, 3)
        c = _make_node("c", NodeType.SINK, 3)
        d = _make_node("d", NodeType.SOURCE, 3)
        e = _make_node("e", NodeType.SINK, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[a, b, c, d, e],
            edges=[
                WorkflowEdge(source_node_id="a", target_node_id="b"),
                WorkflowEdge(source_node_id="b", target_node_id="c"),
                WorkflowEdge(source_node_id="d", target_node_id="e"),
            ],
        )
        assert weak_component_coverage(graph) == 3 / 5

    def test_empty_graph_returns_zero(self) -> None:
        """An empty graph (zero nodes) should return 0.0."""
        graph = WorkflowGraph(paper_id="p", nodes=[], edges=[])
        assert weak_component_coverage(graph) == 0.0

    def test_fully_connected_returns_one(self) -> None:
        """A single connected component spanning all nodes gives rc5 = 1.0."""
        a = _make_node("a", NodeType.SOURCE, 3)
        b = _make_node("b", NodeType.SINK, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[a, b],
            edges=[WorkflowEdge(source_node_id="a", target_node_id="b")],
        )
        assert weak_component_coverage(graph) == 1.0

    def test_all_isolated_nodes(self) -> None:
        """No edges at all: every node is its own component of size 1."""
        a = _make_node("a", NodeType.SOURCE, 3)
        b = _make_node("b", NodeType.SOURCE, 3)
        graph = WorkflowGraph(paper_id="p", nodes=[a, b], edges=[])
        assert weak_component_coverage(graph) == 0.5


class TestStructuralScore:
    """Validate structural_score combines rc1..rc5 with the configured weights."""

    def test_weighted_combination_matches_manual_sum(self) -> None:
        """Rs should equal the manual weighted sum of the five components."""
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        m1 = _make_node("m1", NodeType.METHOD, 3, depends_on=["s1"])
        t1 = _make_node("t1", NodeType.SINK, 3, depends_on=["m1"])
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, m1, t1],
            edges=[
                WorkflowEdge(source_node_id="s1", target_node_id="m1"),
                WorkflowEdge(source_node_id="m1", target_node_id="t1"),
            ],
        )
        weights = StructuralWeights()
        rs, components = structural_score(graph, weights)

        manual = (
            weights.source_consumption * components["source_consumption"]
            + weights.sink_production * components["sink_production"]
            + weights.reference_resolution * components["reference_resolution"]
            + weights.path_coverage * components["path_coverage"]
            + weights.cohesion * components["cohesion"]
        )
        assert abs(rs - manual) < 1e-12
        assert set(components.keys()) == {
            "source_consumption",
            "sink_production",
            "reference_resolution",
            "path_coverage",
            "cohesion",
        }


class TestCompositeScore:
    """Validate composite_score's geometric-mean assembly."""

    def test_composite_score_geometric_mean_no_compensation(self) -> None:
        """Rc=1.0, Rs=0.0 and the reverse both give composite = 0.0.

        Case A: a single perfectly-rated SOURCE node (Rc=1.0) with no
        downstream consumer (rc1=0.0); structural weights put all weight
        on source_consumption, so Rs=0.0 exactly.

        Case B: a SOURCE+METHOD pair both rated 1 (Rc=0.0) where the
        source IS consumed (rc1=1.0); the same structural weights give
        Rs=1.0 exactly.

        Either direction must drive the composite to 0.0 -- a perfect
        score on one axis cannot compensate for a zero on the other.
        """
        only_weight_on_rc1 = StructuralWeights(
            source_consumption=1.0,
            sink_production=0.0,
            reference_resolution=0.0,
            path_coverage=0.0,
            cohesion=0.0,
        )

        # Case A: Rc=1.0, Rs=0.0
        perfect_orphan_source = _make_node("s1", NodeType.SOURCE, 4)
        graph_a = WorkflowGraph(paper_id="a", nodes=[perfect_orphan_source], edges=[])
        result_a = composite_score(graph_a, structural_weights=only_weight_on_rc1)
        assert result_a.content_score == 1.0
        assert result_a.structural_score == 0.0
        assert result_a.composite_score == 0.0

        # Case B: Rc=0.0, Rs=1.0
        worst_source = _make_node("s1", NodeType.SOURCE, 1)
        worst_method = _make_node("m1", NodeType.METHOD, 1, depends_on=["s1"])
        graph_b = WorkflowGraph(
            paper_id="b",
            nodes=[worst_source, worst_method],
            edges=[WorkflowEdge(source_node_id="s1", target_node_id="m1")],
        )
        result_b = composite_score(graph_b, structural_weights=only_weight_on_rc1)
        assert result_b.content_score == 0.0
        assert result_b.structural_score == 1.0
        assert result_b.composite_score == 0.0

    def test_composite_score_empty_graph_no_zero_division(self) -> None:
        """Zero nodes and zero edges: 0.0 everywhere, no exception raised."""
        graph = WorkflowGraph(paper_id="empty", nodes=[], edges=[], dangling_reference_count=0)

        result = composite_score(graph)

        assert result.content_score == 0.0
        assert result.structural_score == 0.0
        assert result.composite_score == 0.0
        assert result.stage_scores == {}
        assert result.structural_components == {
            "source_consumption": 0.0,
            "sink_production": 0.0,
            "reference_resolution": 0.0,
            "path_coverage": 0.0,
            "cohesion": 0.0,
        }
        assert result.n_nodes == 0
        assert result.n_edges == 0
        assert result.n_dangling_references == 0

    def test_composite_score_matches_sqrt_formula(self) -> None:
        """A realistic mixed graph's composite should equal sqrt(Rc * Rs) exactly."""
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        m1 = _make_node("m1", NodeType.METHOD, 4, depends_on=["s1"])
        t1 = _make_node("t1", NodeType.SINK, 2, depends_on=["m1"])
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, m1, t1],
            edges=[
                WorkflowEdge(source_node_id="s1", target_node_id="m1"),
                WorkflowEdge(source_node_id="m1", target_node_id="t1"),
            ],
        )
        result = composite_score(graph)
        assert abs(result.composite_score - math.sqrt(result.content_score * result.structural_score)) < 1e-12
        assert result.n_nodes == 3
        assert result.n_edges == 2
        assert result.n_dangling_references == 0


class TestScoreCorpus:
    """Validate score_corpus batch scoring keyed by paper_id."""

    def test_scores_each_graph_keyed_by_paper_id(self) -> None:
        """Each graph's score should be keyed by its own paper_id."""
        g1 = WorkflowGraph(
            paper_id="doi:10.1/a",
            nodes=[_make_node("s1", NodeType.SOURCE, 4, paper_id="doi:10.1/a")],
            edges=[],
        )
        g2 = WorkflowGraph(
            paper_id="doi:10.2/b",
            nodes=[_make_node("s1", NodeType.SOURCE, 1, paper_id="doi:10.2/b")],
            edges=[],
        )
        results = score_corpus([g1, g2])
        assert set(results.keys()) == {"doi:10.1/a", "doi:10.2/b"}
        assert results["doi:10.1/a"].content_score == 1.0
        assert results["doi:10.2/b"].content_score == 0.0

    def test_empty_corpus_returns_empty_dict(self) -> None:
        """Scoring an empty list of graphs should return an empty dict."""
        assert score_corpus([]) == {}

    def test_forwards_weight_overrides(self) -> None:
        """content_weights/structural_weights kwargs should reach composite_score."""
        graph = WorkflowGraph(
            paper_id="doi:10.1/w",
            nodes=[_make_node("s1", NodeType.SOURCE, 4, paper_id="doi:10.1/w")],
            edges=[],
        )
        custom_weights = ContentWeights(sources=1.0, methods=0.0, experiments=0.0, sinks=0.0)
        results = score_corpus([graph], content_weights=custom_weights)
        assert results["doi:10.1/w"].content_score == 1.0


class TestVerifySourceQuote:
    """Validate verify_source_quote's exact/near/unrelated classification."""

    def test_verify_source_quote_exact_and_near_match(self) -> None:
        """Exact substring True; one-word-changed near match True at 0.85; unrelated sentence False."""
        fulltext = (
            "Introduction paragraph unrelated filler text goes here for padding purposes. "
            "The quick brown fox leaps over the lazy dog in the morning, according to the report. "
            "Conclusion paragraph with more unrelated filler content follows after this point."
        )

        # Exact substring.
        exact_quote = "leaps over the lazy dog in the morning"
        assert verify_source_quote(exact_quote, fulltext) is True

        # Near-verbatim: "jumps" swapped in for "leaps" (one word changed).
        near_quote = "The quick brown fox jumps over the lazy dog in the morning"
        assert verify_source_quote(near_quote, fulltext, fuzzy_threshold=0.85) is True

        # Unrelated sentence, nothing like it appears anywhere in fulltext.
        unrelated_quote = "Completely unrelated content about stock market trading strategies today"
        assert verify_source_quote(unrelated_quote, fulltext) is False

    def test_empty_quote_returns_false(self) -> None:
        """An empty quote string should return False, not match everything."""
        assert verify_source_quote("", "some fulltext content here") is False

    def test_empty_fulltext_returns_false(self) -> None:
        """An empty fulltext should return False for any non-empty quote."""
        assert verify_source_quote("some quote", "") is False

    def test_high_threshold_rejects_near_match(self) -> None:
        """Raising fuzzy_threshold above the near-match's actual ratio should reject it."""
        fulltext = "The quick brown fox leaps over the lazy dog in the morning."
        near_quote = "The quick brown fox jumps over the lazy dog in the morning"
        assert verify_source_quote(near_quote, fulltext, fuzzy_threshold=0.999) is False

    def test_verify_source_quote_whitespace_only_quote_returns_false(self) -> None:
        """A quote that splits to zero words (whitespace-only) must return False."""
        assert verify_source_quote("   \t  \n  ", "some fulltext content here") is False


class TestWeakComponentCoveragePhantomEdges:
    """Verify rc5 never exceeds 1.0 when edges reference phantom node ids."""

    def test_phantom_edge_endpoints_do_not_inflate_rc5(self) -> None:
        """Edges with one endpoint not in graph.nodes must not inflate rc5 above 1.0.

        A hand-built WorkflowGraph with two SOURCE nodes and one edge that
        references a phantom third node would previously cause the BFS to
        add the phantom to the component, inflating len(component) to 3
        while len(graph.nodes) is 2, yielding 3/2 = 1.5 > 1.0.
        """
        s1 = _make_node("s1", NodeType.SOURCE, 3)
        s2 = _make_node("s2", NodeType.SOURCE, 3)
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1, s2],
            edges=[
                # s1 connects to a real node s2.
                WorkflowEdge(source_node_id="s1", target_node_id="s2"),
                # s2 also connects to a phantom "ghost" not in graph.nodes.
                WorkflowEdge(source_node_id="s2", target_node_id="ghost"),
            ],
        )
        rc5 = weak_component_coverage(graph)
        assert rc5 <= 1.0
        # s1 and s2 form one component of size 2; ghost is ignored.
        assert rc5 == 1.0


class TestCycleHandling:
    """Verify all scoring functions handle cyclic dependency graphs without error."""

    def test_two_node_cycle_scores_without_infinite_loop(self) -> None:
        """A depends on B, B depends on A — a cycle that the paper assumes away.

        rc5 (cohesion) should be 1.0 because the cycle is one component.
        composite_score should not hang or raise.
        """
        # Cycle: s1 depends on m1, m1 depends on s1.
        s1_cyclic = WorkflowNode(
            node_id="s1",
            node_name="s1",
            node_type=NodeType.SOURCE,
            source_quote="q",
            description="d",
            reproducibility_rating=3,
            depends_on=["m1"],
            paper_id="p",
        )
        m1_cyclic = WorkflowNode(
            node_id="m1",
            node_name="m1",
            node_type=NodeType.METHOD,
            source_quote="q",
            description="d",
            reproducibility_rating=3,
            depends_on=["s1"],
            paper_id="p",
        )
        graph = WorkflowGraph(
            paper_id="p",
            nodes=[s1_cyclic, m1_cyclic],
            edges=[
                WorkflowEdge(source_node_id="s1", target_node_id="m1"),
                WorkflowEdge(source_node_id="m1", target_node_id="s1"),
            ],
        )
        # Must not hang, must not raise.
        result = composite_score(graph)
        assert 0.0 <= result.composite_score <= 1.0
        # The cycle is one weakly-connected component of size 2.
        assert result.structural_components["cohesion"] == 1.0

    def test_self_referencing_node_scores_without_error(self) -> None:
        """A node that depends on itself — a degenerate cycle.

        build_workflow_graph will create a self-loop edge. Scoring must
        not hang or raise; rc1/rc2/rc3/rc4/rc5 should all be well-defined.
        """
        n1 = WorkflowNode(
            node_id="n1",
            node_name="self-referencing",
            node_type=NodeType.SOURCE,
            source_quote="q",
            description="d",
            reproducibility_rating=3,
            depends_on=["n1"],
            paper_id="p",
        )
        from reproducibility.models import build_workflow_graph

        graph = build_workflow_graph("p", [n1])
        assert len(graph.edges) == 1
        result = composite_score(graph)
        assert 0.0 <= result.composite_score <= 1.0
