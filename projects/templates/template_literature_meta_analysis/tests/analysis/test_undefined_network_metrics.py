"""Undefined network measurements retain null semantics and finite JSON."""

import json

import networkx as nx
import pytest

from template_literature_meta_analysis.analysis.citation_network import compute_network_metrics


@pytest.mark.parametrize("edges", [[], [("a", "b"), ("b", "c"), ("c", "a")]])
def test_undefined_assortativity_is_null_and_serializable(edges):
    graph = nx.DiGraph()
    graph.add_nodes_from(("a", "b", "c"))
    graph.add_edges_from(edges)
    metrics = compute_network_metrics(graph)
    assert metrics["degree_assortativity"] is None
    assert json.loads(json.dumps(metrics, allow_nan=False))["degree_assortativity"] is None
