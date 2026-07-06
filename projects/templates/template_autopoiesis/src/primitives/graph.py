"""Graph primitives: BFS distances and PageRank."""

from __future__ import annotations

from collections import deque

import numpy as np

from .base import PrimitiveSpec


def bfs_distances(inputs: dict) -> dict:
    """Compute BFS distances from a source node on an undirected graph.

    inputs: adjacency (dict[str, list[str]]), source (str)
    Returns: distances (dict[str, int])
    """
    adj: dict[str, list[str]] = inputs["adjacency"]
    source: str = str(inputs["source"])

    dist: dict[str, int] = {source: 0}
    queue: deque[str] = deque([source])
    while queue:
        node = queue.popleft()
        for neighbor in adj.get(node, []):
            if neighbor not in dist:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return {"distances": dist}


def pagerank(inputs: dict) -> dict:
    """Compute PageRank on a directed graph.

    inputs: adjacency (dict[str, list[str]]), damping (float), iterations (int)
    Returns: ranks (dict[str, float])
    """
    adj: dict[str, list[str]] = inputs["adjacency"]
    damping = float(inputs.get("damping", 0.85))
    iterations = int(inputs.get("iterations", 50))

    nodes = list(adj.keys())
    # Collect all nodes (including targets)
    all_nodes: set[str] = set(nodes)
    for targets in adj.values():
        all_nodes.update(targets)
    nodes = sorted(all_nodes)
    n = len(nodes)
    if n == 0:
        return {"ranks": {}}

    idx = {node: i for i, node in enumerate(nodes)}
    ranks = np.ones(n) / n

    for _ in range(iterations):
        new_ranks = np.zeros(n)
        for node, targets in adj.items():
            if not targets:
                # dangling node: distribute evenly
                new_ranks += ranks[idx[node]] / n
            else:
                share = ranks[idx[node]] / len(targets)
                for t in targets:
                    new_ranks[idx[t]] += share
        ranks = (1 - damping) / n + damping * new_ranks

    return {"ranks": {node: float(ranks[i]) for i, node in enumerate(nodes)}}


def _disconnected_control(inputs: dict) -> dict:
    """BFS on a graph with no edges from source: only source has distance 0."""
    inp = dict(inputs)
    inp["adjacency"] = {inp["source"]: []}
    return bfs_distances(inp)


# Fixed test graph
_GRAPH = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D"],
    "D": ["B", "C", "E"],
    "E": ["D"],
}

_EXAMPLE_BFS = {"adjacency": _GRAPH, "source": "A"}
_EXAMPLE_PR = {"adjacency": _GRAPH, "damping": 0.85, "iterations": 50}

PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        name="bfs_distances",
        domain="graph",
        fn=bfs_distances,
        callable_name="bfs_distances",
        example_input=_EXAMPLE_BFS,
        expected={"distances": {"A": 0, "B": 1, "C": 1, "D": 2, "E": 3}},
        tolerance=0.0,
        negative_control=_disconnected_control,
    ),
    PrimitiveSpec(
        name="pagerank",
        domain="graph",
        fn=pagerank,
        callable_name="pagerank",
        example_input=_EXAMPLE_PR,
        expected=None,
        tolerance=1e-4,
    ),
)
