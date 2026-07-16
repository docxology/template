"""Reproducibility scoring: content-coverage and structural graph metrics.

Provides pure, zero-I/O, stdlib-only scoring functions over the
:class:`~reproducibility.models.WorkflowGraph` produced by
:func:`reproducibility.models.build_workflow_graph`, plus a standalone
quote-verification helper. Nothing here calls an LLM or touches the
filesystem or network.

Scoring model
-------------
Two independently-computed scores combine into one composite score:

``Rc`` (content score)
    A weighted average of per-stage reproducibility-rating averages
    (:func:`stage_average`), one term per :class:`~reproducibility.models.NodeType`
    stage that actually has nodes. Weights are renormalized to sum to 1
    over only the stages present, so a paper with no EXPERIMENT nodes is
    not penalized for a stage it never claimed to have.

``Rs`` (structural score)
    A fixed convex combination of five structural-coverage components
    (``rc1``..``rc5``, see :func:`structural_score`), each measuring a
    different graph-theoretic reproducibility signal: source
    consumption, sink production, reference resolution, source-to-sink
    path coverage, and weak-component cohesion.

``R`` (composite score)
    ``sqrt(Rc * Rs)`` -- the geometric mean. This is a deliberate
    *no-compensation* design: a paper cannot buy a high composite score
    by being perfect on one axis (e.g. beautifully described methods,
    ``Rc`` near 1.0) while being structurally incoherent (dangling
    references everywhere, ``Rs`` near 0.0), or vice versa. Either axis
    hitting zero drives the composite to zero.

Ambiguity resolutions (modeling choices made here, not claims from the
source paper -- the paper's own vocabulary left these underspecified)
--------------------------------------------------------------------
- **rc3 (reference_resolution) numerator/denominator scope.** Only
  ``depends_on`` references *emitted by* METHOD and EXPERIMENT nodes are
  counted. SOURCE nodes are excluded from both the numerator and the
  denominator: a SOURCE node's own ``depends_on`` entries describe what
  raw data rests on (e.g. an external repository), not a paper's
  internal pipeline structure, so counting them here would conflate two
  different reproducibility questions.
- **rc4 (source_sink_path_coverage) normalization.** The denominator is
  the *product* of source and sink counts (``|sources| * |sinks|``),
  i.e. uniform-pair-probability semantics over every (source, sink)
  pair -- NOT the size of the union of source and sink node sets. A
  paper with 2 sources and 3 sinks has 6 possible pairs; rc4 is the
  fraction of those 6 pairs joined by a directed path.
- **Edge direction.** Degree/BFS traversal here follows the edge
  direction convention documented in
  :mod:`reproducibility.models` (edges point from the depended-on/
  upstream node to the depending/downstream node), so plain out-degree
  on a SOURCE node measures fan-out and plain in-degree on a SINK node
  measures fan-in.

Follows the same style as :mod:`knowledge_graph.hypothesis`: plain
``@dataclass`` configuration objects, module-level pure functions,
manual dict/attribute access (no Pydantic), and hand-computable
formulas documented in the docstring.
"""

from __future__ import annotations

import difflib
import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

from reproducibility.models import NodeType, WorkflowGraph, WorkflowNode


@dataclass
class ContentWeights:
    """Per-stage weights for the content score ``Rc``.

    Attributes:
        sources: Weight for the SOURCE stage average.
        methods: Weight for the METHOD stage average.
        experiments: Weight for the EXPERIMENT stage average.
        sinks: Weight for the SINK stage average.
    """

    sources: float = 0.30
    methods: float = 0.20
    experiments: float = 0.20
    sinks: float = 0.30


@dataclass
class StructuralWeights:
    """Weights for the five structural-coverage components of ``Rs``.

    Attributes:
        source_consumption: Weight for ``rc1`` (source out-degree coverage).
        sink_production: Weight for ``rc2`` (sink in-degree coverage).
        reference_resolution: Weight for ``rc3`` (dependency-reference resolution).
        path_coverage: Weight for ``rc4`` (source-to-sink pair reachability).
        cohesion: Weight for ``rc5`` (largest weak-component fraction).
    """

    source_consumption: float = 0.25
    sink_production: float = 0.25
    reference_resolution: float = 0.20
    path_coverage: float = 0.15
    cohesion: float = 0.15


