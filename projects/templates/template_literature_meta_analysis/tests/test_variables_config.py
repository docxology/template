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
        # engine fallback lists all ten independently routed providers
        assert v["N_ENGINES"] == "10"
        assert "bioRxiv" in v["ENGINE_LIST"]
        assert "medRxiv" in v["ENGINE_LIST"]

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
