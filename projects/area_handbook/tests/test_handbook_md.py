"""Tests for markdown rendering helpers."""

from __future__ import annotations

from pathlib import Path

from src.corpus_io import load_corpus, load_corpus_from_dict
from src.handbook_md import (
    build_evidence_by_theme_table_md,
    build_executive_summary_md,
    build_full_handbook_body,
    build_gap_report_md,
    build_glossary_md,
    build_toc_md,
    render_section_markdown,
)
from src.synthesis import synthesize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


class TestHandbookMd:
    def test_executive_summary_contains_area(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        text = build_executive_summary_md(s)
        assert "Riverbend" in text
        assert "riverbend_metro" in text
        assert "Coverage threshold" in text
        assert "Themes with no evidence" in text

    def test_render_section_unknown(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        md = render_section_markdown("no_such", s)
        assert "Unknown section" in md

    def test_render_section_known(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        md = render_section_markdown("04_landscape", s)
        assert "## Landscape and setting" in md
        assert "Coverage score" in md
        assert "watershed" in md.lower() or "Regional" in md

    def test_full_body_non_empty(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        body = build_full_handbook_body(s)
        assert len(body) > 200
        assert body.endswith("\n")
        assert "Gap report" in body
        assert "Evidence volume by theme" in body

    def test_gap_report_no_gaps(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        gr = build_gap_report_md(s)
        assert "No gap sections" in gr

    def test_gap_report_lists_rows(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "a",
                "area_label": "A",
                "version": "1",
                "themes": [{"id": "t", "label": "T", "description": "d"}],
                "evidence": [],
            }
        )
        s = synthesize(c)
        gr = build_gap_report_md(s)
        assert "04_landscape" in gr
        assert "|" in gr

    def test_toc_lists_sections(self) -> None:
        c = load_corpus(FIXTURE)
        s = synthesize(c)
        toc = build_toc_md(s)
        assert "04_landscape" in toc
        assert "Handbook outline" in toc
        assert "  - `10_risks`" in toc

    def test_evidence_by_theme_table(self) -> None:
        c = load_corpus(FIXTURE)
        tbl = build_evidence_by_theme_table_md(c)
        assert "landscape" in tbl
        assert "Evidence volume by theme" in tbl

    def test_evidence_by_theme_includes_zero_rows(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "a",
                "area_label": "A",
                "version": "1",
                "themes": [
                    {"id": "used", "label": "U", "description": "d"},
                    {"id": "unused_theme", "label": "U2", "description": "d"},
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
        tbl = build_evidence_by_theme_table_md(c)
        assert "| `unused_theme` | 0 |" in tbl

    def test_glossary_table(self) -> None:
        c = load_corpus(FIXTURE)
        g = build_glossary_md(c)
        assert "Theme glossary" in g
        assert "landscape" in g

    def test_glossary_escapes_pipe(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "p",
                "area_label": "P",
                "version": "1",
                "themes": [
                    {
                        "id": "t",
                        "label": "T",
                        "description": "a|b pipe",
                    }
                ],
                "evidence": [],
            }
        )
        g = build_glossary_md(c)
        assert "\\|" in g or "a\\|b" in g

    def test_bullet_truncation_many_items(self) -> None:
        themes = [{"id": "landscape", "label": "L", "description": "d"}]
        evidence = [
            {
                "id": f"e{i}",
                "statement": f"fact {i}",
                "theme": "landscape",
                "weight": 0.05,
                "source_label": "s",
                "reviewed_at": "2025-01-01",
            }
            for i in range(20)
        ]
        c = load_corpus_from_dict(
            {
                "area_id": "big",
                "area_label": "Big",
                "version": "1",
                "themes": themes,
                "evidence": evidence,
            }
        )
        s = synthesize(c)
        md = render_section_markdown("04_landscape", s)
        assert "more items" in md

    def test_empty_evidence_section(self) -> None:
        c = load_corpus_from_dict(
            {
                "area_id": "e",
                "area_label": "E",
                "version": "1",
                "themes": [
                    {"id": "landscape", "label": "L", "description": "d"},
                    {"id": "communities", "label": "C", "description": "d"},
                ],
                "evidence": [
                    {
                        "id": "e1",
                        "statement": "only landscape",
                        "theme": "landscape",
                        "weight": 0.2,
                        "source_label": "s",
                        "reviewed_at": "2025-01-01",
                    }
                ],
            }
        )
        s = synthesize(c)
        md = render_section_markdown("05_communities", s)
        assert "No evidence mapped" in md
