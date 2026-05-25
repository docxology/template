"""Tests for infrastructure.rendering.manuscript_injection."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.manuscript_injection import (
    EXCLUDED_DOC_FILENAMES,
    substitute_manuscript_text,
    write_resolved_manuscript_tree,
)


class TestSubstituteManuscriptText:
    def test_simple_substitution(self):
        text = "Found {{RESULT_N}} papers in {{YEAR_MIN}}–{{YEAR_MAX}}."
        resolved, unresolved = substitute_manuscript_text(
            text, {"RESULT_N": "42", "YEAR_MIN": "2010", "YEAR_MAX": "2024"}
        )
        assert resolved == "Found 42 papers in 2010–2024."
        assert unresolved == []

    def test_unresolved_token_left_unchanged(self):
        resolved, unresolved = substitute_manuscript_text("{{MISSING}} stays.", {})
        assert "{{MISSING}}" in resolved
        assert "MISSING" in unresolved

    def test_multiple_unresolved_reported(self):
        _, unresolved = substitute_manuscript_text("{{A}} and {{B}}", {})
        assert set(unresolved) == {"A", "B"}

    def test_mermaid_label_not_substituted(self):
        # {{For each keyword}} has spaces and mixed case — must never match.
        text = "CFG --> KW{{For each keyword}}"
        resolved, unresolved = substitute_manuscript_text(text, {})
        assert resolved == text
        assert unresolved == []

    def test_glob_pattern_in_docs_not_substituted(self):
        # {{CONFIG_*}} contains '*' — invalid token, must not match.
        text = "Use ``{{CONFIG_*}}`` and ``{{RESULT_*}}`` tokens."
        resolved, unresolved = substitute_manuscript_text(text, {"CONFIG_": "x"})
        assert "{{CONFIG_*}}" in resolved
        assert unresolved == []

    def test_no_tokens_returns_unchanged(self):
        text = "Plain text with no curly braces."
        resolved, unresolved = substitute_manuscript_text(text, {"KEY": "val"})
        assert resolved == text
        assert unresolved == []

    def test_multiple_occurrences_of_same_token(self):
        resolved, _ = substitute_manuscript_text("{{X}} then {{X}} again.", {"X": "yes"})
        assert resolved == "yes then yes again."

    def test_partial_single_brace_not_matched(self):
        text = "{single} and {{}}"
        resolved, unresolved = substitute_manuscript_text(text, {})
        assert resolved == text
        assert unresolved == []

    def test_empty_variables_leaves_all_tokens(self):
        resolved, unresolved = substitute_manuscript_text("{{A}} {{B}} {{C}}", {})
        assert "{{A}}" in resolved
        assert set(unresolved) == {"A", "B", "C"}

    def test_value_with_special_chars_not_double_processed(self):
        # Value itself contains {{...}} — must not be re-substituted.
        resolved, _ = substitute_manuscript_text("{{KEY}}", {"KEY": "{{OTHER}}"})
        assert resolved == "{{OTHER}}"


class TestWriteResolvedManuscriptTree:
    def test_substitution_written_to_output(self, tmp_path: Path):
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_intro.md").write_text("Papers: {{TOTAL}}.\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {"TOTAL": "7"})

        out = (root / "output" / "manuscript" / "00_intro.md").read_text(encoding="utf-8")
        assert "{{TOTAL}}" not in out
        assert "Papers: 7." in out

    def test_config_yaml_copied_verbatim(self, tmp_path: Path):
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_a.md").write_text("x\n", encoding="utf-8")
        (ms / "config.yaml").write_text("paper:\n  title: T\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {})

        out_yaml = root / "output" / "manuscript" / "config.yaml"
        assert out_yaml.exists()
        assert "title: T" in out_yaml.read_text(encoding="utf-8")

    def test_preamble_md_copied_verbatim(self, tmp_path: Path):
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_a.md").write_text("x\n", encoding="utf-8")
        (ms / "preamble.md").write_text("```latex\n\\usepackage{booktabs}\n```\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {})

        out_preamble = root / "output" / "manuscript" / "preamble.md"
        assert out_preamble.exists()
        assert "\\usepackage{booktabs}" in out_preamble.read_text(encoding="utf-8")

    def test_bib_files_copied(self, tmp_path: Path):
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_a.md").write_text("x\n", encoding="utf-8")
        (ms / "refs.bib").write_text("@article{x,\n title={T}\n}\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {})

        assert (root / "output" / "manuscript" / "refs.bib").exists()

    def test_excluded_doc_files_not_copied(self, tmp_path: Path):
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_main.md").write_text("Main.\n", encoding="utf-8")
        for name in EXCLUDED_DOC_FILENAMES:
            (ms / name).write_text(f"# {name}\n\nExample: {{{{TOKEN}}}}.\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {"TOKEN": "real"})

        out_dir = root / "output" / "manuscript"
        assert (out_dir / "00_main.md").exists()
        for name in EXCLUDED_DOC_FILENAMES:
            assert not (out_dir / name).exists(), f"{name} should not be in output"

    def test_returns_output_manuscript_path(self, tmp_path: Path):
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        (root / "manuscript" / "x.md").write_text("x\n", encoding="utf-8")

        result = write_resolved_manuscript_tree(root, {})
        assert result == root / "output" / "manuscript"

    def test_missing_config_yaml_is_not_an_error(self, tmp_path: Path):
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        (root / "manuscript" / "x.md").write_text("x\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {})
        assert not (root / "output" / "manuscript" / "config.yaml").exists()

    def test_unresolved_token_preserved_in_output_file(self, tmp_path: Path):
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        (root / "manuscript" / "x.md").write_text("{{MISSING}}\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {})

        out = (root / "output" / "manuscript" / "x.md").read_text(encoding="utf-8")
        assert "{{MISSING}}" in out

    def test_idempotent_on_second_call(self, tmp_path: Path):
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        (root / "manuscript" / "00_a.md").write_text("N={{N}}\n", encoding="utf-8")

        write_resolved_manuscript_tree(root, {"N": "1"})
        write_resolved_manuscript_tree(root, {"N": "2"})

        out = (root / "output" / "manuscript" / "00_a.md").read_text(encoding="utf-8")
        assert out == "N=2\n"

    def test_doc_file_token_examples_untouched_in_source(self, tmp_path: Path):
        """Excluding doc files means their literal tokens are never resolved,
        so the source files remain unchanged documentation."""
        root = tmp_path / "proj"
        ms = root / "manuscript"
        ms.mkdir(parents=True)
        (ms / "00_main.md").write_text("val={{KEY}}\n", encoding="utf-8")
        agents_src = "| `{{KEY}}` | description |\n"
        (ms / "AGENTS.md").write_text(agents_src, encoding="utf-8")

        write_resolved_manuscript_tree(root, {"KEY": "42"})

        # AGENTS.md must not appear in output at all
        assert not (root / "output" / "manuscript" / "AGENTS.md").exists()
        # Source AGENTS.md is untouched
        assert (ms / "AGENTS.md").read_text(encoding="utf-8") == agents_src
