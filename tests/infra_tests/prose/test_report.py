"""Tests for infrastructure.prose.report — manuscript-level aggregation."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.prose.report import (
    FileReport,
    ManuscriptReport,
    analyze_files,
    analyze_manuscript,
    analyze_text,
    load_report_json,
    write_report,
)


class TestAnalyzeText:
    def test_basic(self):
        # Heading text counts as prose after Markdown stripping
        # ("Hello" + "A body of text" = 5 words).
        report = analyze_text("intro.md", "# Hello\n\nA body of text.")
        assert isinstance(report, FileReport)
        assert report.name == "intro.md"
        assert report.metrics.word_count == 5
        assert report.structure.has_h1 is True


class TestAnalyzeFiles:
    def test_aggregates_word_counts(self):
        files = {
            "a.md": "# A\n\none two three four five.",
            "b.md": "# B\n\nsix seven eight.",
        }
        report = analyze_files(files)
        assert report.total_words == 10
        assert len(report.files) == 2
        assert report.total_paragraphs >= 2

    def test_citation_keys_deduplicated(self):
        files = {
            "a.md": "Cite [@k1] [@k2].",
            "b.md": "Cite [@k1] again.",
        }
        report = analyze_files(files)
        assert sorted(report.citation_keys) == ["k1", "k2"]

    def test_empty(self):
        report = analyze_files({})
        assert isinstance(report, ManuscriptReport)
        assert report.total_words == 0


class TestAnalyzeManuscript:
    def test_round_trip_to_disk(self, tmp_path: Path):
        man = tmp_path / "manuscript"
        man.mkdir()
        (man / "00_abstract.md").write_text("# Abstract\n\nWe study reproducibility [@peng2011reproducible].")
        (man / "01_introduction.md").write_text("# Introduction\n\nThe field has grown rapidly.")

        report = analyze_manuscript(man)
        assert report.total_words > 0
        assert "peng2011reproducible" in report.citation_keys

        out_path = write_report(report, tmp_path / "report.json")
        assert out_path.exists()
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["total_words"] == report.total_words
        assert "files" in payload


class TestManuscriptReportRoundTrip:
    def test_from_dict_matches_analyze_files(self):
        files = {
            "a.md": "# A\n\none two three four five.",
            "b.md": "# B\n\nsix seven eight [@k1].",
        }
        report = analyze_files(files)
        payload = json.loads(report.to_json())
        loaded = ManuscriptReport.from_dict(payload)
        assert loaded.total_words == report.total_words
        assert loaded.citation_keys == report.citation_keys
        assert len(loaded.files) == len(report.files)

    def test_load_report_json(self, tmp_path: Path):
        files = {"intro.md": "# Hello\n\nA body of text."}
        report = analyze_files(files)
        path = tmp_path / "report.json"
        path.write_text(report.to_json(), encoding="utf-8")
        loaded = load_report_json(path)
        assert loaded.total_words == report.total_words
        assert loaded.files[0].name == "intro.md"