@dataclass
class ReproducibilityScore:
    """The full reproducibility scoring result for a single paper's workflow graph.

    Attributes:
        content_score: ``Rc`` -- weighted stage-rating average, in ``[0.0, 1.0]``.
        structural_score: ``Rs`` -- weighted structural-coverage combination, in ``[0.0, 1.0]``.
        composite_score: ``R = sqrt(Rc * Rs)``, in ``[0.0, 1.0]``.
        stage_scores: Per-stage average (only stages with >=1 node), keyed by
            ``"sources"``/``"methods"``/``"experiments"``/``"sinks"``.
        structural_components: The five ``rc1``..``rc5`` values, keyed by
            ``"source_consumption"``/``"sink_production"``/``"reference_resolution"``/
            ``"path_coverage"``/``"cohesion"``.
        n_nodes: Total node count in the scored graph.
        n_edges: Total resolved-edge count in the scored graph.
        n_dangling_references: Count of unresolved ``depends_on`` references.
    """

    content_score: float
    structural_score: float
    composite_score: float
    stage_scores: dict[str, float]
    structural_components: dict[str, float]
    n_nodes: int
    n_edges: int
    n_dangling_references: int


# Maps a content-score stage name to the NodeType it aggregates over. The
# stage name doubles as the ContentWeights attribute name, so weights can be
# looked up via getattr(weights, stage_name).
_STAGE_NODE_TYPES: dict[str, NodeType] = {
    "sources": NodeType.SOURCE,
    "methods": NodeType.METHOD,
    "experiments": NodeType.EXPERIMENT,
    "sinks": NodeType.SINK,
}


def normalized_rating(node: WorkflowNode) -> float:
    """Map a node's raw reproducibility rating into ``[0.0, 1.0]``.

    The rating is first clamped into the documented ``[1, 4]`` range
    (values outside that range are extraction noise, not a signal to
    propagate), then linearly rescaled: ``1`` (not reproducible) maps to
    ``0.0`` and ``4`` (fully reproducible) maps to ``1.0``.

    Args:
        node: The workflow node whose ``reproducibility_rating`` to normalize.

    Returns:
        Normalized rating in ``[0.0, 1.0]``.
    """
    clamped = min(4.0, max(1.0, float(node.reproducibility_rating)))
    return (clamped - 1) / 3


def stage_average(graph: WorkflowGraph, node_type: NodeType) -> Optional[float]:
    """Compute the mean normalized rating over one stage's nodes.

    Args:
        graph: The workflow graph to inspect.
        node_type: The stage (:class:`~reproducibility.models.NodeType`) to average.

    Returns:
        The mean of :func:`normalized_rating` over all nodes of *node_type*,
        or ``None`` if that stage has zero nodes in *graph*.
    """
    ratings = [normalized_rating(n) for n in graph.nodes if n.node_type == node_type]
    if not ratings:
        return None
    return sum(ratings) / len(ratings)


def content_score(graph: WorkflowGraph, weights: ContentWeights = ContentWeights()) -> tuple[float, dict[str, float]]:
    """Compute the content score ``Rc`` -- a renormalized, weighted stage average.

    Only stages that actually have >=1 node contribute; the configured
    weights for the *present* stages are renormalized to sum to 1.0
    before combining, so an absent stage (e.g. zero EXPERIMENT nodes)
    neither drags the score down nor requires a zero-node stage to be
    invented.

    Args:
        graph: The workflow graph to score.
        weights: Per-stage weights before renormalization.

    Returns:
        A ``(Rc, stage_scores)`` tuple. ``Rc`` is ``0.0`` and
        ``stage_scores`` is ``{}`` when *graph* has zero nodes total, or
        when every present stage happens to carry zero configured weight.
    """
    if not graph.nodes:
        return 0.0, {}

    stage_scores: dict[str, float] = {}
    stage_weights: dict[str, float] = {}
    for stage_name, node_type in _STAGE_NODE_TYPES.items():
        average = stage_average(graph, node_type)
        if average is None:
            continue
        stage_scores[stage_name] = average
        stage_weights[stage_name] = getattr(weights, stage_name)

    total_weight = sum(stage_weights.values())
    if total_weight == 0.0:
        return 0.0, {}

    rc = sum(stage_scores[name] * stage_weights[name] for name in stage_scores) / total_weight
    return rc, stage_scores


