#!/usr/bin/env python3
"""Tests for infrastructure/markdown_validator.py"""

import os
import sys

import pytest

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

from infrastructure.validation.content.markdown_validator import (
    collect_symbols,
    find_manuscript_directory,
    find_markdown_files,
    validate_citations,
    validate_images,
    validate_markdown,
    validate_math,
    validate_pandoc_pitfalls,
    validate_refs,
)
from infrastructure.validation.content.diagnostic_codes import (
    BibtexCode,
    MarkdownCode,
)
from infrastructure.core.logging import DiagnosticSeverity


class TestFindMarkdownFiles:
    """Test find_markdown_files function."""

    def test_finds_and_sorts_markdown_files(self, tmp_path):
        """Test find_markdown_files finds and sorts markdown files."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "02_second.md").write_text("content")
        (manuscript / "01_first.md").write_text("content")
        (manuscript / "not_md.txt").write_text("content")

        files = find_markdown_files(manuscript)

        assert len(files) == 2
        assert "01_first.md" in files[0]
        assert "02_second.md" in files[1]

    def test_nonexistent_directory_raises(self, tmp_path):
        """Test find_markdown_files raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            find_markdown_files(tmp_path / "nonexistent")

    def test_file_instead_of_directory_raises(self, tmp_path):
        """Test find_markdown_files raises when given a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        with pytest.raises(NotADirectoryError):
            find_markdown_files(test_file)

    def test_empty_directory(self, tmp_path):
        """Test find_markdown_files with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        files = find_markdown_files(manuscript)

        assert files == []


