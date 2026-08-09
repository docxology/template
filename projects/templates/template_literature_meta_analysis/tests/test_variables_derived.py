"""Tests for src/manuscript/variables.py — compute_variables and inject_variables.

Tests cover:
- _latex_number formatting (thousand separators)
- _count_jsonl_lines counting
- _count_total_references from corpus JSONL
- compute_variables with full / partial / empty pipeline output
- inject_variables placeholder replacement
- Edge cases: missing files, empty JSON, malformed data
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Ensure infrastructure is importable
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from manuscript.variables import (
    compute_variables,
)


# ── _humanize_list ────────────────────────────────────────────────────────

# ── Fulltext assessment variables ────────────────────────────────────────


class TestFulltextAssessmentVariables:
    """compute_variables populates fulltext coverage tokens from fulltext_assessment.json."""

    def test_fulltext_variables_computed(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        fulltext = {
            "abstract_coverage": {"percent_with_abstract": 87.5, "has_abstract": 7, "no_abstract": 1},
            "open_access": {"is_oa": 4, "percent_oa": 50.0},
            "pdf_availability": {"has_pdf_url": 3, "percent_with_pdf": 37.5},
            "identifier_coverage": {"doi": 6, "arxiv_id": 2, "openalex_id": 5},
            "fulltext_format": {"publisher_pdf_only": 1, "no_fulltext_available": 2},
        }
        (tmp_path / "fulltext_assessment.json").write_text(json.dumps(fulltext))
        v = compute_variables(tmp_path)
        assert v["ABSTRACT_COVERAGE_PCT"] == "87.5"
        assert v["ABSTRACT_COUNT"] == "7"
        assert v["NO_ABSTRACT_COUNT"] == "1"
        assert v["OA_COUNT"] == "4"
        assert v["OA_PCT"] == "50.0"
        assert v["PDF_AVAIL_COUNT"] == "3"
        assert v["PDF_AVAIL_PCT"] == "37.5"
        assert v["DOI_COUNT"] == "6"
        assert v["ARXIV_ID_COUNT"] == "2"
        assert v["OPENALEX_ID_COUNT"] == "5"
        assert v["PUBLISHER_PDF_COUNT"] == "1"
        assert v["NO_FULLTEXT_COUNT"] == "2"

    def test_fulltext_variables_absent_when_missing(self, tmp_path):
        """No fulltext variables emitted when fulltext_assessment.json is missing."""
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert "ABSTRACT_COVERAGE_PCT" not in v
        assert "OA_PCT" not in v


# ── Descriptive statistics variables ─────────────────────────────────────


class TestDescriptiveStatsVariables:
    """compute_variables populates descriptive-stats tokens from descriptive_stats.json."""

    def _write_desc(self, tmp_path, desc: dict) -> None:
        (tmp_path / "corpus.jsonl").write_text("")
        (tmp_path / "descriptive_stats.json").write_text(json.dumps(desc))

    def test_basic_descriptive_stats(self, tmp_path):
        desc = {
            "descriptive_stats": {
                "unique_authors": 12,
                "citation_count_mean": 14.3,
                "citation_count_median": 8.0,
                "citation_count_max": 150,
                "citation_count_total": 858,
                "papers_per_author_mean": 1.5,
                "pct_with_doi": 92.3,
                "counts_by_venue": {"Nature": 5, "Science": 3},
            },
            "citation_distribution": {
                "histogram": {"0": 2, "1-9": 5, "10+": 3},
                "gini": 0.421,
                "n": 10,
                "total_citations": 858,
            },
            "author_productivity": [["Alice Smith", 3], ["Bob Jones", 2]],
        }
        self._write_desc(tmp_path, desc)
        v = compute_variables(tmp_path)
        assert v["UNIQUE_AUTHORS"] == "12"
        assert v["CITATION_MEAN"] == "14.3"
        assert v["CITATION_MEDIAN"] == "8.0"
        assert v["CITATION_MAX"] == "150"
        assert v["CITATION_TOTAL"] == "858"
        assert v["PAPERS_PER_AUTHOR_MEAN"] == "1.50"
        assert v["PCT_WITH_DOI"] == "92.3"
        assert "| Nature | 5 |" in v["TOP_VENUES_TABLE"]
        assert v["GINI_COEFFICIENT"] == "0.421"
        assert v["CITATION_DIST_N"] == "10"
        assert "| 0 | 2 |" in v["CITATION_DIST_TABLE"]
        assert "| Alice Smith" in v["TOP_AUTHORS_TABLE"]

    def test_empty_venues_table(self, tmp_path):
        """Empty venues dict produces empty table marker."""
        desc = {
            "descriptive_stats": {
                "unique_authors": 1,
                "citation_count_mean": 0.0,
                "citation_count_median": 0.0,
                "citation_count_max": 0,
                "citation_count_total": 0,
                "papers_per_author_mean": 1.0,
                "pct_with_doi": 0.0,
                "counts_by_venue": {},
            },
            "citation_distribution": {"histogram": {}, "gini": 0.0, "n": 0},
            "author_productivity": [],
        }
        self._write_desc(tmp_path, desc)
        v = compute_variables(tmp_path)
        assert v["TOP_VENUES_TABLE"] == "| Venue | Papers |\n| --- | --- |"
        assert v["CITATION_DIST_TABLE"] == "| Citations | Papers |\n| --- | --- |"
        assert v["TOP_AUTHORS_TABLE"] == "| Rank | Author | Papers |\n| --- | --- | --- |"

    def test_descriptive_stats_absent_when_missing(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert "UNIQUE_AUTHORS" not in v
        assert "GINI_COEFFICIENT" not in v


# ── Entity and keyphrase variables ────────────────────────────────────────


class TestEntityVariables:
    """compute_variables populates entity and keyphrase tokens."""

    def test_entities_computed(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "corpus.jsonl").write_text("")
        entities = {"modafinil": 42, "wakefulness": 31, "dopamine": 18}
        (data_dir / "entities.json").write_text(json.dumps(entities))
        v = compute_variables(tmp_path)
        assert "| modafinil | 42 |" in v["TOP_ENTITIES_TABLE"]
        assert v["NUM_ENTITIES"] == "3"

    def test_entities_fallback_when_missing(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert v["NUM_ENTITIES"] == "0"
        assert "| Entity | Frequency |" in v["TOP_ENTITIES_TABLE"]

    def test_keyphrases_computed(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "corpus.jsonl").write_text("")
        kp = {"top_keyphrases": [{"phrase": "sleep deprivation", "score": 0.842}]}
        (data_dir / "keyphrases.json").write_text(json.dumps(kp))
        v = compute_variables(tmp_path)
        assert "| sleep deprivation | 0.8420 |" in v["TOP_KEYPHRASES_TABLE"]
        assert v["NUM_KEYPHRASES"] == "1"

    def test_keyphrases_empty_list(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "corpus.jsonl").write_text("")
        kp = {"top_keyphrases": []}
        (data_dir / "keyphrases.json").write_text(json.dumps(kp))
        v = compute_variables(tmp_path)
        assert v["NUM_KEYPHRASES"] == "0"

    def test_keyphrases_fallback_when_missing(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert v["NUM_KEYPHRASES"] == "0"


# ── Embedding analysis variables ──────────────────────────────────────────


class TestEmbeddingAnalysisVariables:
    """compute_variables populates embedding cluster/similarity tokens."""

    def test_embedding_clusters_and_pairs(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "corpus.jsonl").write_text("")
        emb = {
            "num_clusters": 3,
            "top_similar_pairs": [
                {"paper_a": "doi:10.1/a", "paper_b": "doi:10.1/b", "similarity": 0.91},
            ],
        }
        (data_dir / "embedding_analysis.json").write_text(json.dumps(emb))
        v = compute_variables(tmp_path)
        assert v["NUM_EMBEDDING_CLUSTERS"] == "3"
        assert "| doi:10.1/a" in v["TOP_SIMILAR_PAIRS_TABLE"]

    def test_embedding_empty_pairs(self, tmp_path):
        """Empty pairs list yields the header-only table."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "corpus.jsonl").write_text("")
        emb = {"num_clusters": 2, "top_similar_pairs": []}
        (data_dir / "embedding_analysis.json").write_text(json.dumps(emb))
        v = compute_variables(tmp_path)
        assert v["TOP_SIMILAR_PAIRS_TABLE"] == "| Paper A | Paper B | Similarity |\n| --- | --- | --- |"

    def test_embedding_fallback_when_missing(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert v["NUM_EMBEDDING_CLUSTERS"] == "0"


# ── Advanced citation network metric variables ────────────────────────────


class TestAdvancedCitationVariables:
    """compute_variables populates betweenness/assortativity/clustering tokens."""

    def test_advanced_metrics_with_top_betweenness(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        citation = {
            "num_nodes": 5,
            "num_edges": 4,
            "density": 0.2,
            "avg_in_degree": 0.8,
            "connected_components": 2,
            "total_references": 4,
            "degree_assortativity": -0.25,
            "avg_clustering": 0.0333,
            "top_betweenness": {"doi:10.1/a": 0.6, "doi:10.1/b": 0.4},
        }
        (tmp_path / "citation_network.json").write_text(json.dumps(citation))
        v = compute_variables(tmp_path)
        assert v["DEGREE_ASSORTATIVITY"] == "-0.2500"
        assert v["AVG_CLUSTERING"] == "0.0333"
        assert "| 1 | 10.1/a |" in v["TOP_BETWEENNESS_TABLE"]

    def test_advanced_metrics_no_betweenness(self, tmp_path):
        """Empty betweenness dict yields the header-only table."""
        (tmp_path / "corpus.jsonl").write_text("")
        citation = {
            "num_nodes": 2,
            "num_edges": 1,
            "density": 0.5,
            "avg_in_degree": 0.5,
            "connected_components": 1,
            "total_references": 1,
            "top_betweenness": {},
        }
        (tmp_path / "citation_network.json").write_text(json.dumps(citation))
        v = compute_variables(tmp_path)
        assert v["TOP_BETWEENNESS_TABLE"] == "| Rank | DOI | Betweenness |\n| --- | --- | --- |"

    def test_advanced_metrics_fallback_when_citation_missing(self, tmp_path):
        """DEGREE_ASSORTATIVITY/AVG_CLUSTERING default to 0.0000 when citation_network.json is absent."""
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert v["DEGREE_ASSORTATIVITY"] == "0.0000"
        assert v["AVG_CLUSTERING"] == "0.0000"


# ── Reproducibility-assessment variables ──────────────────────────────────


class TestReproducibilityVariables:
    """compute_variables populates reproducibility-assessment tokens."""

    def test_reproducibility_variables_computed(self, tmp_path):
        (tmp_path / "corpus.jsonl").write_text("")
        summary = {
            "mean_composite_score": 0.6234,
            "n_papers_scored": 4,
            "n_low_score": 2,
            "low_score_threshold": 0.5,
            "n_skipped_no_fulltext": 1,
            "n_skipped_unparseable_pdf": 0,
            "fulltext_available": True,
        }
        (tmp_path / "reproducibility_summary.json").write_text(json.dumps(summary))
        scores = {
            "paper_a": {
                "content_score": 0.2,
                "structural_score": 0.1,
                "composite_score": 0.1414,
                "n_nodes": 3,
                "n_edges": 1,
                "n_dangling_references": 2,
                "quote_verification_rate": 0.5,
            },
            "paper_b": {
                "content_score": 0.3,
                "structural_score": 0.25,
                "composite_score": 0.2739,
                "n_nodes": 5,
                "n_edges": 3,
                "n_dangling_references": 1,
                "quote_verification_rate": 0.8,
            },
            "paper_c": {
                "content_score": 0.9,
                "structural_score": 0.95,
                "composite_score": 0.9247,
                "n_nodes": 8,
                "n_edges": 7,
                "n_dangling_references": 0,
                "quote_verification_rate": 1.0,
            },
        }
        (tmp_path / "reproducibility_scores.json").write_text(json.dumps(scores))
        v = compute_variables(tmp_path)
        assert v["REPRODUCIBILITY_MEAN_SCORE"] == "0.623"
        assert v["REPRODUCIBILITY_N_PAPERS_SCORED"] == "4"
        assert v["REPRODUCIBILITY_LOW_SCORE_COUNT"] == "2"
        # Only paper_a and paper_b fall below the 0.5 threshold; sorted ascending.
        table = v["REPRODUCIBILITY_TABLE"]
        assert "| Paper | Composite | Content | Structural |" in table
        assert "paper_c" not in table
        a_idx = table.index("paper_a")
        b_idx = table.index("paper_b")
        assert a_idx < b_idx
        assert "| paper_a | 0.141 | 0.200 | 0.100 |" in table

    def test_reproducibility_variables_pending_when_missing(self, tmp_path):
        """Reproducibility variables degrade gracefully when neither artifact exists."""
        (tmp_path / "corpus.jsonl").write_text("")
        v = compute_variables(tmp_path)
        assert v["REPRODUCIBILITY_MEAN_SCORE"] == "pending"
        assert v["REPRODUCIBILITY_N_PAPERS_SCORED"] == "0"
        assert v["REPRODUCIBILITY_LOW_SCORE_COUNT"] == "0"
        assert v["REPRODUCIBILITY_TABLE"] == "| Paper | Composite | Content | Structural |\n| --- | --- | --- | --- |"

    def test_reproducibility_table_empty_when_no_low_scoring_papers(self, tmp_path):
        """REPRODUCIBILITY_TABLE is header-only when every paper scores above threshold."""
        (tmp_path / "corpus.jsonl").write_text("")
        summary = {
            "mean_composite_score": 0.9,
            "n_papers_scored": 1,
            "n_low_score": 0,
            "low_score_threshold": 0.5,
            "n_skipped_no_fulltext": 0,
            "n_skipped_unparseable_pdf": 0,
            "fulltext_available": True,
        }
        (tmp_path / "reproducibility_summary.json").write_text(json.dumps(summary))
        scores = {"paper_a": {"content_score": 0.9, "structural_score": 0.9, "composite_score": 0.9}}
        (tmp_path / "reproducibility_scores.json").write_text(json.dumps(scores))
        v = compute_variables(tmp_path)
        assert v["REPRODUCIBILITY_TABLE"] == "| Paper | Composite | Content | Structural |\n| --- | --- | --- | --- |"

    def test_reproducibility_scores_present_without_summary(self, tmp_path):
        """Scores file present but summary missing still falls back to the default threshold."""
        (tmp_path / "corpus.jsonl").write_text("")
        scores = {"paper_a": {"content_score": 0.1, "structural_score": 0.1, "composite_score": 0.1}}
        (tmp_path / "reproducibility_scores.json").write_text(json.dumps(scores))
        v = compute_variables(tmp_path)
        assert v["REPRODUCIBILITY_MEAN_SCORE"] == "pending"
        assert "| paper_a | 0.100 | 0.100 | 0.100 |" in v["REPRODUCIBILITY_TABLE"]
