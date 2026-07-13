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
    _latex_number,
    _count_jsonl_lines,
    _count_total_references,
    _humanize_list,
    _load_json,
    compute_variables,
    inject_variables,
)


# ── _humanize_list ────────────────────────────────────────────────────────


class TestHumanizeList:
    """Test English list serialization helper."""

    def test_empty_list(self):
        assert _humanize_list([]) == ""

    def test_single_item(self):
        assert _humanize_list(["arXiv"]) == "arXiv"

    def test_two_items(self):
        assert _humanize_list(["arXiv", "PubMed"]) == "arXiv and PubMed"

    def test_three_items(self):
        assert _humanize_list(["arXiv", "PubMed", "OpenAlex"]) == "arXiv, PubMed, and OpenAlex"


# ── _latex_number ────────────────────────────────────────────────────────


class TestLatexNumber:
    """Test LaTeX thousand separator formatting."""

    def test_small_number(self):
        assert _latex_number(42) == "42"

    def test_three_digits(self):
        assert _latex_number(775) == "775"

    def test_four_digits(self):
        assert _latex_number(1834) == "1,834"

    def test_five_digits(self):
        assert _latex_number(28073) == "28,073"

    def test_six_digits(self):
        assert _latex_number(123456) == "123,456"

    def test_seven_digits(self):
        assert _latex_number(1234567) == "1,234,567"

    def test_zero(self):
        assert _latex_number(0) == "0"

    def test_one(self):
        assert _latex_number(1) == "1"

    def test_exactly_1000(self):
        assert _latex_number(1000) == "1,000"


# ── _count_jsonl_lines ──────────────────────────────────────────────────


class TestCountJsonlLines:
    """Test JSONL line counter."""

    def test_nonexistent_file(self, tmp_path):
        assert _count_jsonl_lines(tmp_path / "missing.jsonl") == 0

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        assert _count_jsonl_lines(p) == 0

    def test_three_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"a":1}\n{"b":2}\n{"c":3}\n')
        assert _count_jsonl_lines(p) == 3

    def test_blank_lines_skipped(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"a":1}\n\n{"b":2}\n\n')
        assert _count_jsonl_lines(p) == 2


# ── _count_total_references ─────────────────────────────────────────────


class TestCountTotalReferences:
    """Test total references counter across corpus JSONL."""

    def test_nonexistent_file(self, tmp_path):
        assert _count_total_references(tmp_path / "nope.jsonl") == 0

    def test_papers_with_references(self, tmp_path):
        p = tmp_path / "corpus.jsonl"
        lines = [
            json.dumps({"title": "A", "references": ["r1", "r2", "r3"]}),
            json.dumps({"title": "B", "references": ["r4"]}),
            json.dumps({"title": "C", "references": []}),
        ]
        p.write_text("\n".join(lines) + "\n")
        assert _count_total_references(p) == 4

    def test_papers_with_referenced_works(self, tmp_path):
        p = tmp_path / "corpus.jsonl"
        lines = [
            json.dumps({"title": "A", "referenced_works": ["w1", "w2"]}),
        ]
        p.write_text("\n".join(lines) + "\n")
        assert _count_total_references(p) == 2

    def test_malformed_line_skipped(self, tmp_path):
        p = tmp_path / "corpus.jsonl"
        p.write_text('{"title":"A","references":["r1"]}\nnot-json\n')
        assert _count_total_references(p) == 1

    def test_blank_line_in_corpus_skipped(self, tmp_path):
        """Blank lines inside a corpus JSONL are skipped without error."""
        p = tmp_path / "corpus.jsonl"
        p.write_text('{"title":"A","references":["r1","r2"]}\n\n{"title":"B","references":["r3"]}\n\n')
        assert _count_total_references(p) == 3


# ── _load_json ──────────────────────────────────────────────────────────


class TestLoadJson:
    """Test JSON file loader."""

    def test_missing_file(self, tmp_path):
        missing = tmp_path / "missing.json"
        result = _load_json(missing)
        assert isinstance(result, dict)
        assert "_error" in result
        assert "file_not_found" in result["_error"]

    def test_valid_json(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"key": "value"}')
        result = _load_json(p)
        assert result == {"key": "value"}