class TestCollectSymbols:
    """Test collect_symbols function."""

    def test_extracts_labels_and_anchors(self, tmp_path):
        """Test collect_symbols extracts labels and anchors."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test1.md").write_text(
            "\\begin{equation}\\label{eq:test1}\\end{equation}\n# Section {#sec:test1}\n"
        )
        (manuscript / "test2.md").write_text(
            "\\begin{equation}\\label{eq:test2}\\end{equation}\n## Subsection {#subsec:test2}\n"
        )

        labels, anchors = collect_symbols(
            [str(manuscript / "test1.md"), str(manuscript / "test2.md")]
        )

        assert labels == {"eq:test1", "eq:test2"}
        assert anchors == {"sec:test1", "subsec:test2"}

    def test_empty_file_list(self):
        """Test collect_symbols with empty file list."""
        labels, anchors = collect_symbols([])

        assert labels == set()
        assert anchors == set()


class TestValidateImages:
    """Test validate_images function."""

    def test_detects_missing_image(self, tmp_path):
        """Test validate_images detects missing images."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![alt text](../output/figures/missing.png)")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Missing referenced image: '../output/figures/missing.png'" in problems[0].message

    def test_validates_existing_image(self, tmp_path):
        """Test validate_images doesn't flag existing images."""
        # Create test markdown file and image
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![alt text](../output/figures/existing.png)")
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "existing.png").write_text("fake image")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 0

    def test_absolute_path(self, tmp_path):
        """Test validate_images with absolute image paths."""
        # Create test markdown file with absolute path
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        abs_image_path = str(tmp_path / "absolute_image.png")
        (manuscript / "test.md").write_text(f"![alt text]({abs_image_path})")

        # Don't create the image file so it will be missing
        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Missing referenced image" in problems[0].message

    def test_relative_path_not_absolute_after_normpath(self, tmp_path, monkeypatch):
        """Test validate_images with relative path that stays relative after normpath.

        This covers line 94 where abs_path is joined with repo_root when not absolute.
        """
        # Create a manuscript directory with an image reference
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(parents=True)

        (manuscript / "test.md").write_text("![alt text](../output/figures/test.png)")

        # Change to tmp_path so we can use relative paths
        monkeypatch.chdir(tmp_path)

        # Pass RELATIVE path to markdown file - this triggers line 94
        # because dirname("manuscript/test.md") = "manuscript"
        # and join("manuscript", "../output/figures/test.png") = "output/figures/test.png" (relative!)
        relative_md_path = "manuscript/test.md"

        problems = validate_images([relative_md_path], tmp_path)

        # Should report missing image since we didn't create it
        assert len(problems) == 1
        assert "Missing referenced image" in problems[0].message

    def test_relative_path_exists_after_repo_root_join(self, tmp_path):
        """Test validate_images with relative path that exists when joined with repo_root.

        This covers line 94 with a file that actually exists.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        # Create the image in a relative location from manuscript
        figures_dir = manuscript / "figures"
        figures_dir.mkdir()
        (figures_dir / "local_image.png").write_text("fake image")

        # Reference with simple relative path
        (manuscript / "test.md").write_text("![alt text](figures/local_image.png)")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        # Image exists, should have no problems
        assert len(problems) == 0


class TestValidateRefs:
    """Test validate_refs function."""

    def test_detects_missing_equation_label(self, tmp_path):
        """Test validate_refs detects missing equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Reference to \\eqref{eq:missing}")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Missing equation label for \\eqref{eq:missing}" in problems[0].message

    def test_detects_missing_anchor(self, tmp_path):
        """Test validate_refs detects missing anchors."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Link to [section](#missing_anchor)")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Missing anchor/label for internal link (#missing_anchor)" in problems[0].message

    def test_ignores_markdown_link_pattern_inside_fenced_code(self, tmp_path):
        """LaTeX like p(#1) in ``` blocks must not be reported as (#1) internal links."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "```latex\n" r"\newcommand{\gen}[1]{p(#1)}" "\n```\n"
        )

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert not any("(#1)" in p.message for p in problems)

    def test_detects_bare_url(self, tmp_path):
        """Test validate_refs detects bare URLs."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Visit https://example.com for more info")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Bare URL found" in problems[0].message

    def test_detects_non_informative_link(self, tmp_path):
        """Test validate_refs detects non-informative link text."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("[https://example.com](https://example.com)")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        # The regex patterns can detect multiple issues with the same text
        assert len(problems) >= 1
        assert any("Non-informative link text" in p.message for p in problems)


class TestValidateMath:
    """Test validate_math function."""

    def test_detects_dollar_math(self, tmp_path):
        """Test validate_math detects dollar math notation."""
        # Create test markdown file with $$ math
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Math: $$x^2 + y^2 = z^2$$")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Use equation environment instead of $$" in problems[0].message

    def test_detects_bracket_math(self, tmp_path):
        """Test validate_math detects bracket math notation."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Math: \\[x^2 + y^2 = z^2\\]")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Use equation environment instead of \\[ \\]" in problems[0].message

    def test_detects_missing_label(self, tmp_path):
        """Test validate_math detects equations without labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(r"\begin{equation}x^2 + y^2 = z^2\end{equation}")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Equation missing \\label{...}" in problems[0].message

    def test_detects_duplicate_label(self, tmp_path):
        """Test validate_math detects duplicate equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"\begin{equation}\label{eq:duplicate}x^2\end{equation}" + "\n"
            r"\begin{equation}\label{eq:duplicate}y^2\end{equation}"
        )

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Duplicate equation label '{eq:duplicate}'" in problems[0].message

    def test_accepts_valid_equations(self, tmp_path):
        """Test validate_math accepts valid labeled equations."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "\\begin{equation}\\label{eq:valid1}x^2 + y^2 = z^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:valid2}a^2 + b^2 = c^2\\end{equation}"
        )

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 0


