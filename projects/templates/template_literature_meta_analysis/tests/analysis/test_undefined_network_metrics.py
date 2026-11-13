"""Undefined network measurements retain null semantics and finite JSON."""

import json

import networkx as nx
import pytest

from template_literature_meta_analysis.analysis.citation_network import compute_network_metrics
from template_literature_meta_analysis.manuscript.variables import compute_variables, inject_variables


@pytest.mark.parametrize(
    ("node_count", "edges", "expected_metric", "expected_text"),
    [
        pytest.param(0, [], None, "N/A", id="empty"),
        pytest.param(3, [], None, "N/A", id="edgeless"),
        pytest.param(3, [(0, 1), (1, 2), (2, 0)], None, "N/A", id="regular-cycle"),
        pytest.param(3, [(0, 1), (1, 2)], -1.0, "-1.0000", id="finite-negative"),
        pytest.param(6, [(0, 1), (1, 2), (2, 3), (4, 5)], 0.0, "0.0000", id="finite-zero"),
    ],
)
def test_assortativity_survives_json_and_hydration(tmp_path, node_count, edges, expected_metric, expected_text):
    graph = nx.DiGraph()
    graph.add_nodes_from(range(node_count))
    graph.add_edges_from(edges)
    metrics = compute_network_metrics(graph)
    serialized = json.dumps(metrics, allow_nan=False)
    assert json.loads(serialized)["degree_assortativity"] == expected_metric

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "citation_network.json").write_text(serialized, encoding="utf-8")
    variables = compute_variables(output_dir)
    hydrated = inject_variables("Degree assortativity: {{DEGREE_ASSORTATIVITY}}.", variables)
    assert hydrated == f"Degree assortativity: {expected_text}."
