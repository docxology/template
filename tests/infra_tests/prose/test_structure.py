"""Tests for infrastructure.prose.analysis.structure."""

from __future__ import annotations

from infrastructure.prose.analysis.structure import (
    Heading,
    analyze_structure,
    parse_headings,
    render_outline,
)


class TestParseHeadings:
    def test_atx_headings(self):
        text = "# Title\n\n## Section\n\n### Subsection\n"
        headings = parse_headings(text)
        assert len(headings) == 3
        assert headings[0] == Heading(level=1, title="Title", line=1)
        assert headings[1].level == 2
        assert headings[2].level == 3

    def test_skips_code_fence_pseudo_headings(self):
        text = "# Real\n\n```python\n# This looks like a heading but is not\n```\n"
        headings = parse_headings(text)
        assert [h.title for h in headings] == ["Real"]

    def test_six_levels(self):
        text = "\n".join(f"{'#' * i} L{i}" for i in range(1, 7))
        headings = parse_headings(text)
        assert [h.level for h in headings] == [1, 2, 3, 4, 5, 6]

    def test_no_headings(self):
        assert parse_headings("Just some prose.\n") == []


class TestAnalyzeStructure:
    def test_total_words_sums_sections(self):
        text = "# A\n\nFirst body has four words.\n\n## B\n\nSecond body."
        report = analyze_structure(text)
        assert report.total_words >= 6
        assert len(report.sections) == 2

    def test_section_word_counts(self):
        text = "# Title\n\nOne two three.\n\n## Sub\n\nA B."
        report = analyze_structure(text)
        # Body of "Title" stops where "## Sub" starts.
        assert report.sections[0].word_count == 3
        assert report.sections[1].word_count == 2

    def test_max_depth(self):
        text = "# A\n\n## B\n\n### C\n\n#### D\n"
        report = analyze_structure(text)
        assert report.max_depth == 4

    def test_has_h1(self):
        assert analyze_structure("# Hello").has_h1 is True
        assert analyze_structure("## Hello").has_h1 is False

    def test_skipped_level_detected(self):
        text = "# A\n\n### Skipped to L3\n"
        report = analyze_structure(text)
        assert report.has_skipped_level is True

    def test_proper_nesting_no_skip(self):
        text = "# A\n\n## B\n\n### C\n\n## D\n"
        report = analyze_structure(text)
        assert report.has_skipped_level is False

    def test_to_dict_keys(self):
        report = analyze_structure("# A\n\nbody")
        d = report.to_dict()
        assert "headings" in d
        assert "sections" in d
        assert "max_depth" in d


class TestRenderOutline:
    def test_indented_outline(self):
        text = "# Top\n\n## Mid\n\n### Bottom\n"
        outline = render_outline(analyze_structure(text))
        assert "- Top" in outline
        assert "  - Mid" in outline
        assert "    - Bottom" in outline
