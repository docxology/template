"""Tests for graph primitives: bfs_distances and pagerank."""
from __future__ import annotations


from src.primitives.graph import bfs_distances, pagerank, _disconnected_control, PRIMITIVES

_GRAPH = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D"],
    "D": ["B", "C", "E"],
    "E": ["D"],
}


# ---------------------------------------------------------------------------
# bfs_distances
# ---------------------------------------------------------------------------


def test_bfs_distances_source_zero():
    result = bfs_distances({"adjacency": _GRAPH, "source": "A"})
    assert result["distances"]["A"] == 0


def test_bfs_distances_direct_neighbors():
    result = bfs_distances({"adjacency": _GRAPH, "source": "A"})
    assert result["distances"]["B"] == 1
    assert result["distances"]["C"] == 1


def test_bfs_distances_known_values():
    result = bfs_distances({"adjacency": _GRAPH, "source": "A"})
    expected = {"A": 0, "B": 1, "C": 1, "D": 2, "E": 3}
    assert result["distances"] == expected


def test_bfs_distances_single_node():
    result = bfs_distances({"adjacency": {"X": []}, "source": "X"})
    assert result["distances"] == {"X": 0}


def test_bfs_distances_returns_dict():
    result = bfs_distances({"adjacency": _GRAPH, "source": "B"})
    assert isinstance(result, dict)
    assert "distances" in result


# ---------------------------------------------------------------------------
# bfs_distances — negative control
# ---------------------------------------------------------------------------


def test_disconnected_control_only_source():
    inp = {"adjacency": _GRAPH, "source": "A"}
    result = _disconnected_control(inp)
    assert result["distances"] == {"A": 0}


def test_disconnected_differs_from_connected():
    inp = {"adjacency": _GRAPH, "source": "A"}
    connected = bfs_distances(inp)
    disconnected = _disconnected_control(inp)
    assert len(connected["distances"]) > len(disconnected["distances"])


# ---------------------------------------------------------------------------
# pagerank
# ---------------------------------------------------------------------------


def test_pagerank_returns_dict():
    result = pagerank({"adjacency": _GRAPH, "damping": 0.85, "iterations": 50})
    assert isinstance(result, dict)
    assert "ranks" in result


def test_pagerank_sums_to_one():
    result = pagerank({"adjacency": _GRAPH, "damping": 0.85, "iterations": 50})
    total = sum(result["ranks"].values())
    assert abs(total - 1.0) < 1e-6


def test_pagerank_all_nodes_covered():
    result = pagerank({"adjacency": _GRAPH, "damping": 0.85, "iterations": 50})
    assert set(result["ranks"].keys()) == {"A", "B", "C", "D", "E"}


def test_pagerank_all_positive():
    result = pagerank({"adjacency": _GRAPH, "damping": 0.85, "iterations": 50})
    for v in result["ranks"].values():
        assert v > 0


def test_pagerank_empty_graph():
    result = pagerank({"adjacency": {}, "damping": 0.85, "iterations": 10})
    assert result["ranks"] == {}


# ---------------------------------------------------------------------------
# PRIMITIVES registry
# ---------------------------------------------------------------------------


def test_primitives_length():
    assert len(PRIMITIVES) == 2


def test_primitives_names():
    names = {p.name for p in PRIMITIVES}
    assert names == {"bfs_distances", "pagerank"}


def test_primitives_domain():
    for p in PRIMITIVES:
        assert p.domain == "graph"


def test_bfs_example_input():
    spec = next(p for p in PRIMITIVES if p.name == "bfs_distances")
    result = spec.fn(spec.example_input)
    assert result["distances"] == spec.expected["distances"]


def test_bfs_negative_control_exists():
    spec = next(p for p in PRIMITIVES if p.name == "bfs_distances")
    assert spec.negative_control is not None
