"""Tests for infrastructure.rendering._pdf_latex_helpers module.

Tests using real temp files (No Mocks Policy).
"""

from __future__ import annotations

import yaml
import pytest

from infrastructure.rendering._pdf_latex_helpers import (
    check_latex_log_for_graphics_errors,
    ensure_setmathfont,
    extract_math_font_preamble,
    extract_preamble,
    generate_title_page_body,
    generate_title_page_preamble,
    parse_missing_latex_package_from_log,
)


class TestExtractMathFontPreamble:
    """Tests for extract_math_font_preamble (slides Beamer math header shim)."""

    def test_returns_none_when_no_unicode_math(self):
        preamble = "\\usepackage{geometry}\n\\usepackage{hyperref}\n"
        assert extract_math_font_preamble(preamble) is None

    def test_returns_none_for_empty_preamble(self):
        assert extract_math_font_preamble("") is None

    def test_unicode_math_without_setmathfont_emits_default(self):
        preamble = "\\usepackage{geometry}\n\\usepackage{unicode-math}\n"
        snippet = extract_math_font_preamble(preamble)
        assert snippet is not None
        assert "\\usepackage{unicode-math}" in snippet
        assert "\\setmathfont{latinmodern-math.otf}" in snippet
        # Geometry / hyperref MUST NOT leak into the slides header.
        assert "geometry" not in snippet
        assert "hyperref" not in snippet

    def test_explicit_setmathfont_preserved(self):
        preamble = "\\usepackage{unicode-math}\n\\setmathfont{XITS Math}\n\\usepackage{geometry}\n"
        snippet = extract_math_font_preamble(preamble)
        assert snippet is not None
        assert "\\setmathfont{XITS Math}" in snippet
        # Exactly one \setmathfont line — no double declaration.
        assert snippet.count("\\setmathfont") == 1
        assert "latinmodern-math.otf" not in snippet

    def test_standalone_setmathfont_implies_unicode_math(self):
        """Real-world case (e.g. fep_lean): ``\\setmathfont`` declared
        without an explicit ``\\usepackage{unicode-math}``. The helper
        still emits a complete header so Beamer can resolve the macro.
        """
        preamble = "\\usepackage{geometry}\n\\usepackage{fontspec}\n\\setmathfont{latinmodern-math.otf}\n"
        snippet = extract_math_font_preamble(preamble)
        assert snippet is not None
        assert "\\usepackage{unicode-math}" in snippet
        assert "\\setmathfont{latinmodern-math.otf}" in snippet
        assert "geometry" not in snippet
        assert "fontspec" not in snippet


class TestSuggestedCitationDoi:
    def test_suggested_citation_includes_doi_when_configured(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        config = manuscript_dir / "config.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "book": {
                        "title": "Introduction to Biology",
                        "subtitle": "A Generative Approach",
                        "author": "Daniel Ari Friedman",
                        "edition": "1.0",
                        "year": 2026,
                    },
                    "publication": {"doi": "10.5281/zenodo.1234567"},
                }
            ),
            encoding="utf-8",
        )
        body = generate_title_page_body(manuscript_dir)
        assert "Suggested citation:" in body
        assert "10.5281/zenodo.1234567" in body
        assert "https://doi.org/10.5281/zenodo.1234567" in body
        assert r"{\small DOI: \href{https://doi.org/10.5281/zenodo.1234567}" in body

    def test_suggested_citation_separates_repository_and_doi(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        config = manuscript_dir / "config.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "book": {"title": "T", "author": "A", "edition": "1.0", "year": 2026},
                    "publication": {
                        "doi": "10.5281/zenodo.1234567",
                        "repository_url": "https://github.com/docxology/biology_textbook",
                    },
                }
            ),
            encoding="utf-8",
        )
        body = generate_title_page_body(manuscript_dir)
        assert "Suggested citation:" in body
        assert r"\href{https://github.com/docxology/biology_textbook}" in body
        assert r"\href{https://doi.org/10.5281/zenodo.1234567}{https://doi.org/10.5281/zenodo.1234567}." in body