# ── compute_variables (full pipeline output) ────────────────────────────


def _write_pipeline_output(output_dir: Path) -> None:
    """Write complete pipeline output for testing compute_variables."""
    # corpus.jsonl (3 papers)
    corpus = [
        json.dumps(
            {
                "title": "Paper A",
                "references": ["r1", "r2"],
            }
        ),
        json.dumps(
            {
                "title": "Paper B",
                "references": ["r3"],
            }
        ),
        json.dumps(
            {
                "title": "Paper C",
                "references": [],
            }
        ),
    ]
    (output_dir / "corpus.jsonl").write_text("\n".join(corpus) + "\n")

    # temporal_analysis.json
    temporal = {
        "year_counts": {"2020": 1, "2021": 1, "2022": 1},
        "cumulative": {"2020": 1, "2021": 2, "2022": 3},
        "first_year": 2020,
        "last_year": 2022,
        "peak_year": 2022,
        "total_papers": 3,
        "mean_growth_rate": 0.5,
        "doubling_time": 1.4,
        "cagr": 0.26,
    }
    (output_dir / "temporal_analysis.json").write_text(json.dumps(temporal))

    # citation_network.json
    citation = {
        "num_nodes": 3,
        "num_edges": 2,
        "density": 0.333,
        "avg_in_degree": 0.67,
        "connected_components": 1,
        "num_communities": 1,
        "total_references": 3,
        "top_pagerank": {"paper_a": 0.4, "paper_b": 0.35},
    }
    (output_dir / "citation_network.json").write_text(json.dumps(citation))

    # subfield_classification.json
    subfield = {
        "A1_formal": 10,
        "A2_philosophy": 8,
        "B_tools": 15,
        "C1_neuroscience": 12,
        "C2_robotics": 9,
        "C3_language": 5,
        "C4_psychiatry": 3,
        "C5_biology": 7,
    }
    (output_dir / "subfield_classification.json").write_text(json.dumps(subfield))

    # assertion_summary.json
    assertion = {
        "total_assertions": 45,
        "type_counts": {"supports": 20, "contradicts": 10, "neutral": 15},
        "per_hypothesis": {
            "PRIMARY_EFFICACY": {"supports": 5, "contradicts": 2, "neutral": 3},
        },
    }
    (output_dir / "assertion_summary.json").write_text(json.dumps(assertion))

    # hypothesis_scores.json
    scores = {
        "PRIMARY_EFFICACY": 0.82,
        "OPTIMAL_PERFORMANCE": 0.5,
        "MECHANISTIC_BASIS": -0.1,
    }
    (output_dir / "hypothesis_scores.json").write_text(json.dumps(scores))

    # topics.json
    topics = [
        {"topic_id": 0, "top_words": ["agent", "model"], "weights": [0.06, 0.05]},
        {"topic_id": 1, "top_words": ["free", "energy"], "weights": [0.07, 0.04]},
    ]
    (output_dir / "topics.json").write_text(json.dumps(topics))

    # figures directory with sample PNGs
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    for name in ["field_summary.png", "growth_curve.png", "hypothesis_dashboard.png"]:
        (fig_dir / name).write_bytes(b"\x89PNG")