def source_consumption(graph: WorkflowGraph) -> float:
    """Compute ``rc1``: the fraction of SOURCE nodes with out-degree > 0.

    Out-degree here follows the edge-direction convention in
    :mod:`reproducibility.models`: an edge's ``source_node_id`` is the
    upstream node, so a SOURCE node with at least one outgoing edge has
    at least one downstream step depending on it.

    Args:
        graph: The workflow graph to inspect.

    Returns:
        Fraction in ``[0.0, 1.0]``, or ``1.0`` if *graph* has zero SOURCE nodes.
    """
    source_ids = [n.node_id for n in graph.nodes if n.node_type == NodeType.SOURCE]
    if not source_ids:
        return 1.0

    out_degree: dict[str, int] = {}
    for edge in graph.edges:
        out_degree[edge.source_node_id] = out_degree.get(edge.source_node_id, 0) + 1

    consumed = sum(1 for sid in source_ids if out_degree.get(sid, 0) > 0)
    return consumed / len(source_ids)


def sink_production(graph: WorkflowGraph) -> float:
    """Compute ``rc2``: the fraction of SINK nodes with in-degree > 0.

    Mirrors :func:`source_consumption` using in-degree (edges whose
    ``target_node_id`` is the SINK node) instead of out-degree.

    Args:
        graph: The workflow graph to inspect.

    Returns:
        Fraction in ``[0.0, 1.0]``, or ``1.0`` if *graph* has zero SINK nodes.
    """
    sink_ids = [n.node_id for n in graph.nodes if n.node_type == NodeType.SINK]
    if not sink_ids:
        return 1.0

    in_degree: dict[str, int] = {}
    for edge in graph.edges:
        in_degree[edge.target_node_id] = in_degree.get(edge.target_node_id, 0) + 1

    produced = sum(1 for sid in sink_ids if in_degree.get(sid, 0) > 0)
    return produced / len(sink_ids)


def reference_resolution(graph: WorkflowGraph) -> float:
    """Compute ``rc3``: the resolution rate of process-node dependency references.

    Only ``depends_on`` entries emitted by METHOD and EXPERIMENT nodes
    are counted (SOURCE nodes' own references describe upstream data
    provenance, not internal pipeline structure -- see module docstring).
    A reference "resolves" when its raw ``node_id`` string matches a
    known node in *graph* -- this recomputes resolution directly from
    each node's ``depends_on`` list rather than trusting
    ``graph.edges``, so it is correct even for a hand-built
    :class:`~reproducibility.models.WorkflowGraph` that was not produced
    via :func:`reproducibility.models.build_workflow_graph`.

    Args:
        graph: The workflow graph to inspect.

    Returns:
        Fraction in ``[0.0, 1.0]``, or ``1.0`` if METHOD+EXPERIMENT nodes
        emit zero references total.
    """
    known_ids = {n.node_id for n in graph.nodes}
    process_nodes = [n for n in graph.nodes if n.node_type in (NodeType.METHOD, NodeType.EXPERIMENT)]

    total_refs = sum(len(n.depends_on) for n in process_nodes)
    if total_refs == 0:
        return 1.0

    resolved = sum(1 for n in process_nodes for dep_id in n.depends_on if dep_id in known_ids)
    return resolved / total_refs


def source_sink_path_coverage(graph: WorkflowGraph) -> float:
    """Compute ``rc4``: the fraction of (source, sink) pairs joined by a directed path.

    Uniform-pair-probability semantics: the denominator is
    ``|sources| * |sinks|`` (every possible pair), NOT the size of the
    union of the two node sets -- see module docstring. Reachability is
    computed with one plain BFS per source over the directed edge
    adjacency, reused across all sinks for that source.

    Args:
        graph: The workflow graph to inspect.

    Returns:
        Fraction in ``[0.0, 1.0]``. ``0.0`` if *graph* has zero SOURCE
        nodes or zero SINK nodes.
    """
    source_ids = [n.node_id for n in graph.nodes if n.node_type == NodeType.SOURCE]
    sink_ids = {n.node_id for n in graph.nodes if n.node_type == NodeType.SINK}
    if not source_ids or not sink_ids:
        return 0.0

    adjacency: dict[str, list[str]] = {}
    for edge in graph.edges:
        adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)

    reachable_pairs = 0
    for source_id in source_ids:
        visited = {source_id}
        queue: deque[str] = deque([source_id])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        reachable_pairs += len(visited & sink_ids)

    return reachable_pairs / (len(source_ids) * len(sink_ids))


