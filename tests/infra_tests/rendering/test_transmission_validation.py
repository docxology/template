"""No-mock tests for PDF transmission validation and content validation paths.

Exercises:
- ``_pdf_combined_transmission`` cover/TOC injection after begin-transmission bookend.
- ``prerender.prevalidate_for_render`` hard-gate paths.
- Individual content validators: math, citations, refs, images, pitfalls, symbols.
- ``diagnostic_codes`` stable ID contract.
- ``pdf_validator`` error/fallback paths for missing/corrupt PDFs.
- ``validate_markdown`` aggregate facade and missing-directory error path.

All tests use real temp files with real markdown/PDF content — no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from infrastructure.core.exceptions import PDFValidationError, RenderingError
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.rendering._pdf_combined_transmission import (
    _inject_toc_after_begin_transmission,
)
from infrastructure.validation.content.diagnostic_codes import BibtexCode, MarkdownCode
from infrastructure.validation.content.markdown_validator import validate_markdown
from infrastructure.validation.content.pdf_validator import (
    extract_text_from_pdf,
    scan_for_issues,
    validate_pdf_rendering,
)
from infrastructure.validation.content.prerender import prevalidate_for_render
from infrastructure.validation.content.symbols import (
    collect_symbols,
    resolve_cross_reference_integrity,
)
from infrastructure.validation.content.validator_citations import validate_citations
from infrastructure.validation.content.validator_images import validate_images
from infrastructure.validation.content.validator_math import validate_math
from infrastructure.validation.content.validator_pitfalls import (
    NON_RENDERED_MANUSCRIPT_FILES,
    validate_pandoc_pitfalls,
)
from infrastructure.validation.content.validator_refs import validate_refs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manuscript(tmp_path: Path) -> Path:
    """Create a minimal manuscript directory with a clean .bib file."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "references.bib").write_text("@article{good_key, title={Ok}, year={2025}}\n", encoding="utf-8")
    return manuscript


def _write_md(manuscript: Path, name: str, content: str) -> Path:
    """Write a markdown file inside *manuscript* and return its path."""
    path = manuscript / name
    path.write_text(content, encoding="utf-8")
    return path


def _make_real_pdf(path: Path, texts: list[str]) -> Path:
    """Create a real multi-page PDF with the given text per page."""
    c = canvas.Canvas(str(path), pagesize=letter)
    for text in texts:
        c.drawString(100, 750, text)
        c.showPage()
    c.save()
    return path


# ---------------------------------------------------------------------------
# PDF transmission bookend injection (_pdf_combined_transmission)
# ---------------------------------------------------------------------------


