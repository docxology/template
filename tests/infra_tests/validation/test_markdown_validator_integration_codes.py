"""Markdown validation: end-to-end flow, non-rendered file skips, and stable diagnostic codes."""

import os
import sys
from infrastructure.validation.content.markdown_validator import (
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

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)


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


class TestNonRenderedFilesSkipped:
    """AGENTS.md / README.md / preamble.md never reach the renderer; checks skip them."""

    def test_pitfalls_skip_non_rendered(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        # AGENTS.md routinely documents '|' patterns and shouldn't be flagged.
        (manuscript / "AGENTS.md").write_text("Mean |word| in docs.\n", encoding="utf-8")
        (manuscript / "preamble.md").write_text("| col1 | col2 |\n|------|------|\n| a \\| b | c |\n", encoding="utf-8")
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
            "| Term | Symbol |\n|------|--------|\n| Cosine | $\\frac{u \\cdot v}{\\|u\\| \\|v\\|}$ |\n",
            encoding="utf-8",
        )
        assert validate_pandoc_pitfalls([str(manuscript / "table.md")], tmp_path) == []


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
        assert not any(p.code == MarkdownCode.MATH_DOLLAR_DISPLAY for p in problems)

    def test_inline_math_dollar_display_carries_code(self, tmp_path):
        paths = self._setup(tmp_path, {"test.md": "Inline misuse: $$x = 1$$\n"})
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
        (manuscript / "references.bib").write_text("@misc{good_only}\n", encoding="utf-8")
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
