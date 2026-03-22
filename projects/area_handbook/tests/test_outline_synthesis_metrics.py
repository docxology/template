"""Tests for outline, synthesis, and metrics modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.corpus_io import load_corpus, load_corpus_from_dict
from src.models import EvidenceItem
from src.metrics import build_metrics_report
from src.outline import HANDBOOK_TEMPLATE, build_handbook_outline
from src.synthesis import DEFAULT_GAP_THRESHOLD, section_coverage_score, synthesize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


class TestOutline:
    def test_template_length(self) -> None:
        assert len(HANDBOOK_TEMPLATE) == 8
        ids = [s.section_id for s in HANDBOOK_TEMPLATE]
        assert ids[0] == "04_landscape"
        assert ids[-1] == "11_recommendations"

    def test_build_outline_stable(self) -> None:
        c = load_corpus(FIXTURE)
        o = build_handbook_outline(c)
        assert o == HANDBOOK_TEMPLATE


class TestSectionCoverageScore:
    def test_empty(self) -> None:
        assert section_coverage_score(()) == 0.0

    def test_cap_at_one(self) -> None:
        ev = (
            EvidenceItem("a", "s", "t", 0.6, "src", "2025-01-01"),
            EvidenceItem("b", "s", "t", 0.6, "src", "2025-01-02"),
        )
        assert section_coverage_score(ev) == 1.0


class TestSynthesis:
    def test_scores_and_gaps_fixture(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        assert len(s.sections) == 8
        assert s.gap_threshold == DEFAULT_GAP_THRESHOLD
        assert set(s.scores.keys()) == {x.section_id for x in s.sections}
        for sid, score in s.scores.items():
            assert 0.0 <= score <= 1.0
        # Fixture is rich; expect no gaps under default threshold
        assert s.gaps == ()

    def test_gap_threshold_invalid(self) -> None:
        c = load_corpus(FIXTURE)
        with pytest.raises(ValueError, match="gap_threshold"):
            synthesize(c, gap_threshold=1.5)

    def test_stricter_threshold_more_gaps(self) -> None:
        c = load_corpus(FIXTURE)
        loose = synthesize(c, gap_threshold=0.01)
        strict = synthesize(c, gap_threshold=0.95)
        assert len(strict.gaps) >= len(loose.gaps)

    def test_gap_when_sparse(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "sparse",
                "area_label": "Sparse",
                "version": "1",
                "themes": [
                    {"id": "landscape", "label": "L", "description": "d"},
                    {"id": "communities", "label": "C", "description": "d"},
                ],
                "evidence": [
                    {
                        "id": "e1",
                        "statement": "one fact",
                        "theme": "landscape",
                        "weight": 0.1,
                        "source_label": "s",
                        "reviewed_at": "2025-01-01",
                    }
                ],
            }
        )
        s = synthesize(c)
        assert "05_communities" in s.gaps
        assert s.scores["04_landscape"] == 0.1


class TestMetrics:
    def test_metrics_shape(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        m = build_metrics_report(s)
        assert m["area_id"] == "riverbend_metro"
        assert m["evidence_count"] == len(c.evidence)
        assert m["section_count"] == 8
        assert 0.0 <= m["coverage_ratio"] <= 1.0
        assert isinstance(m["scores_by_section"], dict)
        assert m["gap_threshold"] == s.gap_threshold
        assert m["gap_count"] == len(s.gaps)
        assert "mean_section_score" in m
        assert "evidence_count_by_theme" in m
        assert m["themes_without_evidence"] == []
        assert m["total_evidence_weight"] > 0

    def test_metrics_zero_sections_edge(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "x",
                "area_label": "X",
                "version": "1",
                "themes": [{"id": "t", "label": "T", "description": "d"}],
                "evidence": [],
            }
        )
        # Synthesis still uses template with 8 sections
        s = synthesize(c)
        m = build_metrics_report(s)
        assert m["coverage_ratio"] == 0.0
        assert m["gap_count"] == len(s.sections)
        assert m["mean_section_score"] == 0.0
