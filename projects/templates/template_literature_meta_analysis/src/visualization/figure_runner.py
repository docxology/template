"""Figure generation from analysis JSON artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")

from visualization.advanced_plots import (
    plot_cooccurrence_matrix,
    plot_dendrogram,
    plot_pca_embeddings,
    plot_term_heatmap,
    plot_topic_term_bars,
    plot_word_cloud,
)
from visualization.citation_plots import plot_citation_network, plot_degree_distribution
from visualization.field_overview import plot_field_summary, plot_subfield_distribution
from visualization.hypothesis_charts import (
    plot_assertion_summary,
    plot_assertion_type_breakdown,
    plot_evidence_timeline,
    plot_hypothesis_dashboard,
)
from visualization.style import VIZ_CONFIG, apply_visual_style
from visualization.temporal_plots import plot_growth_curve, plot_subfield_timeline


FIGURE_CAPTIONS = {
    "field_summary.png": "High-level overview of retrieved literature and subfield counts.",
    "subfield_distribution.png": "Distribution of distinct subfields identified in the literature.",
    "growth_curve.png": "Annual and cumulative growth of publications over time.",
    "subfield_timeline.png": "Temporal evolution of publications by subfield.",
    "citation_network.png": "Citation network demonstrating connections between top papers.",
    "degree_distribution.png": "Degree distribution of nodes within the citation network.",
    "hypothesis_dashboard.png": "Dashboard showing evidence scores for proposed hypotheses.",
    "evidence_timeline.png": "Timeline of evidence score accumulation for each hypothesis.",
    "word_cloud.png": "Word cloud of salient terms appearing in abstract text.",
    "topic_term_bars.png": "Top terms and corresponding weights per discovered topic.",
    "pca_embeddings.png": "PCA plot of TF-IDF vectors highlighting document clusters.",
    "term_heatmap.png": "Heatmap of dominant TF-IDF terms across analyzed documents.",
    "dendrogram.png": "Hierarchical clustering dendrogram showing document similarity.",
    "cooccurrence_matrix.png": "Co-occurrence matrix for significant terms.",
    "assertion_breakdown.png": "Breakdown of nanopublication assertion types by hypothesis.",
    "assertion_summary.png": "Summary of total extracted nanopublication assertions.",
}


def _load_json(path: Path, logger: logging.Logger) -> dict:
    if not path.exists():
        logger.warning("%s not found, skipping", path)
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def generate_all_figures(args: argparse.Namespace) -> list[str]:
    """Generate figures from JSON inputs; return list of output paths."""
    logger = logging.getLogger("generate_figures")
    matplotlib.rcParams["savefig.dpi"] = args.dpi
    VIZ_CONFIG["dpi"] = args.dpi
    apply_visual_style()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[str] = []

    subfield_data = _load_json(input_dir / "subfield_classification.json", logger)
    if subfield_data:
        total_papers = sum(subfield_data.values())
        generated_paths.append(str(plot_field_summary(total_papers, subfield_data, output_dir / "field_summary.png")))
        generated_paths.append(str(plot_subfield_distribution(subfield_data, output_dir / "subfield_distribution.png")))

    temporal_data = _load_json(input_dir / "temporal_analysis.json", logger)
    if temporal_data and "year_counts" in temporal_data:
        year_counts = {int(k): v for k, v in temporal_data["year_counts"].items()}
        cumulative = {int(k): v for k, v in temporal_data["cumulative"].items()}
        smoothed = {int(k): v for k, v in temporal_data.get("smoothed_annual", {}).items()}
        generated_paths.append(
            str(
                plot_growth_curve(
                    year_counts,
                    cumulative,
                    output_dir / "growth_curve.png",
                    smoothed_annual=smoothed,
                )
            )
        )

    timeline_data = _load_json(input_dir / "subfield_timeline.json", logger)
    if timeline_data:
        converted = {sf: {int(k): v for k, v in yrs.items()} for sf, yrs in timeline_data.items()}
        generated_paths.append(str(plot_subfield_timeline(converted, output_dir / "subfield_timeline.png")))

    network_data = _load_json(input_dir / "citation_network.json", logger)
    if network_data and network_data.get("num_nodes", 0) > 0:
        try:
            import networkx as nx

            graph_path = input_dir / "citation_graph.gml"
            if graph_path.exists():
                graph = nx.read_gml(graph_path)
            else:
                graph = nx.DiGraph()
                for node_id in list(network_data.get("top_pagerank", {}).keys()):
                    graph.add_node(node_id)
            if graph.number_of_nodes() > 0:
                generated_paths.append(str(plot_citation_network(graph, output_dir / "citation_network.png")))
                generated_paths.append(str(plot_degree_distribution(graph, output_dir / "degree_distribution.png")))
        except Exception as exc:  # noqa: BLE001 -- safety net: one figure group must not abort the batch
            logger.error("Citation network figures skipped: %s", exc)

    scores_data = _load_json(input_dir / "hypothesis_scores.json", logger)
    if scores_data:
        generated_paths.append(str(plot_hypothesis_dashboard(scores_data, output_dir / "hypothesis_dashboard.png")))

    trends_data = _load_json(input_dir / "hypothesis_trends.json", logger)
    if trends_data:
        converted_trends = {hyp: {int(k): v for k, v in yrs.items()} for hyp, yrs in trends_data.items()}
        generated_paths.append(str(plot_evidence_timeline(converted_trends, output_dir / "evidence_timeline.png")))

    topics_data = _load_json(input_dir / "topics.json", logger)
    if isinstance(topics_data, list) and topics_data:
        word_weights: dict[str, float] = {}
        for topic in topics_data:
            for word, weight in zip(topic.get("top_words", []), topic.get("weights", [])):
                word_weights[word] = max(word_weights.get(word, 0), weight)
        if word_weights:
            generated_paths.append(str(plot_word_cloud(word_weights, output_dir / "word_cloud.png")))
        generated_paths.append(str(plot_topic_term_bars(topics_data, output_dir / "topic_term_bars.png")))

    tfidf_data = _load_json(input_dir / "tfidf_data.json", logger)
    if tfidf_data and "matrix" in tfidf_data:
        tfidf_matrix = np.array(tfidf_data["matrix"], dtype=np.float64)
        feature_names = tfidf_data.get("feature_names", [])
        doc_labels = tfidf_data.get("labels", [])
        doc_tokens = tfidf_data.get("doc_tokens", [])
        if tfidf_matrix.shape[0] >= 2 and doc_labels:
            generated_paths.extend(
                [
                    str(
                        plot_pca_embeddings(
                            tfidf_matrix,
                            doc_labels,
                            feature_names,
                            output_dir / "pca_embeddings.png",
                        )
                    ),
                    str(
                        plot_term_heatmap(
                            tfidf_matrix,
                            feature_names,
                            doc_labels,
                            output_dir / "term_heatmap.png",
                        )
                    ),
                    str(plot_dendrogram(tfidf_matrix, doc_labels, output_dir / "dendrogram.png")),
                ]
            )
        if doc_tokens:
            generated_paths.append(str(plot_cooccurrence_matrix(doc_tokens, output_dir / "cooccurrence_matrix.png")))

    assertion_data = _load_json(input_dir / "assertion_summary.json", logger)
    if assertion_data:
        per_hyp = assertion_data.get("per_hypothesis", {})
        if per_hyp:
            generated_paths.append(str(plot_assertion_type_breakdown(per_hyp, output_dir / "assertion_breakdown.png")))
        total = assertion_data.get("total_assertions", 0)
        type_counts = assertion_data.get("type_counts", {})
        hyp_totals = {h: sum(v.values()) for h, v in per_hyp.items()} if per_hyp else {}
        if total > 0:
            generated_paths.append(
                str(
                    plot_assertion_summary(
                        total,
                        type_counts,
                        hyp_totals,
                        output_dir / "assertion_summary.png",
                    )
                )
            )

    for path_str in generated_paths:
        print(path_str)

    _register_figures(generated_paths, output_dir, logger)
    logger.info("Generated %d figures", len(generated_paths))
    return generated_paths


def _register_figures(generated_paths: list[str], output_dir: Path, logger: logging.Logger) -> None:
    try:
        from infrastructure.documentation.figure_manager import FigureManager
    except ImportError:
        logger.warning("FigureManager unavailable — skipping figure registry")
        return

    registry_file = output_dir / "figure_registry.json"
    figure_manager = FigureManager(str(registry_file))
    for path_str in generated_paths:
        path = Path(path_str)
        filename = path.name
        caption = FIGURE_CAPTIONS.get(
            filename,
            f"Figure showing {filename.replace('.png', '').replace('_', ' ')}.",
        )
        label = f"fig:{path.stem}"
        if not figure_manager.get_figure(label):
            figure_manager.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                generated_by="04_generate_figures.py",
            )
