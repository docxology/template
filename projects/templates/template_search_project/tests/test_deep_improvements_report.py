"""
Reading-report edge cases (zero papers, all-failed enrichment,
per-paper notes whose ``paper_id`` is missing from the citation map).
"""

from __future__ import annotations
from pathlib import Path
from infrastructure.search.literature import Paper, SearchQuery, SearchResult
from template_search_project.report import write_reading_report
from template_search_project.synthesis import SynthesisResult


# ---------------------------------------------------------------------------
# Reading-report edge cases
# ---------------------------------------------------------------------------


class TestReadingReportEdgeCases:
    """Pin the empty / partial-coverage behaviours of write_reading_report."""

    def test_zero_papers_writes_clean_report(self, tmp_path: Path) -> None:
        """Zero-paper run still writes a header, the topic line, and an
        explicit '(no source counts recorded)' marker rather than an
        empty markdown body."""
        result = SearchResult(
            query=SearchQuery(text="empty topic", max_results=10),
            papers=[],
            per_source_counts={},
        )
        out = write_reading_report(
            tmp_path / "report.md",
            search_result=result,
            citation_keys={},
        )
        text = out.read_text(encoding="utf-8")
        assert text.startswith("# Literature Reading Report")
        assert "_Topic:_ **empty topic**" in text
        assert "_results:_ 0" in text
        assert "## Summary by Source" in text
        assert "_(no source counts recorded)_" in text
        # Critically: no per-paper notes section is emitted when none exist.
        assert "## Per-Paper Notes" not in text
        assert "## Cross-Corpus Synthesis" not in text

    def test_all_failed_enrichment_papers_render_no_abstract_marker(self, tmp_path: Path) -> None:
        """Papers whose enrichment failed (no abstract attached) must
        render the documented ``(no abstract)`` placeholder rather than
        the literal Python ``None``."""
        papers = [
            Paper(id="x:1", title="No Abstract Paper", authors=["A One"], year=2020),
        ]
        result = SearchResult(
            query=SearchQuery(text="t"),
            papers=papers,
            per_source_counts={"local": 1},
            errors={"arxiv": "HTTP 503", "crossref": "HTTP 500"},
        )
        out = write_reading_report(
            tmp_path / "r.md",
            search_result=result,
            citation_keys={"x:1": "aone2020no"},
        )
        text = out.read_text(encoding="utf-8")
        # Backend errors must surface in the report header.
        assert "Partial coverage" in text
        assert "arxiv" in text and "HTTP 503" in text
        assert "crossref" in text and "HTTP 500" in text
        # The placeholder is the documented sentinel — never the literal
        # word "None" (which would point to a regression in
        # _format_paper_summary).
        assert "(no abstract)" in text
        assert "None" not in text

    def test_per_paper_note_with_unknown_paper_id_uses_question_mark_key(self, tmp_path: Path) -> None:
        """``write_reading_report`` is defensive about per-paper entries
        whose ``paper_id`` is not in the citation-key map: it falls back
        to ``paper_id`` itself, then to literal ``"?"``. This branch
        must never crash and the rendered note still includes the
        body text so reviewers see *something*.
        """
        result = SearchResult(query=SearchQuery(text="t"), papers=[], per_source_counts={})
        out = write_reading_report(
            tmp_path / "r.md",
            search_result=result,
            citation_keys={},
            per_paper=[
                SynthesisResult(
                    kind="per_paper",
                    prompt="p",
                    text="orphan note body",
                    paper_id=None,
                )
            ],
        )
        text = out.read_text(encoding="utf-8")
        assert "## Per-Paper Notes" in text
        assert "[?]" in text
        assert "orphan note body" in text
