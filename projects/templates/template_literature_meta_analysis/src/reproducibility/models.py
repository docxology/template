"""Reproducibility workflow graph models.

Provides ``NodeType``, ``WorkflowNode``, ``WorkflowEdge``, and
``WorkflowGraph`` dataclasses along with a pure graph-assembly function
and JSONL serialization/merge/append helpers, following the same
patterns as :mod:`knowledge_graph.nanopublication`.

A workflow graph decomposes a paper's described pipeline into discrete
steps (source data, methods, experiments, sinks/outputs) and records how
confidently each step could be reproduced from the paper's own text.

Edge direction convention
--------------------------
``WorkflowNode.depends_on`` lists the raw (possibly-dangling) ``node_id``
values a node depends on -- i.e. upstream nodes that must exist/run
before this node makes sense. The source paper's own vocabulary for
"workflow node" does not specify a canonical edge-object direction, so
this is a deliberate modeling choice, not a claim from the source paper.

When :func:`build_workflow_graph` resolves ``depends_on`` references into
``WorkflowEdge`` objects for ``WorkflowGraph.edges``, each edge points
FROM the depended-on (upstream) node TO the depending (downstream) node::

    WorkflowEdge(source_node_id=<upstream node id>, target_node_id=<downstream node id>)

This mirrors the natural data-flow direction through the pipeline
(source -> method -> experiment -> sink) rather than the "depends on"
direction, so that simple graph-theoretic degree measures line up with
the reproducibility questions we actually care about:

- A SOURCE node that many downstream steps depend on accumulates
  *out-edges* (edges whose ``source_node_id`` is the SOURCE node) --
  so out-degree on a SOURCE node measures how much of the pipeline
  rests on it (source fan-out).
- A SINK node that depends on a long chain of upstream steps
  accumulates *in-edges* (edges whose ``target_node_id`` is the SINK
  node) -- so in-degree on a SINK node measures how much of the
  pipeline had to succeed to reach it (sink fan-in).

References that do not resolve against the known ``node_id`` set (a
paper mentioning a step that was never itself extracted as a node) are
dropped from ``edges`` and counted in ``dangling_reference_count``
instead of raising -- extraction is inherently partial, and a dangling
reference is signal (something the paper alludes to but that our
extraction did not capture as its own node), not an error.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """The four workflow-step categories a paper's pipeline is decomposed into."""

    SOURCE = "source"
    METHOD = "method"
    EXPERIMENT = "experiment"
    SINK = "sink"


@dataclass
class WorkflowNode:
    """A single step in a paper's described workflow.

    Attributes:
        node_id: Unique identifier for this node within its paper's graph.
        node_name: Short human-readable name for the step.
        node_type: One of the :class:`NodeType` categories.
        source_quote: Verbatim quote from the paper supporting this node.
        description: Free-text description of what this step does.
        reproducibility_rating: Rating in ``[1, 4]`` of how reproducible
            this step is from the paper's own text (1 = not reproducible,
            4 = fully reproducible).
        rationale: Free-text justification for ``reproducibility_rating``.
        depends_on: Raw, possibly-dangling ``node_id`` values this node
            depends on. Resolved into :class:`WorkflowEdge` objects by
            :func:`build_workflow_graph`.
        paper_id: Canonical ID of the source paper.
    """

    node_id: str
    node_name: str
    node_type: NodeType
    source_quote: str
    description: str
    reproducibility_rating: int
    rationale: str = ""
    depends_on: list[str] = field(default_factory=list)
    paper_id: str = ""


@dataclass
class WorkflowEdge:
    """A directional link between two resolved workflow nodes.

    Attributes:
        source_node_id: The upstream (depended-on) node's ``node_id``.
        target_node_id: The downstream (depending) node's ``node_id``.
        relation: Relationship label for this edge.
    """

    source_node_id: str
    target_node_id: str
    relation: str = "dependency"


