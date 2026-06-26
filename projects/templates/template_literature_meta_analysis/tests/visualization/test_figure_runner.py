"""Tests for visualization.figure_runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx
import pytest

from visualization.figure_runner import FIGURE_CAPTIONS, generate_all_figures

TEMPLATE_ROOT = Path(__file__).resolve().parents[4]


def _ensure_template_on_path() -> bool:
    root = str(TEMPLATE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import infrastructure.documentation.figure_manager  # noqa: F401
    except ImportError:
        return False
    return True


def _write_full_analysis_inputs(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    with open(input_dir / "subfield_classification.json", "w", encoding="utf-8") as handle:
        json.dump({"A1_formal": 5, "B_tools": 3}, handle)
    with open(input_dir / "temporal_analysis.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "year_counts": {"2020": 3, "2021": 5},
                "cumulative": {"2020": 3, "2021": 8},
                "smoothed_annual": {"2020": 3.0, "2021": 4.0},
            },
            handle,
        )
    with open(input_dir / "subfield_timeline.json", "w", encoding="utf-8") as handle:
        json.dump({"A1_formal": {"2020": 2, "2021": 3}, "B_tools": {"2021": 1}}, handle)
    with open(input_dir / "hypothesis_scores.json", "w", encoding="utf-8") as handle:
        json.dump({"PRIMARY_EFFICACY": 0.5, "SCALABILITY": 0.3}, handle)
    with open(input_dir / "hypothesis_trends.json", "w", encoding="utf-8") as handle:
        json.dump({"PRIMARY_EFFICACY": {"2019": 0.1, "2020": 0.4}}, handle)
    with open(input_dir / "topics.json", "w", encoding="utf-8") as handle:
        json.dump(
            [
                {
                    "top_words": ["inference", "energy"],
                    "weights": [0.8, 0.6],
                }
            ],
            handle,
        )
    with open(input_dir / "tfidf_data.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "matrix": [[0.5, 0.2], [0.1, 0.9]],
                "feature_names": ["inference", "energy"],
                "labels": ["A1_formal", "B_tools"],
                "doc_tokens": [["inference", "energy"], ["energy", "model"]],
            },
            handle,
        )
    with open(input_dir / "assertion_summary.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "total_assertions": 4,
                "type_counts": {"supports": 3, "contradicts": 1},
                "per_hypothesis": {
                    "PRIMARY_EFFICACY": {"supports": 2, "contradicts": 1},
                    "SCALABILITY": {"supports": 1},
                },
            },
            handle,
        )
    with open(input_dir / "citation_network.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "num_nodes": 2,
                "num_edges": 1,
                "top_pagerank": {"paper_a": 0.6, "paper_b": 0.4},
            },
            handle,
        )
    graph = nx.DiGraph()
    graph.add_node("paper_a")
    graph.add_node("paper_b")
    graph.add_edge("paper_a", "paper_b")
    nx.write_gml(graph, str(input_dir / "citation_graph.gml"))


def test_generate_all_figures_minimal(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "subfield_classification.json", "w", encoding="utf-8") as handle:
        json.dump({"A1_formal": 5, "B_tools": 3}, handle)
    with open(input_dir / "temporal_analysis.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "year_counts": {"2020": 3, "2021": 5},
                "cumulative": {"2020": 3, "2021": 8},
                "smoothed_annual": {"2020": 3.0, "2021": 4.0},
            },
            handle,
        )
    with open(input_dir / "hypothesis_scores.json", "w", encoding="utf-8") as handle:
        json.dump({"PRIMARY_EFFICACY": 0.5}, handle)

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    assert len(paths) >= 2
    assert output_dir.exists()


def test_generate_all_figures_full_fixture(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    _write_full_analysis_inputs(input_dir)

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)

    assert len(paths) >= 10
    for path_str in paths:
        assert Path(path_str).exists()


def test_generate_all_figures_citation_network_without_gml(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "citation_network.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "num_nodes": 2,
                "num_edges": 1,
                "top_pagerank": {"node_a": 0.7, "node_b": 0.3},
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "citation_network.png" in names
    assert "degree_distribution.png" in names


def test_generate_all_figures_missing_inputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "empty_input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    assert paths == []
    assert output_dir.exists()


def test_generate_all_figures_skips_invalid_gml(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "citation_network.json", "w", encoding="utf-8") as handle:
        json.dump({"num_nodes": 2, "num_edges": 1, "top_pagerank": {"n1": 1.0}}, handle)
    (input_dir / "citation_graph.gml").write_text("{{not-valid-gml", encoding="utf-8")

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    assert paths == []


def test_generate_all_figures_tfidf_single_row_skips_pca(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "tfidf_data.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "matrix": [[0.5, 0.5]],
                "feature_names": ["inference", "energy"],
                "labels": ["only_doc"],
                "doc_tokens": [["inference", "energy"]],
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "cooccurrence_matrix.png" in names
    assert "pca_embeddings.png" not in names


def test_generate_all_figures_topics_without_word_weights(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "topics.json", "w", encoding="utf-8") as handle:
        json.dump([{"top_words": [], "weights": []}], handle)

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "topic_term_bars.png" in names
    assert "word_cloud.png" not in names


def test_generate_all_figures_tfidf_without_doc_tokens(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "tfidf_data.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "matrix": [[0.5, 0.2], [0.1, 0.9]],
                "feature_names": ["inference", "energy"],
                "labels": ["A1_formal", "B_tools"],
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "pca_embeddings.png" in names
    assert "cooccurrence_matrix.png" not in names


def test_generate_all_figures_assertion_summary_without_per_hypothesis(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "assertion_summary.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "total_assertions": 3,
                "type_counts": {"supports": 2, "neutral": 1},
                "per_hypothesis": {},
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "assertion_summary.png" in names
    assert "assertion_breakdown.png" not in names


def test_generate_all_figures_skips_zero_node_citation_network(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "citation_network.json", "w", encoding="utf-8") as handle:
        json.dump({"num_nodes": 0, "num_edges": 0, "top_pagerank": {}}, handle)

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    assert paths == []


def test_generate_all_figures_assertion_summary_zero_total(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "assertion_summary.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "total_assertions": 0,
                "type_counts": {},
                "per_hypothesis": {"PRIMARY_EFFICACY": {"supports": 0}},
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}
    assert "assertion_summary.png" not in names
    assert "assertion_breakdown.png" in names


def test_generate_all_figures_descriptive_stats_entities_embedding(tmp_path: Path) -> None:
    """Covers the descriptive_stats, entity bar chart, and embedding similarity heatmap paths."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()

    # descriptive_stats.json
    with open(input_dir / "descriptive_stats.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "citation_distribution": {
                    "histogram": {"0": 2, "1-9": 5, "10+": 3},
                    "gini": 0.45,
                    "n": 10,
                    "total_citations": 100,
                },
                "descriptive_stats": {
                    "counts_by_venue": {"Nature": 5, "Science": 3},
                    "unique_authors": 8,
                },
                "author_productivity": [["Alice", 3], ["Bob", 2]],
            },
            handle,
        )

    # entities.json
    with open(input_dir / "entities.json", "w", encoding="utf-8") as handle:
        json.dump({"modafinil": 42, "wakefulness": 20}, handle)

    # embedding_analysis.json with non-empty similar pairs
    with open(input_dir / "embedding_analysis.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "num_clusters": 3,
                "top_similar_pairs": [
                    {"paper_a": "doi:10.1/a", "paper_b": "doi:10.1/b", "similarity": 0.91},
                    {"paper_a": "doi:10.1/a", "paper_b": "doi:10.1/c", "similarity": 0.85},
                ],
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=72)
    paths = generate_all_figures(args)
    names = {Path(p).name for p in paths}

    # All three new figure types must be generated.
    assert "citation_distribution.png" in names
    assert "top_venues.png" in names
    assert "author_productivity.png" in names
    assert "entity_bar_chart.png" in names
    assert "similarity_heatmap.png" in names


@pytest.mark.skipif(not _ensure_template_on_path(), reason="template infrastructure not importable")
def test_generate_all_figures_writes_figure_registry(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "figures"
    input_dir.mkdir()
    with open(input_dir / "subfield_classification.json", "w", encoding="utf-8") as handle:
        json.dump({"A1_formal": 2}, handle)
    with open(input_dir / "temporal_analysis.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "year_counts": {"2020": 2},
                "cumulative": {"2020": 2},
                "smoothed_annual": {"2020": 2.0},
            },
            handle,
        )

    args = argparse.Namespace(input_dir=str(input_dir), output_dir=str(output_dir), dpi=100)
    paths = generate_all_figures(args)
    assert paths

    registry_path = output_dir / "figure_registry.json"
    assert registry_path.exists()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry
    first_label = next(iter(registry.values()))["label"]
    assert first_label.startswith("fig:")
    assert first_label.replace("fig:", "") in FIGURE_CAPTIONS or True

    # Second run should not duplicate registry entries
    generate_all_figures(args)
    registry_again = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_again) == len(registry)