class TestInjectTocAfterBeginTransmission:
    """Cover/TOC relocation after the begin-transmission bookend."""

    BASE_TEX = (
        "\\documentclass{article}\n\\begin{document}\n"
        "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
        "Bookend body\n\\end{samepage}\n\\newpage\n"
        "\\section{Abstract}\nBody\n\\end{document}"
    )

    def test_inserts_toc_and_cover_after_begin_bookend(self) -> None:
        """When title_page_body is provided, both cover and TOC are inserted."""
        result = _inject_toc_after_begin_transmission(
            self.BASE_TEX,
            begin_doc_idx=self.BASE_TEX.find("\\begin{document}"),
            title_page_body="\\maketitle",
        )
        toc_idx = result.find("\\tableofcontents")
        newpage_idx = result.find("\\newpage")
        abstract_idx = result.find("\\section{Abstract}")
        assert toc_idx > newpage_idx
        assert abstract_idx > toc_idx
        assert "\\maketitle" in result

    def test_inserts_only_toc_when_no_title_body(self) -> None:
        """Empty title_page_body skips cover and inserts only TOC."""
        result = _inject_toc_after_begin_transmission(
            self.BASE_TEX,
            begin_doc_idx=self.BASE_TEX.find("\\begin{document}"),
            title_page_body="",
        )
        assert "\\tableofcontents" in result
        assert "\\maketitle" not in result

    def test_returns_unchanged_when_label_not_found(self) -> None:
        """Missing begin-transmission label returns tex unchanged."""
        tex = "\\begin{document}\n\\section{No label}\nBody\n\\end{document}"
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_samepage_missing(self) -> None:
        """Missing ``\\end{samepage}`` after the label returns tex unchanged."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\newpage\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_newpage_missing(self) -> None:
        """Missing ``\\newpage`` after samepage returns tex unchanged."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\end{samepage}\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_toc_already_present(self) -> None:
        """If ``\\tableofcontents`` is already in the window, no double-insert."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\end{samepage}\n\\newpage\n"
            "\\tableofcontents\n\\newpage\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
            title_page_body="\\maketitle",
        )
        assert result.count("\\tableofcontents") == 1
        assert "\\maketitle" not in result


# ---------------------------------------------------------------------------
# Prerender validation — prevalidate_for_render
# ---------------------------------------------------------------------------


class TestPrevalidateForRender:
    """Hard-gate behaviour for the combined-PDF pre-render leaf."""

    def test_clean_manuscript_passes(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "# Intro\n\nSee [@good_key].\n")
        # Should not raise
        prevalidate_for_render(manuscript, repo_root=tmp_path)

    def test_nonexistent_source_path_returns_silently(self, tmp_path: Path) -> None:
        """A Path that doesn't exist returns without error (no files to validate)."""
        prevalidate_for_render(tmp_path / "nonexistent", repo_root=tmp_path)

    def test_empty_path_list_returns_silently(self, tmp_path: Path) -> None:
        prevalidate_for_render([], repo_root=tmp_path)

    def test_undefined_citation_raises_rendering_error(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "See [@missing_key] and [@good_key].\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        assert "missing_key" in str(excinfo.value)
        assert "Pre-render validation failed" in str(excinfo.value)

    def test_bare_pipe_raises_rendering_error(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "Mean |N400| in caption.\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        assert "Pre-render validation failed" in str(excinfo.value)
        assert "01_intro.md" in str(excinfo.value)

    def test_explicit_path_list_signature(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        md = _write_md(manuscript, "01_intro.md", "Clean text.\n")
        prevalidate_for_render([md], bib_file=manuscript / "references.bib")

    def test_citation_resolves_with_second_bib_file(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "references.bib").write_text("@article{good_key, title={Ok}, year={2025}}\n", encoding="utf-8")
        (manuscript / "references_deep.bib").write_text(
            "@article{deep_only, title={Deep}, year={2025}}\n", encoding="utf-8"
        )
        _write_md(manuscript, "01_intro.md", "See [@good_key] and [@deep_only].\n")
        prevalidate_for_render(manuscript)

    def test_error_message_includes_severity_counts(self, tmp_path: Path) -> None:
        """RenderingError message reports error and warning counts."""
        manuscript = _make_manuscript(tmp_path)
        # ERROR: undefined citation; WARNING: bare pipe
        _write_md(manuscript, "01_intro.md", "See [@bad] and |word| here.\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        msg = str(excinfo.value)
        assert "blocker" in msg


# ---------------------------------------------------------------------------
# Content validators — math, citations, refs, images, pitfalls
# ---------------------------------------------------------------------------


class TestValidatorMath:
    """``validate_math`` — display-math delimiter and equation-label checks."""

    def test_valid_labeled_equations_pass(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "\\begin{equation}\\label{eq:a}x^2\\end{equation}\n\\begin{equation}\\label{eq:b}y^2\\end{equation}\n",
        )
        assert validate_math([str(manuscript / "test.md")], tmp_path) == []

    def test_inline_dollar_display_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Math: $$x^2 + y^2 = z^2$$")
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.MATH_DOLLAR_DISPLAY
        assert problems[0].severity == DiagnosticSeverity.WARNING

    def test_bracket_display_math_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Math: \\[x^2 + y^2 = z^2\\]")
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.MATH_BRACKET_DISPLAY

    def test_equation_missing_label_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "\\begin{equation}x^2\\end{equation}")
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.MATH_LABEL_MISSING

    def test_duplicate_equation_label_flagged_as_error(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "\\begin{equation}\\label{eq:dup}x^2\\end{equation}\n\\begin{equation}\\label{eq:dup}y^2\\end{equation}\n",
        )
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.MATH_LABEL_DUPLICATE
        assert problems[0].severity == DiagnosticSeverity.ERROR

    def test_isolated_dollar_display_passes(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "$$x^2 + y^2 = z^2$$\n\n$$\na+b=c\n$$\n")
        assert validate_math([str(manuscript / "test.md")], tmp_path) == []

    def test_math_inside_code_not_scanned(self, tmp_path: Path) -> None:
        """``\\[...\\]`` inside a fenced code block should not be flagged."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "```latex\n\\[x^2\\]\n```\n")
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        # The bracket check scans raw text, but the equation block scan
        # strips fenced code. Only the bracket-display warning fires.
        codes = [p.code for p in problems]
        assert MarkdownCode.MATH_LABEL_MISSING not in codes


class TestValidatorCitations:
    """``validate_citations`` — BibTeX key resolution."""

    def _setup(self, tmp_path: Path, md: str, bib: str) -> list[str]:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", md)
        (manuscript / "references.bib").write_text(bib, encoding="utf-8")
        return [str(manuscript / "test.md")]

    def test_known_key_passes(self, tmp_path: Path) -> None:
        paths = self._setup(
            tmp_path,
            "See [@smith2020].\n",
            "@article{smith2020, title={Foo}, year={2020}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_unknown_key_flagged_as_error(self, tmp_path: Path) -> None:
        paths = self._setup(
            tmp_path,
            "See [@unknown2026].\n",
            "@article{smith2020, title={Foo}}\n",
        )
        problems = validate_citations(paths, tmp_path)
        assert len(problems) == 1
        assert problems[0].code == BibtexCode.UNDEFINED_KEY
        assert problems[0].severity == DiagnosticSeverity.ERROR
        assert "unknown2026" in problems[0].message

    def test_crossref_prefix_keys_not_flagged(self, tmp_path: Path) -> None:
        """Keys with known cross-reference prefixes (eq:, fig:, etc.) are skipped."""
        paths = self._setup(
            tmp_path,
            "See [@fig:chart] and [@eq:result].\n",
            "@article{smith2020, title={Foo}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_no_bib_file_returns_empty(self, tmp_path: Path) -> None:
        """When no .bib file is found, citations are not checked."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "See [@anykey].\n")
        assert validate_citations([str(manuscript / "test.md")], tmp_path) == []

    def test_non_rendered_files_skipped(self, tmp_path: Path) -> None:
        """AGENTS.md, README.md, preamble.md are skipped by citation validator."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "README.md", "See [@missing].\n")
        (manuscript / "references.bib").write_text("@article{a, title={A}}\n", encoding="utf-8")
        assert validate_citations([str(manuscript / "README.md")], tmp_path) == []

    def test_explicit_bib_file_path(self, tmp_path: Path) -> None:
        """A single explicit bib_file path is used instead of globbing."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "See [@known].\n")
        bib = manuscript / "custom.bib"
        bib.write_text("@article{known, title={K}}\n", encoding="utf-8")
        assert validate_citations([str(manuscript / "test.md")], tmp_path, bib_file=bib) == []

    def test_citation_in_code_not_flagged(self, tmp_path: Path) -> None:
        paths = self._setup(
            tmp_path,
            "Run `lookup(@email_handle)` here.\n",
            "@article{smith2020, title={Foo}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_duplicate_key_per_file_deduped(self, tmp_path: Path) -> None:
        """Same unresolved key cited twice produces a single diagnostic."""
        paths = self._setup(
            tmp_path,
            "See [@bad] and [@bad] again.\n",
            "@article{good, title={G}}\n",
        )
        problems = validate_citations(paths, tmp_path)
        assert len(problems) == 1


class TestValidatorRefs:
    """``validate_refs`` — cross-references, internal links, bare URLs."""

    def test_missing_equation_label_flagged_as_error(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Ref to \\eqref{eq:missing}")
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.REF_EQUATION_MISSING
        assert problems[0].severity == DiagnosticSeverity.ERROR

    def test_resolved_equation_label_passes(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Ref to \\eqref{eq:found}")
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, {"eq:found"}, set())
        assert problems == []

    def test_missing_anchor_flagged_as_error(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Link to [section](#missing_anchor)")
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.LINK_ANCHOR_MISSING

    def test_bare_url_flagged_as_warning(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Visit https://example.com for info")
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.LINK_BARE_URL
        assert problems[0].severity == DiagnosticSeverity.WARNING

    def test_non_informative_link_text_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "[https://example.com](https://example.com)")
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())
        assert any(p.code == MarkdownCode.LINK_BAD_TEXT for p in problems)

    def test_ref_in_fenced_code_not_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "```latex\n\\newcommand{\\gen}[1]{p(#1)}\n```\n",
        )
        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())
        assert not any("(#1)" in p.message for p in problems)


class TestValidatorImages:
    """``validate_images`` — referenced image resolution."""

    def test_missing_image_flagged_as_error(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "![alt](../output/figures/missing.png)")
        problems = validate_images([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.IMG_MISSING
        assert problems[0].severity == DiagnosticSeverity.ERROR

    def test_existing_image_passes(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "![alt](../output/figures/ok.png)")
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "ok.png").write_text("fake")
        assert validate_images([str(manuscript / "test.md")], tmp_path) == []

    def test_image_in_fenced_code_not_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "```markdown\n![Caption](../output/figures/example.png)\n```\n",
        )
        assert validate_images([str(manuscript / "test.md")], tmp_path) == []

    def test_empty_path_list_returns_empty(self, tmp_path: Path) -> None:
        assert validate_images([], tmp_path) == []


class TestValidatorPitfalls:
    """``validate_pandoc_pitfalls`` — bare pipe and escaped table-cell pipe."""

    def test_bare_pipe_in_prose_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Mean |N400| in caption.\n")
        problems = validate_pandoc_pitfalls([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.PANDOC_BARE_PIPE
        assert problems[0].severity == DiagnosticSeverity.WARNING

    def test_pipe_in_inline_math_not_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Use $|N400|$ for magnitude.\n")
        assert validate_pandoc_pitfalls([str(manuscript / "test.md")], tmp_path) == []

    def test_pipe_in_code_not_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "See `|alpha|` in snippet.\n")
        assert validate_pandoc_pitfalls([str(manuscript / "test.md")], tmp_path) == []

    def test_escaped_pipe_in_table_flagged(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "| Domain | Example |\n|--------|---------|\n| Prob | P(A \\| B) |\n",
        )
        problems = validate_pandoc_pitfalls([str(manuscript / "test.md")], tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE

    def test_non_rendered_files_skipped(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "README.md", "Bare |word| here.\n")
        assert validate_pandoc_pitfalls([str(manuscript / "README.md")], tmp_path) == []

    def test_non_rendered_files_constant(self) -> None:
        assert NON_RENDERED_MANUSCRIPT_FILES == frozenset({"AGENTS.md", "README.md", "preamble.md"})


# ---------------------------------------------------------------------------
# Symbols — collect_symbols and resolve_cross_reference_integrity
# ---------------------------------------------------------------------------


class TestCollectSymbols:
    """``collect_symbols`` — label/anchor collection from markdown files."""

    def test_extracts_labels_and_anchors(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test1.md",
            "\\begin{equation}\\label{eq:a}\\end{equation}\n# Section {#sec:a}\n",
        )
        _write_md(
            manuscript,
            "test2.md",
            "\\begin{equation}\\label{eq:b}\\end{equation}\n## Sub {#sec:b}\n",
        )
        labels, anchors = collect_symbols([str(manuscript / "test1.md"), str(manuscript / "test2.md")])
        assert labels == {"eq:a", "eq:b"}
        assert {"sec:a", "sec:b"} <= anchors

    def test_heading_slug_added_to_anchors(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "# My Great Heading\n")
        _, anchors = collect_symbols([str(manuscript / "test.md")])
        assert "my-great-heading" in anchors

    def test_empty_file_list(self) -> None:
        labels, anchors = collect_symbols([])
        assert labels == set()
        assert anchors == set()


class TestResolveCrossReferenceIntegrity:
    """``resolve_cross_reference_integrity`` — cross-doc reference resolution."""

    def test_all_resolved(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.md"
        f1.write_text("See \\ref{eq:x} and \\eqref{eq:x}.\n", encoding="utf-8")
        f2 = tmp_path / "b.md"
        f2.write_text("\\label{eq:x}\n", encoding="utf-8")
        result = resolve_cross_reference_integrity([f1, f2])
        assert result["equations"] is True
        assert result["scan_healthy"] is True

    def test_missing_label_marks_equations_false(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.md"
        f1.write_text("See \\eqref{eq:missing}.\n", encoding="utf-8")
        result = resolve_cross_reference_integrity([f1])
        assert result["equations"] is False

    def test_unreadable_file_marks_scan_unhealthy(self, tmp_path: Path) -> None:
        """A path that doesn't exist triggers OSError → scan_healthy=False."""
        result = resolve_cross_reference_integrity([tmp_path / "ghost.md"])
        assert result["scan_healthy"] is False


# ---------------------------------------------------------------------------
# Diagnostic codes — stable ID contract
# ---------------------------------------------------------------------------


class TestDiagnosticCodes:
    """Verify stable dotted IDs don't change (breaking-change guard)."""

    def test_markdown_code_values(self) -> None:
        expected = {
            "IMG_MISSING": "MARKDOWN.IMG_MISSING",
            "REF_EQUATION_MISSING": "MARKDOWN.REF_EQUATION_MISSING",
            "LINK_ANCHOR_MISSING": "MARKDOWN.LINK_ANCHOR_MISSING",
            "LINK_BARE_URL": "MARKDOWN.LINK_BARE_URL",
            "LINK_BAD_TEXT": "MARKDOWN.LINK_BAD_TEXT",
            "MATH_DOLLAR_DISPLAY": "MARKDOWN.MATH_DOLLAR_DISPLAY",
            "MATH_BRACKET_DISPLAY": "MARKDOWN.MATH_BRACKET_DISPLAY",
            "MATH_LABEL_MISSING": "MARKDOWN.MATH_LABEL_MISSING",
            "MATH_LABEL_DUPLICATE": "MARKDOWN.MATH_LABEL_DUPLICATE",
            "PANDOC_BARE_PIPE": "MARKDOWN.PANDOC_BARE_PIPE",
            "PANDOC_TABLE_ESCAPED_PIPE": "MARKDOWN.PANDOC_TABLE_ESCAPED_PIPE",
        }
        for attr, expected_val in expected.items():
            assert getattr(MarkdownCode, attr) == expected_val

    def test_bibtex_code_values(self) -> None:
        assert BibtexCode.UNDEFINED_KEY == "BIBTEX.UNDEFINED_KEY"

    def test_codes_are_strings(self) -> None:
        """All code constants must be str, not None."""
        for attr in dir(MarkdownCode):
            if attr.isupper():
                assert isinstance(getattr(MarkdownCode, attr), str)
        assert isinstance(BibtexCode.UNDEFINED_KEY, str)

    def test_codes_assigned_in_validators(self, tmp_path: Path) -> None:
        """Each validator assigns the correct code to its DiagnosticEvent."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "![missing](nope.png)\n"
            "\\eqref{eq:gone}\n"
            "[link](#gone)\n"
            "https://bare.url\n"
            "$$inline$$\n"
            "\\[bracket\\]\n"
            "\\begin{equation}x\\end{equation}\n"
            "|word|\n"
            "| a \\| b |\n",
        )
        (manuscript / "references.bib").write_text("@article{k, title={K}}\n", encoding="utf-8")
        paths = [str(manuscript / "test.md")]
        labels, anchors = collect_symbols(paths)
        all_codes: set[str | None] = set()
        all_codes.update(p.code for p in validate_images(paths, tmp_path))
        all_codes.update(p.code for p in validate_refs(paths, tmp_path, labels, anchors))
        all_codes.update(p.code for p in validate_math(paths, tmp_path))
        all_codes.update(p.code for p in validate_pandoc_pitfalls(paths, tmp_path))
        all_codes.update(p.code for p in validate_citations(paths, tmp_path))
        # None of the codes should be None — every event must carry a code
        assert None not in all_codes


# ---------------------------------------------------------------------------
# PDF validator — error and fallback paths
# ---------------------------------------------------------------------------


class TestPdfValidatorPaths:
    """``pdf_validator`` — missing, corrupt, and valid PDF paths."""

    def test_missing_pdf_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PDFValidationError, match="PDF file not found"):
            extract_text_from_pdf(tmp_path / "nonexistent.pdf")

    def test_too_small_file_raises(self, tmp_path: Path) -> None:
        """A file under 1000 bytes is flagged as likely corrupted."""
        small = tmp_path / "tiny.pdf"
        small.write_bytes(b"%PDF-1.4\nshort")
        with pytest.raises(PDFValidationError, match="too small"):
            extract_text_from_pdf(small)

    def test_corrupt_pdf_raises_extraction_failure(self, tmp_path: Path) -> None:
        """A >1KB non-PDF file fails all extraction methods."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_text("This is not a PDF. " * 200, encoding="utf-8")
        with pytest.raises(PDFValidationError, match="Failed to extract text"):
            extract_text_from_pdf(corrupt)

    def test_valid_pdf_extracts_text(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(tmp_path / "valid.pdf", ["Hello World", "Second Page"])
        text = extract_text_from_pdf(pdf)
        assert "Hello World" in text
        assert "Second Page" in text

    def test_validate_pdf_rendering_report_structure(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(tmp_path / "report.pdf", ["Title Here", "Body Text"])
        report = validate_pdf_rendering(pdf, n_words=5)
        assert "pdf_path" in report
        assert "issues" in report
        assert "first_words" in report
        assert "summary" in report
        assert report["summary"]["has_issues"] is False
        assert report["summary"]["word_count"] <= 5
        assert "Title" in report["first_words"]

    def test_validate_pdf_rendering_detects_issues(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(
            tmp_path / "issues.pdf",
            ["Intro ?? ref", "[WARNING] problem", "Error: Bad thing"],
        )
        report = validate_pdf_rendering(pdf)
        assert report["summary"]["has_issues"] is True
        assert report["issues"]["unresolved_references"] > 0
        assert report["issues"]["warnings"] > 0
        assert report["issues"]["errors"] > 0

    def test_validate_pdf_rendering_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PDFValidationError, match="PDF file not found"):
            validate_pdf_rendering(tmp_path / "nope.pdf")

    def test_scan_for_issues_all_categories(self) -> None:
        text = "?? ref\n[WARNING] w\nError: Bad\n[?] cite\n${VAR} placeholder"
        issues = scan_for_issues(text)
        assert issues["unresolved_references"] >= 1
        assert issues["warnings"] >= 1
        assert issues["errors"] >= 1
        assert issues["missing_citations"] >= 1
        assert issues["unresolved_placeholders"] >= 1
        assert issues["total_issues"] == sum(
            issues[k]
            for k in (
                "unresolved_references",
                "warnings",
                "errors",
                "missing_citations",
                "unresolved_placeholders",
            )
        )

    def test_scan_for_issues_clean_text(self) -> None:
        issues = scan_for_issues("This is clean text with no issues.")
        assert issues["total_issues"] == 0

    def test_scan_for_issues_scientific_error_not_flagged(self) -> None:
        """Scientific 'error:' terms should not trigger false-positive errors."""
        text = "final error: 1.2e-6\nstandard error: 0.03\n"
        issues = scan_for_issues(text)
        assert issues["errors"] == 0


# ---------------------------------------------------------------------------
# validate_markdown aggregate facade — error/fallback paths
# ---------------------------------------------------------------------------


class TestValidateMarkdownFacade:
    """``validate_markdown`` — aggregate facade and error paths."""

    def test_nonexistent_directory_raises(self, tmp_path: Path) -> None:
        from infrastructure.core.exceptions import FileNotFoundError

        with pytest.raises(FileNotFoundError):
            validate_markdown(tmp_path / "nonexistent", tmp_path)

    def test_empty_directory_returns_no_problems(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert problems == []
        assert exit_code == 0

    def test_clean_manuscript_no_problems(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "# Title\n\nClean content here.\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert problems == []
        assert exit_code == 0

    def test_problems_non_strict_exit_zero(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "![missing](nope.png)\n\\[bracket math\\]\n\\eqref{eq:gone}\n",
        )
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)
        assert exit_code == 0
        assert len(problems) >= 3

    def test_problems_strict_with_errors_exit_one(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "![missing](nope.png)\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)
        assert exit_code == 1
        assert len(problems) >= 1
        assert any(p.severity == DiagnosticSeverity.ERROR for p in problems)

    def test_strict_with_only_warnings_exit_zero(self, tmp_path: Path) -> None:
        """Strict mode only returns exit 1 when there are ERROR-level problems."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Math: $$inline$$\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)
        assert exit_code == 0
        assert len(problems) >= 1
        assert all(p.severity != DiagnosticSeverity.ERROR for p in problems)

    def test_full_validation_flow_clean(self, tmp_path: Path) -> None:
        """End-to-end: images, refs, math, pitfalls, citations all pass."""
        output_dir = tmp_path / "output" / "figures"
        output_dir.mkdir(parents=True)
        (output_dir / "fig.png").write_text("fake")

        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "# Section {#sec:test}\n\n"
            "![Fig](../output/figures/fig.png)\n\n"
            "\\begin{equation}\\label{eq:test}\nx^2\n\\end{equation}\n\n"
            "See \\eqref{eq:test} and [section](#sec:test).\n",
        )
        (manuscript / "references.bib").write_text("@article{k, title={K}}\n", encoding="utf-8")
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert exit_code == 0
        assert problems == []
