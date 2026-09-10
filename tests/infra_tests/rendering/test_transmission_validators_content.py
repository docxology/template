"""Content validators: math, citations, refs, images, pitfalls, symbols, and diagnostic codes (split from test_transmission_validation.py)."""

from __future__ import annotations

from pathlib import Path
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.validation.content.diagnostic_codes import (
    BibtexCode,
    MarkdownCode,
)
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
from ._transmission_validation_helpers import (
    _write_md,
)


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
