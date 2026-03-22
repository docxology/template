"""Tests for corpus_stats helpers."""

from __future__ import annotations

from pathlib import Path

from src.corpus_io import load_corpus, load_corpus_from_dict
from src.corpus_stats import evidence_counts_by_theme, themes_without_evidence, total_evidence_weight

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


def test_counts_fixture_matches_evidence() -> None:
    c = load_corpus(FIXTURE)
    counts = evidence_counts_by_theme(c)
    assert sum(counts.values()) == len(c.evidence)
    assert counts["landscape"] == 2


def test_themes_without_evidence_empty_for_fixture() -> None:
    c = load_corpus(FIXTURE)
    assert themes_without_evidence(c) == ()


def test_themes_without_evidence_detects_unused() -> None:
    c = load_corpus_from_dict(
        {
            "area_id": "a",
            "area_label": "A",
            "version": "1",
            "themes": [
                {"id": "used", "label": "U", "description": "d"},
                {"id": "orphan", "label": "O", "description": "d"},
            ],
            "evidence": [
                {
                    "id": "e1",
                    "statement": "x",
                    "theme": "used",
                    "weight": 1.0,
                    "source_label": "s",
                    "reviewed_at": "2025-01-01",
                }
            ],
        }
    )
    assert themes_without_evidence(c) == ("orphan",)


def test_total_weight() -> None:
    c = load_corpus_from_dict(
        {
            "area_id": "a",
            "area_label": "A",
            "version": "1",
            "themes": [{"id": "t", "label": "T", "description": "d"}],
            "evidence": [
                {
                    "id": "e1",
                    "statement": "a",
                    "theme": "t",
                    "weight": 0.25,
                    "source_label": "s",
                    "reviewed_at": "2025-01-01",
                },
                {
                    "id": "e2",
                    "statement": "b",
                    "theme": "t",
                    "weight": 0.5,
                    "source_label": "s",
                    "reviewed_at": "2025-01-02",
                },
            ],
        }
    )
    assert total_evidence_weight(c) == 0.75