class TestComputeVariables:
    """Test compute_variables with various pipeline output states."""

    def test_full_output(self, tmp_path):
        _write_pipeline_output(tmp_path)
        variables = compute_variables(tmp_path)

        # Corpus size
        assert variables["CORPUS_SIZE"] == "3"
        assert variables["CORPUS_SIZE_LATEX"] == "3"

        # Temporal
        assert variables["YEAR_START"] == "2020"
        assert variables["YEAR_END"] == "2022"
        assert variables["PEAK_YEAR"] == "2022"
        assert variables["PEAK_YEAR_COUNT"] == "1"
        assert "CAGR_PCT" in variables
        assert "MEAN_YOY_GROWTH_PCT" in variables
        assert "DOUBLING_TIME" in variables

        # Citation
        assert variables["CITATION_EDGES"] == "2"
        assert variables["CITATION_NODES"] == "3"
        assert variables["CITATION_COMPONENTS"] == "1"
        assert "CITATION_DENSITY_PCT" in variables
        assert variables["MEAN_IN_DEGREE"] == "0.7"
        assert variables["CITATION_TOTAL_REFS"] == "3"
        assert "CITATION_RESOLUTION_PCT" in variables

        # Subfield: a config-driven Markdown table. With no config.yaml present
        # the table falls back to the classifier's own keys; the per-code tokens
        # (A1_COUNT, ...) are intentionally gone — the table/list replace them.
        assert "SUBFIELD_TABLE" in variables
        assert "| Subfield | Papers | Share |" in variables["SUBFIELD_TABLE"]
        assert "A1 Formal" in variables["SUBFIELD_TABLE"]  # humanized fallback key
        assert "SUBFIELD_LIST" in variables
        assert "N_SUBFIELDS" in variables
        assert "A1_COUNT" not in variables  # old per-code tokens removed

        # Assertions
        assert variables["TOTAL_ASSERTIONS"] == "45"

        # Hypothesis scores
        assert variables["PRIMARY_EFFICACY_SCORE"] == "+0.82"
        assert variables["MECHANISTIC_BASIS_SCORE"] == "-0.10"

        # Topics
        assert variables["NUM_TOPICS"] == "2"

        # Figures
        assert variables["NUM_FIGURES"] == "3"

    def test_empty_output_dir(self, tmp_path):
        """compute_variables handles a completely empty output directory."""
        variables = compute_variables(tmp_path)
        assert variables["CORPUS_SIZE"] == "0"
        assert variables["CORPUS_SIZE_LATEX"] == "0"
        # Should have at least corpus-size variables
        assert len(variables) >= 2

    def test_partial_output(self, tmp_path):
        """compute_variables handles partial pipeline output."""
        (tmp_path / "corpus.jsonl").write_text('{"title":"A"}\n')
        variables = compute_variables(tmp_path)
        assert variables["CORPUS_SIZE"] == "1"
        # No temporal data, so temporal variables should be absent
        assert "YEAR_START" not in variables

    def test_citation_without_total_refs(self, tmp_path):
        """Citation variables compute from corpus when total_references=0."""
        (tmp_path / "corpus.jsonl").write_text(json.dumps({"title": "A", "references": ["r1", "r2"]}) + "\n")
        citation = {
            "num_nodes": 1,
            "num_edges": 2,
            "density": 0.5,
            "avg_in_degree": 2.0,
            "connected_components": 1,
            "total_references": 0,  # Force fallback to corpus counting
        }
        (tmp_path / "citation_network.json").write_text(json.dumps(citation))
        variables = compute_variables(tmp_path)
        assert variables["CITATION_TOTAL_REFS"] == "2"

    def test_citation_no_refs_anywhere(self, tmp_path):
        """Citation variables when no references in corpus or JSON."""
        (tmp_path / "corpus.jsonl").write_text(json.dumps({"title": "A"}) + "\n")
        citation = {
            "num_nodes": 1,
            "num_edges": 0,
            "density": 0.0,
            "avg_in_degree": 0.0,
            "connected_components": 1,
            "total_references": 0,
        }
        (tmp_path / "citation_network.json").write_text(json.dumps(citation))
        variables = compute_variables(tmp_path)
        assert variables["CITATION_TOTAL_REFS"] == "0"
        assert variables["CITATION_RESOLUTION_PCT"] == "0.0"

    def test_citation_top_authorities_and_hubs_populated(self, tmp_path):
        """TOP_AUTHORITIES_TABLE and TOP_HUBS_TABLE are populated when data is present."""
        (tmp_path / "corpus.jsonl").write_text("")
        citation = {
            "num_nodes": 3,
            "num_edges": 2,
            "density": 0.33,
            "avg_in_degree": 0.67,
            "connected_components": 1,
            "total_references": 2,
            "top_authorities": {"doi:10.1/a": 0.8, "doi:10.1/b": 0.5},
            "top_hubs": {"doi:10.1/c": 0.7, "doi:10.1/d": 0.4},
        }
        (tmp_path / "citation_network.json").write_text(json.dumps(citation))
        variables = compute_variables(tmp_path)
        assert "| 1 | 10.1/a | 0.800000 |" in variables["TOP_AUTHORITIES_TABLE"]
        assert "| 1 | 10.1/c | 0.700000 |" in variables["TOP_HUBS_TABLE"]

    def test_no_figures_dir(self, tmp_path):
        """NUM_FIGURES defaults when figures/ doesn't exist."""
        (tmp_path / "corpus.jsonl").write_text("")
        variables = compute_variables(tmp_path)
        assert variables["NUM_FIGURES"] == "pending"

    def test_hypothesis_scores_dict_format(self, tmp_path):
        """Handle hypothesis scores in nested dict format."""
        (tmp_path / "corpus.jsonl").write_text("")
        scores = {"PRIMARY_EFFICACY": {"score": 0.75, "ci_low": 0.6}}
        (tmp_path / "hypothesis_scores.json").write_text(json.dumps(scores))
        variables = compute_variables(tmp_path)
        assert variables["PRIMARY_EFFICACY_SCORE"] == "+0.75"

    def test_cagr_large_value(self, tmp_path):
        """CAGR_PCT always formatted as a percentage (multiplied by 100).
        cagr=1.5 means 150% annual growth, displayed as '150.00'."""
        (tmp_path / "corpus.jsonl").write_text("")
        temporal = {
            "year_counts": {"2020": 10},
            "cumulative": {"2020": 10},
            "first_year": 2020,
            "last_year": 2020,
            "peak_year": 2020,
            "total_papers": 10,
            "mean_growth_rate": 1.5,
            "doubling_time": 0.5,
            "cagr": 1.5,
        }
        (tmp_path / "temporal_analysis.json").write_text(json.dumps(temporal))
        variables = compute_variables(tmp_path)
        assert variables["CAGR_PCT"] == "150.00"
        assert variables["MEAN_YOY_GROWTH_PCT"] == "150.0"

    def test_doubling_time_zero(self, tmp_path):
        """DOUBLING_TIME empty string when zero."""
        (tmp_path / "corpus.jsonl").write_text("")
        temporal = {
            "year_counts": {"2020": 10},
            "cumulative": {"2020": 10},
            "first_year": 2020,
            "last_year": 2020,
            "peak_year": 2020,
            "total_papers": 10,
            "mean_growth_rate": 0.1,
            "doubling_time": 0,
            "cagr": 0.1,
        }
        (tmp_path / "temporal_analysis.json").write_text(json.dumps(temporal))
        variables = compute_variables(tmp_path)
        assert variables["DOUBLING_TIME"] == ""

    def test_subfield_with_zero_total(self, tmp_path):
        """Subfield table handles all-zero counts without dividing by zero."""
        (tmp_path / "corpus.jsonl").write_text("")
        subfield = {"A1_formal": 0, "B_tools": 0, "C1_neuroscience": 0}
        (tmp_path / "subfield_classification.json").write_text(json.dumps(subfield))
        variables = compute_variables(tmp_path)
        # All-zero total -> every share renders 0.0% (no ZeroDivisionError).
        assert "0.0%" in variables["SUBFIELD_TABLE"]
        assert "A1 Formal" in variables["SUBFIELD_TABLE"]

    def test_assertion_pct_computed(self, tmp_path):
        """ASSERTION_SUPPORT_PCT and ASSERTION_CONTRADICT_PCT computed from type_counts."""
        (tmp_path / "corpus.jsonl").write_text("")
        assertion = {
            "total_assertions": 40,
            "type_counts": {"supports": 20, "contradicts": 5, "neutral": 15},
        }
        (tmp_path / "assertion_summary.json").write_text(json.dumps(assertion))
        variables = compute_variables(tmp_path)
        # (20/(20+5))*100 = 80.0%; (5/(20+5))*100 = 20.0%
        assert variables["ASSERTION_SUPPORT_PCT"] == "80.0"
        assert variables["ASSERTION_CONTRADICT_PCT"] == "20.0"

    def test_assertion_pct_zero_when_no_support_or_contradict(self, tmp_path):
        """Assertion percentages are 0.0 when supports=0 and contradicts=0."""
        (tmp_path / "corpus.jsonl").write_text("")
        assertion = {
            "total_assertions": 15,
            "type_counts": {"supports": 0, "contradicts": 0, "neutral": 15},
        }
        (tmp_path / "assertion_summary.json").write_text(json.dumps(assertion))
        variables = compute_variables(tmp_path)
        assert variables["ASSERTION_SUPPORT_PCT"] == "0.0"
        assert variables["ASSERTION_CONTRADICT_PCT"] == "0.0"

    def test_assertion_pct_not_produced_when_missing(self, tmp_path):
        """ASSERTION_*_PCT keys absent when assertion_summary.json is missing."""
        (tmp_path / "corpus.jsonl").write_text("")
        variables = compute_variables(tmp_path)
        assert "ASSERTION_SUPPORT_PCT" not in variables
        assert "ASSERTION_CONTRADICT_PCT" not in variables