class TestValidateMarkdown:
    """Test validate_markdown function."""

    def test_no_problems_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 when no problems found."""
        # Create test markdown directory with valid content
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("# Test\n\nNo problems here.")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)

        assert exit_code == 0
        assert problems == []

    def test_problems_non_strict_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 with problems in non-strict mode."""
        # Create test markdown directory with problems
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("\\begin{equation}x^2\\end{equation}")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)

        assert exit_code == 0
        assert len(problems) > 0

    def test_problems_strict_returns_one(self, tmp_path):
        """Test validate_markdown returns 1 with problems in strict mode."""
        # Create test markdown directory with an ERROR-level problem
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![Missing image](../output/figures/missing.png)")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)

        assert exit_code == 1
        assert len(problems) > 0

    def test_nonexistent_directory_raises(self, tmp_path):
        """Test validate_markdown raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            validate_markdown(tmp_path / "nonexistent", tmp_path)

    def test_empty_directory_returns_zero(self, tmp_path):
        """Test validate_markdown with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        problems, exit_code = validate_markdown(manuscript, tmp_path)

        assert exit_code == 0
        assert problems == []


class TestFindManuscriptDirectory:
    """Test find_manuscript_directory function."""

    def test_finds_project_manuscript(self, tmp_path):
        """Test find_manuscript_directory finds projects/project/manuscript."""
        manuscript = tmp_path / "projects" / "project" / "manuscript"
        manuscript.mkdir(parents=True)

        result = find_manuscript_directory(tmp_path, "project")

        assert result == manuscript

    def test_raises_when_not_found(self, tmp_path):
        """Test find_manuscript_directory raises when not found."""
        with pytest.raises(FileNotFoundError):
            find_manuscript_directory(tmp_path, "project")


class TestIntegration:
    """Integration tests for the complete validation flow."""

    def test_full_validation_flow(self, tmp_path):
        """Test complete validation with images, refs, and math."""
        # Create test project structure
        output_dir = tmp_path / "output" / "figures"
        output_dir.mkdir(parents=True)
        (output_dir / "test_figure.png").write_text("fake image")

        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"""
# Test Section {#sec:test}

Valid content with image:

![Test Figure](../output/figures/test_figure.png)

Valid equation:

\begin{equation}\label{eq:test}
x^2 + y^2 = z^2
\end{equation}

Valid reference: \eqref{eq:test}

Valid link: [See section](#sec:test)
"""
        )

        problems, exit_code = validate_markdown(manuscript, tmp_path)

        assert exit_code == 0
        assert problems == []

    def test_multiple_problems_detected(self, tmp_path):
        """Test detection of multiple types of problems."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"""
# Test Section

Missing image: ![Missing](../output/figures/missing.png)

Dollar math: $$x^2$$

Unlabeled equation: \begin{equation}x^2\end{equation}

Missing ref: \eqref{eq:missing}