@dataclass
class WorkflowGraph:
    """The assembled reproducibility workflow graph for a single paper.

    Attributes:
        paper_id: Canonical ID of the source paper.
        nodes: All workflow nodes extracted for this paper.
        edges: Only the *resolved* dependency edges (see module docstring
            for the direction convention). Dangling references are not
            represented here.
        dangling_reference_count: Count of ``depends_on`` entries across
            all nodes that did not resolve against a known ``node_id``.
    """

    paper_id: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    dangling_reference_count: int = 0

    def to_dict(self) -> dict:
        """Serialize this workflow graph to a plain dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "paper_id": self.paper_id,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_name": n.node_name,
                    "node_type": n.node_type.value,
                    "source_quote": n.source_quote,
                    "description": n.description,
                    "reproducibility_rating": n.reproducibility_rating,
                    "rationale": n.rationale,
                    "depends_on": list(n.depends_on),
                    "paper_id": n.paper_id,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "relation": e.relation,
                }
                for e in self.edges
            ],
            "dangling_reference_count": self.dangling_reference_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowGraph":
        """Deserialize a workflow graph from a plain dictionary.

        Args:
            data: Dictionary previously produced by :meth:`to_dict`.

        Returns:
            Reconstructed WorkflowGraph instance.
        """
        nodes = [
            WorkflowNode(
                node_id=n["node_id"],
                node_name=n["node_name"],
                node_type=NodeType(n["node_type"]),
                source_quote=n["source_quote"],
                description=n["description"],
                reproducibility_rating=n["reproducibility_rating"],
                rationale=n.get("rationale", ""),
                depends_on=list(n.get("depends_on", [])),
                paper_id=n.get("paper_id", ""),
            )
            for n in data.get("nodes", [])
        ]
        edges = [
            WorkflowEdge(
                source_node_id=e["source_node_id"],
                target_node_id=e["target_node_id"],
                relation=e.get("relation", "dependency"),
            )
            for e in data.get("edges", [])
        ]
        return cls(
            paper_id=data["paper_id"],
            nodes=nodes,
            edges=edges,
            dangling_reference_count=data.get("dangling_reference_count", 0),
        )


def build_workflow_graph(paper_id: str, nodes: list[WorkflowNode]) -> WorkflowGraph:
    """Assemble a WorkflowGraph by resolving each node's dependency references.

    Pure function: for every ``depends_on`` entry across *nodes*, checks it
    against the set of known ``node_id`` values in *nodes*. Resolved
    references become a :class:`WorkflowEdge` pointing from the depended-on
    node to the depending node (see module docstring for the direction
    rationale); unresolved references are dropped and counted.

    Args:
        paper_id: Canonical ID of the source paper.
        nodes: All workflow nodes extracted for this paper.

    Returns:
        A WorkflowGraph with resolved edges and a dangling-reference count.
    """
    known_ids = {n.node_id for n in nodes}
    edges: list[WorkflowEdge] = []
    dangling_count = 0

    for node in nodes:
        for dep_id in node.depends_on:
            if dep_id in known_ids:
                edges.append(
                    WorkflowEdge(
                        source_node_id=dep_id,
                        target_node_id=node.node_id,
                        relation="dependency",
                    )
                )
            else:
                dangling_count += 1

    return WorkflowGraph(
        paper_id=paper_id,
        nodes=list(nodes),
        edges=edges,
        dangling_reference_count=dangling_count,
    )


def serialize_workflow_graphs(graphs: list[WorkflowGraph]) -> list[str]:
    """Serialize workflow graphs to a list of JSON Lines strings.

    Each returned string is a single JSON object representing one
    workflow graph, suitable for writing one-per-line to a JSONL file.

    Args:
        graphs: List of workflow graphs to serialize.

    Returns:
        List of JSON-encoded strings, one per graph.
    """
    return [json.dumps(g.to_dict(), ensure_ascii=False) for g in graphs]


def deserialize_workflow_graphs(path: Path) -> list[WorkflowGraph]:
    """Read workflow graphs from a JSON Lines file.

    Args:
        path: Source file path containing one JSON object per line.

    Returns:
        List of deserialized WorkflowGraph instances.
    """
    graphs: list[WorkflowGraph] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                graphs.append(WorkflowGraph.from_dict(data))
    return graphs


def merge_workflow_graphs(
    existing: list[WorkflowGraph],
    new: list[WorkflowGraph],
) -> list[WorkflowGraph]:
    """Merge two lists of workflow graphs, deduplicating by paper_id.

    ``paper_id`` uniquely identifies a paper's workflow graph. When
    duplicates exist the *new* entry wins so that re-runs with improved
    extraction can overwrite stale results.

    Args:
        existing: Previously saved workflow graphs.
        new: Freshly built workflow graphs to merge in.

    Returns:
        Merged list with duplicates removed.
    """
    seen: dict[str, WorkflowGraph] = {}
    for g in existing:
        seen[g.paper_id] = g
    for g in new:
        seen[g.paper_id] = g  # new wins
    return list(seen.values())


def get_processed_paper_ids(graphs: list[WorkflowGraph]) -> set[str]:
    """Extract the set of unique paper IDs from workflow graphs.

    Useful for determining which papers already have a workflow graph
    so that incremental runs can skip them.

    Args:
        graphs: List of workflow graphs to inspect.

    Returns:
        Set of canonical paper IDs.
    """
    return {g.paper_id for g in graphs}


def append_workflow_graphs(graphs: list[WorkflowGraph], path: Path) -> None:
    """Atomically append workflow graphs to an existing JSONL file.

    Reads the existing file (if present), merges with the new entries
    (deduplicating by ``paper_id`` -- new wins), and writes the result
    atomically via a temporary file + rename.

    This is the single source of truth for incremental persistence:
    every checkpoint flush writes directly to the workflow-graphs file
    so that interrupts never lose already-checkpointed work.

    Args:
        graphs: Freshly built workflow graphs to persist.
        path: Destination JSONL file (created if absent).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = deserialize_workflow_graphs(path) if path.exists() else []
    merged = merge_workflow_graphs(existing, graphs)

    # Atomic write: temp file -> rename
    tmp = path.with_suffix(".jsonl.tmp")
    lines = serialize_workflow_graphs(merged)
    with open(tmp, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line + "\n")
    tmp.rename(path)

    logger.info(
        "📄 Wrote %d workflow graphs → %s",
        len(merged),
        path,
    )