def weak_component_coverage(graph: WorkflowGraph) -> float:
    """Compute ``rc5``: the largest weakly-connected component's share of all nodes.

    Edges are treated as undirected for this computation (a plain BFS
    over an undirected adjacency built from the directed edge list).

    Args:
        graph: The workflow graph to inspect.

    Returns:
        Fraction in ``[0.0, 1.0]``, or ``0.0`` for an empty graph (zero nodes).
    """
    if not graph.nodes:
        return 0.0

    known_ids = {n.node_id for n in graph.nodes}
    undirected: dict[str, set[str]] = {n.node_id: set() for n in graph.nodes}
    for edge in graph.edges:
        # Skip edges with phantom endpoints not in graph.nodes — including
        # them would inflate component sizes beyond len(graph.nodes) and
        # could drive the result above 1.0, violating the [0.0, 1.0]
        # contract. This can happen with hand-built WorkflowGraph objects
        # whose edges were not filtered through build_workflow_graph.
        if edge.source_node_id not in known_ids or edge.target_node_id not in known_ids:
            continue
        undirected[edge.source_node_id].add(edge.target_node_id)
        undirected[edge.target_node_id].add(edge.source_node_id)

    visited_global: set[str] = set()
    largest = 0
    for node in graph.nodes:
        node_id = node.node_id
        if node_id in visited_global:
            continue
        component = {node_id}
        visited_global.add(node_id)
        queue: deque[str] = deque([node_id])
        while queue:
            current = queue.popleft()
            for neighbor in undirected.get(current, ()):
                if neighbor not in component:
                    component.add(neighbor)
                    visited_global.add(neighbor)
                    queue.append(neighbor)
        largest = max(largest, len(component))

    return largest / len(graph.nodes)


def structural_score(
    graph: WorkflowGraph, weights: StructuralWeights = StructuralWeights()
) -> tuple[float, dict[str, float]]:
    """Compute the structural score ``Rs`` -- a fixed convex combination of ``rc1``..``rc5``.

    Unlike :func:`content_score`, weights are never renormalized: all
    five components are always defined (each has its own vacuous-case
    fallback), so the configured weights are used as-is.

    Args:
        graph: The workflow graph to score.
        weights: Weights for each of the five structural components.

    Returns:
        A ``(Rs, structural_components)`` tuple, where
        ``structural_components`` holds the five raw ``rc1``..``rc5`` values.
    """
    rc1 = source_consumption(graph)
    rc2 = sink_production(graph)
    rc3 = reference_resolution(graph)
    rc4 = source_sink_path_coverage(graph)
    rc5 = weak_component_coverage(graph)

    components = {
        "source_consumption": rc1,
        "sink_production": rc2,
        "reference_resolution": rc3,
        "path_coverage": rc4,
        "cohesion": rc5,
    }
    rs = (
        weights.source_consumption * rc1
        + weights.sink_production * rc2
        + weights.reference_resolution * rc3
        + weights.path_coverage * rc4
        + weights.cohesion * rc5
    )
    return rs, components