# ── inject_variables ────────────────────────────────────────────────────


class TestInjectVariables:
    """Test template variable injection."""

    def test_basic_replacement(self):
        content = "The corpus contains {{CORPUS_SIZE}} papers."
        variables = {"CORPUS_SIZE": "775"}
        result = inject_variables(content, variables, filename="test.md")
        assert result == "The corpus contains 775 papers."

    def test_multiple_replacements(self):
        content = "From {{YEAR_START}} to {{YEAR_END}}."
        variables = {"YEAR_START": "2010", "YEAR_END": "2024"}
        result = inject_variables(content, variables)
        assert result == "From 2010 to 2024."

    def test_unresolved_variable_kept(self):
        content = "Size: {{CORPUS_SIZE}}, Unknown: {{UNKNOWN_VAR}}"
        variables = {"CORPUS_SIZE": "42"}
        result = inject_variables(content, variables, lenient=True)
        assert "42" in result
        assert "{{UNKNOWN_VAR}}" in result

    def test_no_variables(self):
        content = "No placeholders here."
        result = inject_variables(content, {})
        assert result == content

    def test_empty_content(self):
        result = inject_variables("", {"CORPUS_SIZE": "42"})
        assert result == ""

    def test_repeated_variable(self):
        content = "{{SIZE}} and another {{SIZE}}"
        variables = {"SIZE": "100"}
        result = inject_variables(content, variables)
        assert result == "100 and another 100"

    def test_latex_formatted_value(self):
        content = "$N = {{CORPUS_SIZE_LATEX}}$ papers"
        variables = {"CORPUS_SIZE_LATEX": "1,834"}
        result = inject_variables(content, variables, filename="abstract.md")
        assert result == "$N = 1,834$ papers"

    def test_unresolved_variable_raises_by_default(self):
        """inject_variables raises RuntimeError for unresolved vars in strict mode."""
        content = "Size: {{CORPUS_SIZE}}, Unknown: {{UNKNOWN_VAR}}"
        variables = {"CORPUS_SIZE": "42"}
        import pytest

        with pytest.raises(RuntimeError, match="UNKNOWN_VAR"):
            inject_variables(content, variables, lenient=False)