class TestExtractPreamble:
    """Tests for extract_preamble."""

    def test_extracts_latex_block(self, tmp_path):
        """Extracts content from ```latex ... ``` block."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{geometry}\n```\n")
        result = extract_preamble(preamble_file)
        assert "\\usepackage{geometry}" in result

    def test_returns_empty_for_missing_file(self, tmp_path):
        """Missing file returns empty string."""
        result = extract_preamble(tmp_path / "nonexistent.md")
        assert result == ""

    def test_returns_empty_for_no_latex_block(self, tmp_path):
        """File with no latex block returns empty string."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("# Just markdown\nNo LaTeX here.\n")
        result = extract_preamble(preamble_file)
        assert result == ""

    def test_extracts_multiple_blocks(self, tmp_path):
        """Combines multiple ```latex blocks."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{geometry}\n```\n\n```latex\n\\usepackage{amsmath}\n```\n")
        result = extract_preamble(preamble_file)
        assert "\\usepackage{geometry}" in result
        assert "\\usepackage{amsmath}" in result

    def test_strips_whitespace(self, tmp_path):
        """Strips leading/trailing whitespace from extracted content."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n  \\usepackage{geometry}  \n```\n")
        result = extract_preamble(preamble_file)
        assert result.strip() == "\\usepackage{geometry}"

    def test_recovers_raw_unfenced_latex(self, tmp_path):
        """Regression: raw LaTeX with no ```latex fence is recovered, not dropped.

        Previously an unfenced preamble.md (e.g. declaring \\geometry{margin=...})
        returned "" silently, so manuscript-declared margins/fonts never reached the
        PDF. The whitelist fallback now recovers LaTeX-command lines.
        """
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text(
            "\\usepackage{amsmath,amssymb}\n"
            "\\geometry{margin=0.25in}\n"
            "\\changefontsize{9pt}{11pt}\n"
        )
        result = extract_preamble(preamble_file)
        assert "\\geometry{margin=0.25in}" in result
        assert "\\changefontsize{9pt}{11pt}" in result

    def test_raw_fallback_drops_non_command_prose(self, tmp_path):
        """Negative control: prose lines are NOT injected into the preamble.

        Only whitelisted LaTeX-command lines survive the raw fallback, so stray body
        text in an unfenced preamble.md cannot leak into the LaTeX preamble.
        """
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text(
            "Some prose introduction.\n"
            "\\usepackage{xcolor}\n"
            "more prose that must not reach the preamble\n"
            "\\setlength{\\parindent}{0pt}\n"
        )
        result = extract_preamble(preamble_file)
        assert "\\usepackage{xcolor}" in result
        assert "\\setlength{\\parindent}{0pt}" in result
        assert "prose" not in result

    def test_raw_fallback_drops_multiline_command_not_truncated(self, tmp_path):
        """Well-formedness control: a multi-line command is dropped, never truncated.

        Recovering a multi-line construct line-by-line would emit an unbalanced
        ``\\newcommand{\\foo}{%`` fragment — malformed LaTeX worse than dropping it.
        Only the balanced single-line directive survives.
        """
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text(
            "\\newcommand{\\foo}{%\n"
            "  multi-line body\n"
            "}\n"
            "\\usepackage{xcolor}\n"
        )
        result = extract_preamble(preamble_file)
        assert "\\newcommand" not in result, "unbalanced multi-line opener must be dropped"
        assert "\\usepackage{xcolor}" in result
        # The recovered preamble is brace-balanced (no truncated fragment leaked).
        assert result.count("{") == result.count("}")

    def test_raw_fallback_drops_input_scope_expansion(self, tmp_path):
        r"""\input is NOT recovered — it would pull an arbitrary file into the preamble."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("\\input{../../elsewhere.tex}\n\\geometry{margin=0.5in}\n")
        result = extract_preamble(preamble_file)
        assert "input" not in result, "\\input must be dropped (scope expansion)"
        assert "\\geometry{margin=0.5in}" in result

    def test_unicode_math_gets_setmathfont_injected(self, tmp_path):
        """When unicode-math is loaded without \\setmathfont, one is auto-injected."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{unicode-math}\n```\n")
        result = extract_preamble(preamble_file)
        assert "\\setmathfont{latinmodern-math.otf}" in result

    def test_existing_setmathfont_preserved(self, tmp_path):
        """User-supplied \\setmathfont is not overridden."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{unicode-math}\n\\setmathfont{XITSMath-Regular.otf}\n```\n")
        result = extract_preamble(preamble_file)
        assert result.count("\\setmathfont") == 1
        assert "XITSMath" in result
        assert "latinmodern-math.otf" not in result


class TestEnsureSetmathfont:
    """Tests for the constitutional ``\\setmathfont`` injector."""

    def test_no_unicode_math_no_change(self):
        original = "\\usepackage{geometry}\n\\usepackage{amsmath}"
        assert ensure_setmathfont(original) == original

    def test_unicode_math_appends_default(self):
        result = ensure_setmathfont("\\usepackage{unicode-math}")
        assert "\\setmathfont{latinmodern-math.otf}" in result

    def test_existing_setmathfont_no_change(self):
        original = "\\usepackage{unicode-math}\n\\setmathfont{Latin Modern Math}"
        assert ensure_setmathfont(original) == original

    def test_unicode_math_with_options_detected(self):
        result = ensure_setmathfont("\\usepackage[warnings-off={mathtools-colon}]{unicode-math}")
        assert "\\setmathfont" in result

    def test_requirepackage_form_detected(self):
        result = ensure_setmathfont("\\RequirePackage{unicode-math}")
        assert "\\setmathfont" in result

    def test_custom_math_font_used(self):
        result = ensure_setmathfont("\\usepackage{unicode-math}", math_font="STIX2Math.otf")
        assert "\\setmathfont{STIX2Math.otf}" in result

    def test_empty_preamble_no_change(self):
        assert ensure_setmathfont("") == ""


class TestCheckLatexLogForGraphicsErrors:
    """Tests for check_latex_log_for_graphics_errors."""

    def test_returns_empty_for_missing_log(self, tmp_path):
        """Missing log file returns empty lists."""
        result = check_latex_log_for_graphics_errors(tmp_path / "missing.log")
        assert result == {"graphics_errors": [], "graphics_warnings": [], "missing_files": []}

    def test_detects_missing_file(self, tmp_path):
        """Detects 'File not found' error pattern."""
        log_file = tmp_path / "test.log"
        log_file.write_text("File `figure.png` not found\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert "figure.png" in result["missing_files"]

    def test_detects_includegraphics_undefined(self, tmp_path):
        """Detects undefined includegraphics control sequence."""
        log_file = tmp_path / "test.log"
        log_file.write_text(r"! Undefined control sequence \includegraphics" + "\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert len(result["graphics_errors"]) > 0

    def test_clean_log_returns_empty(self, tmp_path):
        """Log with no graphics errors returns empty lists."""
        log_file = tmp_path / "test.log"
        log_file.write_text("This is a clean LaTeX compile log.\nNo errors.\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert result["missing_files"] == []
        assert result["graphics_errors"] == []


class TestGenerateTitlePagePreamble:
    """Tests for generate_title_page_preamble."""

    def _write_config(self, tmp_path, config: dict) -> None:
        (tmp_path / "config.yaml").write_text(yaml.dump(config))

    def test_returns_empty_for_missing_config(self, tmp_path):
        """Returns empty string when config.yaml doesn't exist."""
        result = generate_title_page_preamble(tmp_path)
        assert result == ""

    def test_includes_title_command(self, tmp_path):
        """\\title{} command appears in preamble."""
        self._write_config(tmp_path, {"paper": {"title": "My Research"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\title{My Research}" in result

    def test_subtitle_not_embedded_in_title_command(self, tmp_path):
        """Subtitle renders on the title page body, not inside \\title{} metadata."""
        self._write_config(
            tmp_path,
            {"paper": {"title": "Main Title", "subtitle": "A Subtitle"}},
        )
        preamble = generate_title_page_preamble(tmp_path)
        body = generate_title_page_body(tmp_path)
        assert r"\title{Main Title}" in preamble
        assert r"\\normalsize" not in preamble
        assert r"{\large A Subtitle" in body

    def test_includes_author_command(self, tmp_path):
        """\\author{} appears when authors defined."""
        self._write_config(
            tmp_path,
            {"paper": {"title": "Test"}, "authors": [{"name": "Alice Smith"}]},
        )
        result = generate_title_page_preamble(tmp_path)
        assert "\\author{" in result
        assert "Alice Smith" in result

    def test_uses_today_when_no_date(self, tmp_path):
        """\\date{\\today} used when config has no date field."""
        self._write_config(tmp_path, {"paper": {"title": "Test"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\date{\\today}" in result

    def test_includes_provided_date(self, tmp_path):
        """Explicit date used when config has date field."""
        self._write_config(tmp_path, {"paper": {"title": "T", "date": "March 2026"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\date{March 2026}" in result

    def test_returns_string(self, tmp_path):
        """Always returns a string."""
        self._write_config(tmp_path, {"paper": {"title": "Test"}})
        result = generate_title_page_preamble(tmp_path)
        assert isinstance(result, str)

    def test_singular_affiliation_string(self, tmp_path):
        """Single affiliation string renders on title page."""
        self._write_config(
            tmp_path,
            {
                "paper": {"title": "Test"},
                "authors": [{"name": "Alice", "affiliation": "MIT"}],
            },
        )
        result = generate_title_page_preamble(tmp_path)
        assert "MIT" in result

    def test_plural_affiliations_list_all_rendered(self, tmp_path):
        """Multiple affiliations from list all appear on title page."""
        self._write_config(
            tmp_path,
            {
                "paper": {"title": "Test"},
                "authors": [
                    {
                        "name": "Joel Dietz",
                        "affiliations": [
                            "Massachusetts Institute of Technology (MIT)",
                            "California Institute for Machine Consciousness (CIMC)",
                        ],
                    }
                ],
            },
        )
        result = generate_title_page_preamble(tmp_path)
        assert "Massachusetts Institute of Technology (MIT)" in result
        assert "California Institute for Machine Consciousness (CIMC)" in result

    def test_both_authors_affiliations_rendered(self, tmp_path):
        """Both authors with different affiliation formats all appear."""
        self._write_config(
            tmp_path,
            {
                "paper": {"title": "Test"},
                "authors": [
                    {"name": "Daniel Friedman", "affiliations": ["Active Inference Institute"]},
                    {
                        "name": "Joel Dietz",
                        "affiliations": [
                            "Massachusetts Institute of Technology (MIT)",
                            "California Institute for Machine Consciousness (CIMC)",
                        ],
                    },
                ],
            },
        )
        result = generate_title_page_preamble(tmp_path)
        assert "Active Inference Institute" in result
        assert "Massachusetts Institute of Technology (MIT)" in result
        assert "California Institute for Machine Consciousness (CIMC)" in result


class TestGenerateTitlePageBody:
    """Tests for generate_title_page_body."""

    def test_returns_maketitle_when_config_exists(self, tmp_path):
        """Returns \\maketitle when config.yaml is present."""
        (tmp_path / "config.yaml").write_text(yaml.dump({"paper": {"title": "Test"}}))
        result = generate_title_page_body(tmp_path)
        assert "\\maketitle" in result

    def test_book_publishing_page_supports_quote_and_acknowledgement_blocks(self, tmp_path):
        """Book configs may add page-two quote and acknowledgement boxes."""
        (tmp_path / "config.yaml").write_text(
            yaml.dump(
                {
                    "book": {
                        "title": "Book Title",
                        "subtitle": "Book Subtitle",
                        "author": "Author Name",
                        "license": "CC BY 4.0",
                    },
                    "front_matter": {
                        "page_two_quote": {
                            "text": "A quoted line with 100% evidence.",
                            "attribution": "Source Name",
                        },
                        "page_two_acknowledgements": {
                            "title": "Thanks",
                            "text": "A compact acknowledgement with one paragraph.",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result = generate_title_page_body(tmp_path)

        assert "Publishing Information" in result
        assert r"\fcolorbox{red!55!black}{red!3}" in result
        assert r"A quoted line with 100\% evidence." in result
        assert "Source Name" in result
        assert r"\fcolorbox{black!35}{black!2}" in result
        assert "Thanks" in result
        assert "A compact acknowledgement with one paragraph." in result
        assert "\\end{minipage}%\n}\n\\par\n\\vspace{1.0em}" in result

    def test_book_publishing_page_includes_repository_url_and_doi(self, tmp_path):
        """Book publishing page emits DOI and optional repository_url from config."""
        (tmp_path / "config.yaml").write_text(
            yaml.dump(
                {
                    "book": {
                        "title": "Book Title",
                        "subtitle": "Book Subtitle",
                        "author": "Author Name",
                        "license": "CC BY 4.0",
                    },
                    "publication": {
                        "doi": "10.5281/zenodo.1234567",
                        "repository_url": "https://github.com/docxology/biology_textbook",
                        "repository_label": "Source repository",
                    },
                }
            ),
            encoding="utf-8",
        )
        result = generate_title_page_body(tmp_path)

        assert "Publishing Information" in result
        assert r"\href{https://doi.org/10.5281/zenodo.1234567}" in result
        assert r"{\small DOI: \href{https://doi.org/10.5281/zenodo.1234567}" in result
        assert r"\href{https://github.com/docxology/biology_textbook}" in result
        assert "Source repository" in result
        assert "via the source repository linked above." in result

    def test_returns_string(self, tmp_path):
        """Always returns a string."""
        result = generate_title_page_body(tmp_path)
        assert isinstance(result, str)


class TestParseMissingLatexPackage:
    """Tests for parse_missing_latex_package_from_log."""

    @pytest.mark.parametrize(
        ("log_content", "expected"),
        [
            ("File `multirow.sty' not found\n", "multirow"),
            ("! LaTeX Error: File `cleveref.sty' not found\n", "cleveref"),
            ("All good, no errors.\n", None),
        ],
    )
    def test_parse_missing_package_from_log(self, tmp_path, log_content: str, expected: str | None) -> None:
        log = tmp_path / "test.log"
        log.write_text(log_content, encoding="utf-8")
        assert parse_missing_latex_package_from_log(log) == expected

    def test_nonexistent_log(self, tmp_path):
        assert parse_missing_latex_package_from_log(tmp_path / "missing.log") is None


class TestErrorPaths:
    """Error-handler paths for latex helper IO and YAML parsing."""

    def test_check_latex_log_unreadable(self, tmp_path):
        import stat

        log = tmp_path / "test.log"
        log.write_text("File `figure.png` not found\n", encoding="utf-8")
        log.chmod(0o000)
        try:
            result = check_latex_log_for_graphics_errors(log)
            assert isinstance(result, dict)
        finally:
            log.chmod(stat.S_IRWXU)

    def test_generate_title_page_preamble_invalid_yaml(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: [\n  invalid yaml\n", encoding="utf-8")
        assert generate_title_page_preamble(tmp_path) == ""

    def test_generate_title_page_body_invalid_yaml(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: [\n  broken\n", encoding="utf-8")
        assert generate_title_page_body(tmp_path) == ""

    def test_parse_missing_latex_package_unreadable(self, tmp_path):
        import stat

        log = tmp_path / "test.log"
        log.write_text("File `multirow.sty' not found\n", encoding="utf-8")
        log.chmod(0o000)
        try:
            assert parse_missing_latex_package_from_log(log) is None
        finally:
            log.chmod(stat.S_IRWXU)
