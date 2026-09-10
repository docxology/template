"""Markdown validation: Pandoc pitfalls, citation audit, and regex hardening."""

import os
import sys
from infrastructure.validation.content.markdown_validator import (
    validate_citations,
    validate_pandoc_pitfalls,
)
from infrastructure.validation.content.diagnostic_codes import (
    BibtexCode,
    MarkdownCode,
)
from infrastructure.core.logging import DiagnosticSeverity

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)


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

    def test_sibling_bib_files_unioned_by_default(self, tmp_path):
        # Two .bib files next to the markdown — split-citation projects
        # (e.g. references.bib + references_deep.bib) must validate as a union.
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("Curated [@smith2020]; deep [@deep2024].\n", encoding="utf-8")
        (manuscript / "references.bib").write_text("@article{smith2020, title={Foo}}\n", encoding="utf-8")
        (manuscript / "references_deep.bib").write_text("@misc{deep2024, title={Bar}}\n", encoding="utf-8")
        assert validate_citations([str(md)], tmp_path) == []

    def test_explicit_bib_list(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("[@a]\n[@b]\n", encoding="utf-8")
        bib_a = tmp_path / "a.bib"
        bib_a.write_text("@misc{a, title={A}}\n", encoding="utf-8")
        bib_b = tmp_path / "b.bib"
        bib_b.write_text("@misc{b, title={B}}\n", encoding="utf-8")
        assert validate_citations([str(md)], tmp_path, bib_file=[bib_a, bib_b]) == []

    def test_multibib_message_lists_all_filenames(self, tmp_path):
        # When multiple bibs are loaded and a key is missing, the error message
        # should list every filename so users know where to add the entry.
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        md = manuscript / "test.md"
        md.write_text("[@missing_everywhere]\n", encoding="utf-8")
        (manuscript / "references.bib").write_text("@article{smith2020, title={Foo}}\n", encoding="utf-8")
        (manuscript / "references_deep.bib").write_text("@misc{deep2024, title={Bar}}\n", encoding="utf-8")
        problems = validate_citations([str(md)], tmp_path)
        assert len(problems) == 1
        assert "references.bib" in problems[0].message
        assert "references_deep.bib" in problems[0].message


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