Bare URL: https://example.com
"""
        )

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)

        assert exit_code == 0  # Non-strict mode
        assert len(problems) >= 5  # At least 5 different types of problems


class TestPandocPitfalls:
    """Tests for ``validate_pandoc_pitfalls`` — patterns Pandoc converts to ``\\mid``."""

    def _write(self, tmp_path, name, content):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(exist_ok=True)
        (manuscript / name).write_text(content, encoding="utf-8")
        return [str(manuscript / name)]

    def test_bare_pipe_in_prose_flagged(self, tmp_path):
        paths = self._write(tmp_path, "test.md", "Mean |N400| in caption text.\n")
        problems = validate_pandoc_pitfalls(paths, tmp_path)
        assert len(problems) == 1
        assert problems[0].category == "MARKDOWN_PANDOC_MID"
        assert problems[0].code == MarkdownCode.PANDOC_BARE_PIPE
        assert problems[0].severity == DiagnosticSeverity.WARNING
        assert "N400" in problems[0].message

    def test_pipe_in_inline_math_not_flagged(self, tmp_path):
        paths = self._write(tmp_path, "test.md", "Use $|N400|$ for the magnitude.\n")
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_pipe_in_code_not_flagged(self, tmp_path):
        paths = self._write(tmp_path, "test.md", "See `|alpha|` in the snippet.\n")
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_pipe_in_fenced_code_not_flagged(self, tmp_path):
        paths = self._write(
            tmp_path,
            "test.md",
            "```python\nresult = |word|  # not flagged\n```\n",
        )
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_escaped_pipe_in_table_cell_flagged(self, tmp_path):
        paths = self._write(
            tmp_path,
            "test.md",
            "| Domain | Example |\n|--------|---------|\n| Prob | P(A \\| B) |\n",
        )
        problems = validate_pandoc_pitfalls(paths, tmp_path)
        assert len(problems) == 1
        assert problems[0].code == MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE
        assert "table cell" in problems[0].message.lower()

    def test_escaped_pipe_outside_table_not_flagged(self, tmp_path):
        # `\|` outside a table row is a normal escape and Pandoc renders it
        # as a literal pipe, not \mid.
        paths = self._write(tmp_path, "test.md", "Plain text with \\| escape.\n")
        assert validate_pandoc_pitfalls(paths, tmp_path) == []


class TestCitationAudit:
    """Tests for ``validate_citations`` — pre-render BibTeX-key check."""

    def _setup(self, tmp_path, md_content, bib_content):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(exist_ok=True)
        (manuscript / "test.md").write_text(md_content, encoding="utf-8")
        (manuscript / "references.bib").write_text(bib_content, encoding="utf-8")
        return [str(manuscript / "test.md")]

    def test_known_key_passes(self, tmp_path):
        paths = self._setup(
            tmp_path,
            "See [@smith2020] for details.\n",
            "@article{smith2020, title={Foo}, author={Smith}, year={2020}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_unknown_key_flagged(self, tmp_path):
        paths = self._setup(
            tmp_path,
            "See [@unknown2026] for details.\n",
            "@article{smith2020, title={Foo}, author={Smith}, year={2020}}\n",
        )
        problems = validate_citations(paths, tmp_path)
        assert len(problems) == 1
        assert problems[0].category == "MARKDOWN_CITATION"
        assert problems[0].code == BibtexCode.UNDEFINED_KEY
        assert problems[0].severity == DiagnosticSeverity.ERROR
        assert "unknown2026" in problems[0].message

    def test_citation_in_code_not_flagged(self, tmp_path):
        paths = self._setup(
            tmp_path,
            "Run `result = lookup(@email_handle)` here.\n",
            "@article{smith2020, title={Foo}, author={Smith}, year={2020}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_citation_with_dash_underscore_handled(self, tmp_path):
        paths = self._setup(
            tmp_path,
            "Cite [@a-b_c2020].\n",
            "@article{a-b_c2020, title={Foo}}\n",
        )
        assert validate_citations(paths, tmp_path) == []

    def test_dedup_per_file(self, tmp_path):
        # Same unresolved key cited twice should produce a single warning
        paths = self._setup(
            tmp_path,
            "First [@missing2020]; again [@missing2020].\n",
            "@article{other, title={X}}\n",
        )
        assert len(validate_citations(paths, tmp_path)) == 1

    def test_no_bib_file_no_problems(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("[@anything]\n", encoding="utf-8")
        assert validate_citations([str(md)], tmp_path) == []

    def test_explicit_bib_path(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("[@known]\n", encoding="utf-8")
        bib = tmp_path / "external.bib"
        bib.write_text("@misc{known, title={X}}\n", encoding="utf-8")
        assert validate_citations([str(md)], tmp_path, bib_file=bib) == []


class TestNonRenderedFilesSkipped:
    """AGENTS.md / README.md / preamble.md never reach the renderer; checks skip them."""

    def test_pitfalls_skip_non_rendered(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        # AGENTS.md routinely documents '|' patterns and shouldn't be flagged.
        (manuscript / "AGENTS.md").write_text("Mean |word| in docs.\n", encoding="utf-8")
        (manuscript / "preamble.md").write_text(
            "| col1 | col2 |\n|------|------|\n| a \\| b | c |\n", encoding="utf-8"
        )
        (manuscript / "README.md").write_text("Cite [@anything] in docs.\n", encoding="utf-8")
        paths = [
            str(manuscript / "AGENTS.md"),
            str(manuscript / "preamble.md"),
            str(manuscript / "README.md"),
        ]
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_citations_skip_non_rendered(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "AGENTS.md").write_text("[@undef_key]\n", encoding="utf-8")
        (manuscript / "references.bib").write_text("@misc{x}\n", encoding="utf-8")
        assert validate_citations([str(manuscript / "AGENTS.md")], tmp_path) == []

    def test_norm_operator_in_table_math_not_flagged(self, tmp_path):
        # ``\|`` inside ``$...$`` is the norm operator, NOT a Pandoc-converted pipe.
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "table.md").write_text(
            "| Term | Symbol |\n|------|--------|\n"
            "| Cosine | $\\frac{u \\cdot v}{\\|u\\| \\|v\\|}$ |\n",
            encoding="utf-8",
        )
        assert validate_pandoc_pitfalls([str(manuscript / "table.md")], tmp_path) == []


class TestRegexHardening:
    """Tests for the broadened regex coverage (numeric pipes, code variants, BibTeX)."""

    def _write(self, tmp_path, name, content):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(exist_ok=True)
        path = manuscript / name
        path.write_text(content, encoding="utf-8")
        return [str(path)]

    def test_numeric_bare_pipe_flagged(self, tmp_path):
        paths = self._write(tmp_path, "test.md", "Sample size |123| in caption.\n")
        problems = validate_pandoc_pitfalls(paths, tmp_path)
        assert len(problems) == 1
        assert "123" in problems[0].message

    def test_indented_code_block_not_flagged(self, tmp_path):
        paths = self._write(
            tmp_path,
            "test.md",
            "Intro paragraph.\n\n    sample = |word|  # 4-space indented code\n    more = |x|\n\nBack to prose.\n",
        )
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_tilde_fenced_code_not_flagged(self, tmp_path):
        paths = self._write(
            tmp_path,
            "test.md",
            "Intro.\n\n~~~python\nresult = |word|  # tilde fence\n~~~\n\nOutro.\n",
        )
        assert validate_pandoc_pitfalls(paths, tmp_path) == []

    def test_bibtex_entry_without_trailing_comma_recognised(self, tmp_path):
        # Field-less ``@misc{key}`` is legal BibTeX; the original regex missed it.
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("Cite [@field_less].\n", encoding="utf-8")
        bib = manuscript / "references.bib"
        bib.write_text("@misc{field_less}\n", encoding="utf-8")
        assert validate_citations([str(md)], tmp_path) == []


class TestDiagnosticCodes:
    """Every emission site in markdown_validator carries the matching stable code."""

    def _setup(self, tmp_path, files):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(exist_ok=True)
        paths = []
        for name, content in files.items():
            (manuscript / name).write_text(content, encoding="utf-8")
            paths.append(str(manuscript / name))
        return paths

    def test_image_missing_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "![alt](../figures/missing.png)\n"},
        )
        problems = validate_images(paths, tmp_path)
        assert problems
        assert all(p.code == MarkdownCode.IMG_MISSING for p in problems)

    def test_eqref_missing_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "See \\eqref{eq:undefined}.\n"},
        )
        problems = validate_refs(paths, tmp_path, labels=set(), anchors=set())
        eq_problems = [p for p in problems if p.code == MarkdownCode.REF_EQUATION_MISSING]
        assert len(eq_problems) == 1

    def test_link_anchor_missing_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "Jump to [section](#undefined-anchor).\n"},
        )
        problems = validate_refs(paths, tmp_path, labels=set(), anchors=set())
        link_problems = [p for p in problems if p.code == MarkdownCode.LINK_ANCHOR_MISSING]
        assert link_problems

    def test_link_bare_url_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "Visit https://example.com directly.\n"},
        )
        problems = validate_refs(paths, tmp_path, labels=set(), anchors=set())
        bare = [p for p in problems if p.code == MarkdownCode.LINK_BARE_URL]
        assert bare

    def test_link_bad_text_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "Click [https://example.com](https://example.com) here.\n"},
        )
        problems = validate_refs(paths, tmp_path, labels=set(), anchors=set())
        bad = [p for p in problems if p.code == MarkdownCode.LINK_BAD_TEXT]
        assert bad

    def test_math_dollar_display_carries_code(self, tmp_path):
        paths = self._setup(tmp_path, {"test.md": "$$x = 1$$\n"})
        problems = validate_math(paths, tmp_path)
        assert any(p.code == MarkdownCode.MATH_DOLLAR_DISPLAY for p in problems)

    def test_math_bracket_display_carries_code(self, tmp_path):
        paths = self._setup(tmp_path, {"test.md": "\\[ x = 1 \\]\n"})
        problems = validate_math(paths, tmp_path)
        assert any(p.code == MarkdownCode.MATH_BRACKET_DISPLAY for p in problems)

    def test_math_label_missing_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "\\begin{equation}\nx = 1\n\\end{equation}\n"},
        )
        problems = validate_math(paths, tmp_path)
        assert any(p.code == MarkdownCode.MATH_LABEL_MISSING for p in problems)

    def test_math_label_duplicate_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {
                "test.md": (
                    "\\begin{equation}\\label{eq:dup}\nx = 1\n\\end{equation}\n"
                    "\\begin{equation}\\label{eq:dup}\ny = 2\n\\end{equation}\n"
                )
            },
        )
        problems = validate_math(paths, tmp_path)
        dup = [p for p in problems if p.code == MarkdownCode.MATH_LABEL_DUPLICATE]
        assert dup

    def test_pandoc_bare_pipe_carries_code(self, tmp_path):
        paths = self._setup(tmp_path, {"test.md": "Mean |word| in caption.\n"})
        problems = validate_pandoc_pitfalls(paths, tmp_path)
        assert problems[0].code == MarkdownCode.PANDOC_BARE_PIPE

    def test_pandoc_table_escaped_pipe_carries_code(self, tmp_path):
        paths = self._setup(
            tmp_path,
            {"test.md": "| A | B |\n|---|---|\n| P(A \\| B) | x |\n"},
        )
        problems = validate_pandoc_pitfalls(paths, tmp_path)
        assert problems[0].code == MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE

    def test_undefined_citation_carries_code(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(exist_ok=True)
        (manuscript / "test.md").write_text("Cite [@nope].\n", encoding="utf-8")
        (manuscript / "references.bib").write_text(
            "@misc{good_only}\n", encoding="utf-8"
        )
        problems = validate_citations([str(manuscript / "test.md")], tmp_path)
        assert problems[0].code == BibtexCode.UNDEFINED_KEY

    def test_all_emitted_codes_are_unique_constants(self):
        """Sanity: the registry exposes 12 unique strings (the audit count)."""
        all_codes = {
            MarkdownCode.IMG_MISSING,
            MarkdownCode.REF_EQUATION_MISSING,
            MarkdownCode.LINK_ANCHOR_MISSING,
            MarkdownCode.LINK_BARE_URL,
            MarkdownCode.LINK_BAD_TEXT,
            MarkdownCode.MATH_DOLLAR_DISPLAY,
            MarkdownCode.MATH_BRACKET_DISPLAY,
            MarkdownCode.MATH_LABEL_MISSING,
            MarkdownCode.MATH_LABEL_DUPLICATE,
            MarkdownCode.PANDOC_BARE_PIPE,
            MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE,
            BibtexCode.UNDEFINED_KEY,
        }
        assert len(all_codes) == 12
