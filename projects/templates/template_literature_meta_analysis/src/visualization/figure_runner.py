"""Figure generation from analysis JSON artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

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
from visualization.descriptive_plots import (
    plot_author_productivity,
    plot_citation_distribution,
    plot_entity_bar_chart,
    plot_similarity_heatmap,
    plot_top_venues,
)
from visualization.field_overview import plot_field_summary, plot_subfield_distribution
from visualization.hypothesis_charts import (
    plot_assertion_summary,
    plot_assertion_type_breakdown,
    plot_evidence_timeline,
    plot_hypothesis_dashboard,
)
from visualization.style import VIZ_CONFIG, apply_visual_style, load_viz_labels_from_config
from visualization.temporal_plots import plot_growth_curve, plot_subfield_timeline


FIGURE_SPECS: tuple[str, ...] = (
    "subfield_classification.json",
    "temporal_analysis.json",
    "subfield_timeline.json",
    "citation_network.json",
    "hypothesis_scores.json",
    "hypothesis_trends.json",
    "topics.json",
    "tfidf_data.json",
    "assertion_summary.json",
    "descriptive_stats.json",
    "entities.json",
    "embedding_analysis.json",
)

FIGURE_CAPTIONS = {
    "field_summary.png": "High-level overview of retrieved literature and subfield counts.",
    "subfield_distribution.png": "Distribution of subfields, with categories below 2% grouped as 'Other'.",
    "growth_curve.png": "Annual and cumulative growth of publications over time.",
    "subfield_timeline.png": "Temporal evolution of publications by subfield.",
    "citation_network.png": "Citation network of the corpus, displaying up to 100 highest in-degree nodes.",
    "degree_distribution.png": "Degree distribution of nodes within the citation network.",
    "hypothesis_dashboard.png": "Dashboard showing evidence scores for proposed hypotheses.",
    "evidence_timeline.png": "Timeline of evidence score accumulation for each hypothesis.",
    "word_cloud.png": "Word cloud of top weighted terms from the discovered topics.",
    "topic_term_bars.png": "Top terms and corresponding weights per discovered topic.",
    "pca_embeddings.png": "PCA plot of TF-IDF vectors highlighting document clusters.",
    "term_heatmap.png": "Heatmap of mean TF-IDF weights for terms selected by between-subfield variance.",
    "dendrogram.png": "Hierarchical clustering dendrogram of subfield TF-IDF centroids.",
    "cooccurrence_matrix.png": "Normalized co-occurrence matrix for the most frequent terms.",
    "assertion_breakdown.png": "Breakdown of nanopublication assertion types by hypothesis.",
    "assertion_summary.png": "Summary of total extracted nanopublication assertions.",
    "citation_distribution.png": "Histogram of citation counts with Gini coefficient of concentration.",
    "top_venues.png": "Top publication venues by number of papers in the corpus.",
    "author_productivity.png": "Top authors ranked by number of corpus publications.",
    "similarity_heatmap.png": "Top document pairs ranked by cosine similarity of TF-IDF/SVD embeddings.",
    "entity_bar_chart.png": "Top named entities extracted from abstracts.",
}

# Alt text describes the visual encoding and the information available in each
# plot.  Keep it separate from the shorter print caption: renderers and
# accessibility audits consume this field when the image itself is unavailable.
FIGURE_ALT_TEXT = {
    "field_summary.png": (
        "Horizontal bars run from zero to each configured subfield's paper count; "
        "labels at the bar ends give both the count and its percentage of the "
        "current corpus, while the title reports the corpus total."
    ),
    "subfield_distribution.png": (
        "Donut chart partitions the current corpus by configured subfield. Each "
        "slice is labelled with its percentage, the centre reports total N, and "
        "subfields below two percent are pooled into an Other slice."
    ),
    "growth_curve.png": (
        "Dual-axis time series with annual publication counts as bars, a dashed "
        "moving-average line, and cumulative publications as a marked line. "
        "Annotations identify the peak year, median year, total N, span, and CAGR."
    ),
    "subfield_timeline.png": (
        "Stacked area chart of publication counts by year. Coloured bands identify "
        "configured subfields, and their combined height at each year gives the "
        "annual corpus total; an inset reports total N across all bands."
    ),
    "citation_network.png": (
        "Directed spring-layout citation graph in which arrows represent citation "
        "links, node area increases with in-degree, and node colour denotes detected "
        "community when available. The five highest-in-degree papers are labelled."
    ),
    "degree_distribution.png": (
        "Histogram of paper in-degree in the directed citation graph, with the "
        "horizontal axis giving citations received and the vertical axis giving the "
        "number of papers; logarithmic axes are used when the degree range is large."
    ),
    "hypothesis_dashboard.png": (
        "Horizontal evidence-score bars for the configured hypotheses on a scale "
        "from minus one to plus one. Orange bars extend left for contradictory "
        "evidence, green bars extend right for supportive evidence, and zero is marked."
    ),
    "evidence_timeline.png": (
        "One marked line per configured hypothesis traces cumulative evidence score "
        "by publication year on a minus-one-to-plus-one scale. A dashed zero line and "
        "a shaded near-neutral band distinguish support from contradiction."
    ),
    "word_cloud.png": (
        "Term cloud derived from topic-term weights: more heavily weighted corpus "
        "terms appear in larger type, with a fixed layout seed and a cividis colour "
        "scale; word position and colour do not encode additional quantities."
    ),
    "topic_term_bars.png": (
        "Grid of horizontal bar charts, one panel per NMF topic. Each panel lists up "
        "to ten leading terms on the vertical axis, and bar length represents that "
        "term's weight in the topic."
    ),
    "pca_embeddings.png": (
        "Scatter plot projecting document TF-IDF vectors onto the first two principal "
        "components. Points are coloured by configured subfield, axes state explained "
        "variance, and arrows label the strongest well-separated term loadings."
    ),
    "term_heatmap.png": (
        "Heatmap with configured subfields as rows and the twenty terms with greatest "
        "between-subfield variance as columns. Cell colour from pale yellow to dark red "
        "encodes the subfield's mean TF-IDF weight for each term."
    ),
    "dendrogram.png": (
        "Ward-linkage dendrogram clustering configured subfields by their mean TF-IDF "
        "vectors. Leaves name subfields, branch height gives Ward distance, and an inset "
        "reports the cophenetic correlation of the hierarchy."
    ),
    "cooccurrence_matrix.png": (
        "Symmetric square matrix for the thirty most frequent document-level terms. "
        "Rows and columns list the same terms; increasingly dark blue cells indicate "
        "larger normalized within-document co-occurrence, with a zero diagonal."
    ),
    "assertion_breakdown.png": (
        "Stacked horizontal bars compare extracted assertions for each hypothesis. "
        "Green, orange, and blue segments encode supportive, contradictory, and neutral "
        "counts, and each bar-end label gives total assertions and support percentage."
    ),
    "assertion_summary.png": (
        "Two-panel assertion summary: a pie chart on the left partitions all extracted "
        "assertions into supportive, contradictory, and neutral types, while horizontal "
        "bars on the right compare total assertion counts across hypotheses."
    ),
    "citation_distribution.png": (
        "Vertical bars show how many retained papers fall in each citation-count bucket; "
        "bar-top labels give bucket counts, and the title reports the corpus size, total "
        "citations, and Gini concentration coefficient."
    ),
    "top_venues.png": (
        "Descending horizontal bars rank up to fifteen publication venues by the number "
        "of retained corpus papers. Venue names appear on the vertical axis and bar "
        "length measures the paper count represented in the current evidence snapshot."
    ),
    "author_productivity.png": (
        "Descending horizontal bars rank up to twenty authors by their number of retained "
        "corpus publications. Author names appear on the vertical axis and bar length "
        "encodes publication count after the pipeline's record deduplication."
    ),
    "similarity_heatmap.png": (
        "Ranked horizontal bars, despite the legacy heatmap filename, compare up to "
        "fifteen document pairs. Each label identifies a pair of paper IDs and bar length "
        "gives cosine similarity on a fixed zero-to-one axis."
    ),
    "entity_bar_chart.png": (
        "Descending horizontal bars rank up to twenty named entities extracted from "
        "abstracts. Entity labels appear on the vertical axis and bar length represents "
        "the number of extracted occurrences in the current corpus."
    ),
}


def _load_json(path: Path, logger: logging.Logger) -> Any:
    if not path.exists():
        logger.warning("%s not found, skipping", path)
        return {}
    with open(path, encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded


def generate_all_figures(args: argparse.Namespace) -> list[str]:
    """Generate figures from JSON inputs; return list of output paths."""
    logger = logging.getLogger("generate_figures")
    load_viz_labels_from_config(Path(__file__).resolve().parents[2])
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

    # hypothesis_dashboard.png is referenced unconditionally by
    # manuscript/03_results_hypothesis.md, and plot_hypothesis_dashboard is
    # explicitly designed to render a "no scores available" placeholder when
    # given an empty mapping (offline/no-LLM default run, before the optional
    # knowledge-graph stage has populated hypothesis_scores.json). Always call
    # it so the figure file exists regardless of whether that data is present.
    scores_data = _load_json(input_dir / "hypothesis_scores.json", logger)
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

    # Descriptive statistics figures: citation distribution, top venues, author productivity
    descriptive_data = _load_json(input_dir / "descriptive_stats.json", logger)
    if descriptive_data:
        cit_dist = descriptive_data.get("citation_distribution", {})
        if cit_dist:
            generated_paths.append(str(plot_citation_distribution(cit_dist, output_dir / "citation_distribution.png")))
        stats = descriptive_data.get("descriptive_stats", {})
        if stats:
            generated_paths.append(str(plot_top_venues(stats, output_dir / "top_venues.png")))
        author_data = descriptive_data.get("author_productivity", [])
        if author_data:
            generated_paths.append(str(plot_author_productivity(author_data, output_dir / "author_productivity.png")))

    # Entity bar chart
    entity_data = _load_json(input_dir / "entities.json", logger)
    if entity_data:
        generated_paths.append(str(plot_entity_bar_chart(entity_data, output_dir / "entity_bar_chart.png")))

    # Embedding similarity heatmap
    embedding_data = _load_json(input_dir / "embedding_analysis.json", logger)
    if embedding_data:
        similar_pairs = embedding_data.get("top_similar_pairs", [])
        if similar_pairs:
            generated_paths.append(str(plot_similarity_heatmap(similar_pairs, output_dir / "similarity_heatmap.png")))

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
    build_file = output_dir / ".figure_registry.build.json"
    build_file.unlink(missing_ok=True)
    try:
        figure_manager = FigureManager(str(build_file))
        for path_str in generated_paths:
            path = Path(path_str)
            filename = path.name
            try:
                caption = FIGURE_CAPTIONS[filename]
                alt_text = FIGURE_ALT_TEXT[filename]
            except KeyError as exc:
                raise ValueError(f"Missing caption or alt-text specification for generated figure: {filename}") from exc
            label = f"fig:{path.stem}"
            figure_manager.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                generated_by="04_generate_figures.py",
                metadata={"alt_text": alt_text},
            )
        build_file.replace(registry_file)
    finally:
        build_file.unlink(missing_ok=True)