def composite_score(
    graph: WorkflowGraph,
    content_weights: ContentWeights = ContentWeights(),
    structural_weights: StructuralWeights = StructuralWeights(),
) -> ReproducibilityScore:
    """Assemble the full reproducibility score for one workflow graph.

    ``R = sqrt(Rc * Rs)`` -- the geometric mean of the content and
    structural scores (see module docstring for the no-compensation
    rationale). An empty graph (zero nodes, zero edges) short-circuits
    to an all-zero :class:`ReproducibilityScore` with no division or
    ``sqrt`` performed, so it can never raise ``ZeroDivisionError`` or
    a ``math.sqrt`` domain error.

    Args:
        graph: The workflow graph to score.
        content_weights: Per-stage weights for :func:`content_score`.
        structural_weights: Per-component weights for :func:`structural_score`.

    Returns:
        The assembled :class:`ReproducibilityScore`.
    """
    if not graph.nodes:
        return ReproducibilityScore(
            content_score=0.0,
            structural_score=0.0,
            composite_score=0.0,
            stage_scores={},
            structural_components={
                "source_consumption": 0.0,
                "sink_production": 0.0,
                "reference_resolution": 0.0,
                "path_coverage": 0.0,
                "cohesion": 0.0,
            },
            n_nodes=0,
            n_edges=0,
            n_dangling_references=graph.dangling_reference_count,
        )

    rc, stage_scores = content_score(graph, content_weights)
    rs, structural_components = structural_score(graph, structural_weights)
    # max(0.0, ...) guards against a sqrt domain error from floating-point
    # noise driving the product fractionally below zero; Rc and Rs are
    # each always in [0.0, 1.0] by construction, so this is a safety net,
    # not a normal code path.
    composite = math.sqrt(max(0.0, rc * rs))

    return ReproducibilityScore(
        content_score=rc,
        structural_score=rs,
        composite_score=composite,
        stage_scores=stage_scores,
        structural_components=structural_components,
        n_nodes=len(graph.nodes),
        n_edges=len(graph.edges),
        n_dangling_references=graph.dangling_reference_count,
    )


def score_corpus(
    graphs: list[WorkflowGraph],
    **weights: Any,
) -> dict[str, ReproducibilityScore]:
    """Batch-score a corpus of workflow graphs.

    Args:
        graphs: Workflow graphs to score, one per paper.
        **weights: Optional ``content_weights`` and/or ``structural_weights``
            overrides forwarded to :func:`composite_score` for every graph.

    Returns:
        Dictionary mapping ``paper_id`` to its :class:`ReproducibilityScore`.
        When *graphs* contains duplicate ``paper_id`` values, the later
        entry wins (plain dict-comprehension overwrite semantics).
    """
    return {graph.paper_id: composite_score(graph, **weights) for graph in graphs}


def verify_source_quote(quote: str, fulltext: str, *, fuzzy_threshold: float = 0.85) -> bool:
    """Check whether *quote* is an actual (near-)verbatim substring of *fulltext*.

    Algorithm (stdlib ``difflib`` only, no prior art in the source paper
    for this check -- a deliberate modeling choice documented here for
    auditability):

    1. **Fast path** -- if *quote* is an exact substring of *fulltext*,
       return ``True`` immediately.
    2. **Word-aligned sliding window** -- otherwise, split both *quote*
       and *fulltext* on whitespace. Slide a window of word-count sizes
       ranging over ``quote``'s word count +/- a quarter-length
       tolerance across *fulltext*'s words (stepping one word at a
       time), re-joining each window with single spaces. Word alignment
       (rather than raw character offsets) guarantees a window lands
       exactly on the real match position regardless of surrounding
       punctuation or filler text length, which a fixed-character-step
       scan cannot guarantee.
    3. Each window is scored against *quote* with
       ``difflib.SequenceMatcher.ratio()``. A single word swap or minor
       punctuation drift still yields a high ratio because
       ``SequenceMatcher`` scores on matching *subsequence* blocks, not
       position-by-position equality.
    4. If no window's ratio reaches *fuzzy_threshold*, the quote is
       judged unrelated to *fulltext* and ``False`` is returned.

    Args:
        quote: The candidate quote to verify.
        fulltext: The full source text to search within.
        fuzzy_threshold: Minimum ``SequenceMatcher.ratio()``, in
            ``[0.0, 1.0]``, for a near-verbatim (non-exact) match to
            count. Defaults to ``0.85``.

    Returns:
        ``True`` if *quote* is an exact or near-verbatim substring of
        *fulltext*, ``False`` otherwise (including when *quote* or
        *fulltext* is empty).
    """
    if not quote or not fulltext:
        return False
    if quote in fulltext:
        return True

    quote_word_count = len(quote.split())
    fulltext_words = fulltext.split()
    if quote_word_count == 0 or not fulltext_words:
        return False

    tolerance = max(1, quote_word_count // 4)
    min_size = max(1, quote_word_count - tolerance)
    max_size = min(len(fulltext_words), quote_word_count + tolerance)

    for size in range(min_size, max_size + 1):
        for start in range(0, len(fulltext_words) - size + 1):
            window = " ".join(fulltext_words[start : start + size])
            ratio = difflib.SequenceMatcher(None, quote, window).ratio()
            if ratio >= fuzzy_threshold:
                return True

    return False
