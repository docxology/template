"""Tests for handbook_plot_data (gap-aware series for figures)."""

from __future__ import annotations

from pathlib import Path

from src.corpus_io import load_corpus, load_corpus_from_dict
from src.handbook_plot_data import section_scores_with_gap_flags
from src.metrics import build_metrics_report
from src.synthesis import synthesize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


def test_riverbend_sorted_and_matches_gap_list() -> None:
    c = load_corpus(FIXTURE)
    s = synthesize(c)
    m = build_metrics_report(s)
    labels, scores, flags, thr = section_scores_with_gap_flags(m)
    assert labels == sorted(m["scores_by_section"].keys())
    assert len(scores) == len(labels)
    assert thr == m["gap_threshold"]
    for i, sid in enumerate(labels):
        assert flags[i] == (sid in set(m["gap_section_ids"]))
    assert sum(flags) == m["gap_count"]


def test_sparse_corpus_marks_communities_gap() -> None:
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
    m = build_metrics_report(s)
    labels, _scores, flags, _thr = section_scores_with_gap_flags(m)
    assert flags[labels.index("05_communities")] is True
    # Single weak landscape row (0.1) is also below default threshold
    assert flags[labels.index("04_landscape")] is True