# ── Config-driven domain tokens ──────────────────────────────────────────


class TestConfigDrivenTokens:
    """Domain tokens (term, keywords, engines, subfields, hypotheses) come from config."""

    @staticmethod
    def _project(tmp_path, config_yaml: str):
        """Build a project tree (manuscript/config.yaml + output/data/) and return output dir."""
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(config_yaml, encoding="utf-8")
        out = tmp_path / "output"
        (out / "data").mkdir(parents=True)
        return out

    _CONFIG = """
keywords:
  - alpha
  - beta
project_config:
  search:
    term: "widgets"
    relevance_keywords: [w1, w2]
    engines:
      arxiv: true
      openalex: false
      crossref: true
  subfield_keywords:
    first_bucket: [a, b]
    second_bucket: [c]
  hypothesis_definitions:
    H1:
      name: "Primary Claim"
      scope: "clinical"
    H2:
      name: "Secondary Claim"
      scope: "applied"
"""

    def test_term_keywords_engines_from_config(self, tmp_path):
        out = self._project(tmp_path, self._CONFIG)
        (out / "data" / "corpus.jsonl").write_text("")
        v = compute_variables(out)
        assert v["SEARCH_TERM"] == "widgets"
        assert v["SEARCH_TERM_TITLE"] == "Widgets"
        assert v["KEYWORDS_LIST"] == "alpha, beta"
        assert v["KEYWORDS_RELEVANCE"] == "w1, w2"
        # only arxiv + crossref are enabled (openalex: false)
        assert v["N_ENGINES"] == "2"
        assert v["ENGINE_LIST"] == "arXiv and Crossref"

    def test_subfield_table_from_config_and_counts(self, tmp_path):
        out = self._project(tmp_path, self._CONFIG)
        (out / "data" / "corpus.jsonl").write_text("")
        # classifier counts keyed by the CONFIG subfield names
        (out / "data" / "subfield_classification.json").write_text(json.dumps({"first_bucket": 3, "second_bucket": 1}))
        v = compute_variables(out)
        assert v["N_SUBFIELDS"] == "2"
        assert v["SUBFIELD_LIST"] == "First Bucket and Second Bucket"
        # 3 / (3+1) = 75.0%
        assert "| First Bucket | 3 | 75.0% |" in v["SUBFIELD_TABLE"]
        assert v["TOP_SUBFIELD"] == "First Bucket"
        assert v["TOP_SUBFIELD_PCT"] == "75.0"

    def test_hypothesis_table_pending_without_scores(self, tmp_path):
        out = self._project(tmp_path, self._CONFIG)
        (out / "data" / "corpus.jsonl").write_text("")
        v = compute_variables(out)
        assert v["N_HYPOTHESES"] == "2"
        assert v["HYPOTHESIS_LIST"] == "H1 Primary Claim; H2 Secondary Claim"
        assert "| H1 | Primary Claim | clinical | pending |" in v["HYPOTHESIS_TABLE"]

    def test_hypothesis_table_merges_scores(self, tmp_path):
        out = self._project(tmp_path, self._CONFIG)
        (out / "data" / "corpus.jsonl").write_text("")
        (out / "data" / "hypothesis_scores.json").write_text(json.dumps({"H1": 0.42}))
        v = compute_variables(out)
        assert "| H1 | Primary Claim | clinical | +0.42 |" in v["HYPOTHESIS_TABLE"]
        # H2 has no score -> still pending
        assert "| H2 | Secondary Claim | applied | pending |" in v["HYPOTHESIS_TABLE"]

    def test_fallbacks_when_config_absent(self, tmp_path):
        # output_dir with no sibling manuscript/config.yaml -> safe fallbacks
        out = tmp_path / "output"
        (out / "data").mkdir(parents=True)
        (out / "data" / "corpus.jsonl").write_text("")
        v = compute_variables(out)
        assert v["SEARCH_TERM"] == "the target topic"
        assert v["N_SUBFIELDS"] == "0"
        assert v["N_HYPOTHESES"] == "0"
        # engine fallback lists all seven
        assert v["N_ENGINES"] == "7"

    def test_tfidf_default(self, tmp_path):
        """NUM_VOCAB_FEATURES defaults to 500 when tfidf_data.json missing."""
        (tmp_path / "corpus.jsonl").write_text("")
        variables = compute_variables(tmp_path)
        assert variables["NUM_VOCAB_FEATURES"] == "pending"

    def test_tfidf_from_data(self, tmp_path):
        """NUM_VOCAB_FEATURES computed from tfidf_data.json feature_names."""
        (tmp_path / "corpus.jsonl").write_text("")
        tfidf = {"feature_names": ["word1", "word2", "word3"]}
        (tmp_path / "tfidf_data.json").write_text(json.dumps(tfidf))
        variables = compute_variables(tmp_path)
        assert variables["NUM_VOCAB_FEATURES"] == "3"
        assert variables["NUM_VOCAB_FEATURES_LATEX"] == "3"

    def test_data_subdir_fallback(self, tmp_path):
        """Variables are loaded from data/ subdirectory when present."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Put corpus in data/
        (data_dir / "corpus.jsonl").write_text('{"title":"A"}\n{"title":"B"}\n')
        variables = compute_variables(tmp_path)
        assert variables["CORPUS_SIZE"] == "2"


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
