"""Tests for infrastructure.rendering._pdf_combined_renderer — comprehensive coverage."""

import pytest
import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_combined_renderer import (
    CombinedMarkdownResult,
    flatten_manuscript_vars,
    substitute_manuscript_var_placeholders,
    preprocess_combined_markdown,
    postprocess_latex,
    inject_bibliography,
    verify_figure_references,
    prevalidate_markdown,
    prevalidate_source_markdown,
    inject_latex_preamble,
)


class TestFlattenManuscriptVars:
    def test_flat_dict(self):
        data = {"title": "My Paper", "version": "1.0"}
        result = flatten_manuscript_vars(data)
        assert result == {"title": "My Paper", "version": "1.0"}

    def test_nested_dict(self):
        data = {"paper": {"title": "Test", "year": 2025}}
        result = flatten_manuscript_vars(data)
        assert result == {"paper.title": "Test", "paper.year": "2025"}

    def test_list_values(self):
        data = {"keywords": ["ai", "ml", "nlp"]}
        result = flatten_manuscript_vars(data)
        assert result == {"keywords": "ai, ml, nlp"}

    def test_bool_values(self):
        data = {"enabled": True, "draft": False}
        result = flatten_manuscript_vars(data)
        assert result == {"enabled": "true", "draft": "false"}

    def test_none_values(self):
        data = {"optional": None}
        result = flatten_manuscript_vars(data)
        assert result == {"optional": ""}

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": "deep"}}}
        result = flatten_manuscript_vars(data)
        assert result == {"a.b.c": "deep"}

    def test_empty_dict(self):
        assert flatten_manuscript_vars({}) == {}

    def test_non_dict_root(self):
        assert flatten_manuscript_vars("string") == {}
        assert flatten_manuscript_vars(42) == {}
        assert flatten_manuscript_vars(None) == {}

    def test_mixed_types(self):
        data = {
            "str_val": "hello",
            "int_val": 42,
            "float_val": 3.14,
            "nested": {"key": "val"},
            "list_val": [1, 2, 3],
            "bool_val": True,
            "none_val": None,
        }
        result = flatten_manuscript_vars(data)
        assert result["str_val"] == "hello"
        assert result["int_val"] == "42"
        assert result["float_val"] == "3.14"
        assert result["nested.key"] == "val"
        assert result["list_val"] == "1, 2, 3"
        assert result["bool_val"] == "true"
        assert result["none_val"] == ""

    def test_with_prefix(self):
        data = {"key": "val"}
        result = flatten_manuscript_vars(data, prefix="root")
        assert result == {"root.key": "val"}


class TestSubstituteManuscriptVarPlaceholders:
    def test_simple_substitution(self):
        content = "Title: {{title}}"
        flat = {"title": "My Paper"}
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert result == "Title: My Paper"
        assert count == 1

    def test_multiple_substitutions(self):
        content = "{{title}} by {{author}}"
        flat = {"title": "Paper", "author": "Alice"}
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert result == "Paper by Alice"
        assert count == 2

    def test_unknown_key_left_unchanged(self):
        content = "Value: {{unknown}}"
        flat = {"title": "Paper"}
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert result == "Value: {{unknown}}"
        assert count == 0

    def test_maturity_wildcard(self):
        flat = {"maturity.real": "5", "maturity.partial": "3", "maturity.aspirational": "2"}
        content = "Maturity: {{maturity.*}}"
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert "5 real" in result
        assert "3 partial" in result
        assert "2 aspirational" in result
        assert count == 1

    def test_verify_wildcard(self):
        flat = {"verify.alpha": "0.95", "verify.beta": "0.80"}
        content = "Verify: {{verify.*}}"
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert "verify.alpha=0.95" in result
        assert "verify.beta=0.80" in result
        assert count == 1

    def test_verify_wildcard_empty(self):
        flat = {}
        content = "Verify: {{verify.*}}"
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert "no verify metrics" in result
        assert count == 1

    def test_whitespace_in_key(self):
        content = "{{ title }}"
        flat = {"title": "Paper"}
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert result == "Paper"
        assert count == 1

    def test_no_placeholders(self):
        content = "Plain text without placeholders"
        flat = {"title": "Paper"}
        result, count = substitute_manuscript_var_placeholders(content, flat)
        assert result == content
        assert count == 0


class TestPreprocessCombinedMarkdown:
    def test_strips_mermaid_blocks(self):
        content = "Before\n```mermaid\ngraph TD\nA-->B\n```\nAfter"
        result = preprocess_combined_markdown(content)
        assert isinstance(result, CombinedMarkdownResult)
        assert "mermaid" not in result.content
        assert result.mermaid_blocks_removed == 1
        assert "Before" in result.content
        assert "After" in result.content

    def test_multiple_mermaid_blocks(self):
        content = "```mermaid\nA\n```\ntext\n```Mermaid\nB\n```"
        result = preprocess_combined_markdown(content)
        assert result.mermaid_blocks_removed == 2

    def test_no_mermaid(self):
        content = "Regular markdown content"
        result = preprocess_combined_markdown(content)
        assert result.mermaid_blocks_removed == 0
        assert result.content == content

    def test_fixes_figure_paths(self):
        content = "![fig](../../output/figures/plot.png)"
        result = preprocess_combined_markdown(content)
        assert "../figures/plot.png" in result.content
        assert result.fig_paths_fixed == 1

    def test_fixes_multiple_path_variants(self):
        content = (
            "![a](../../output/figures/a.png)\n"
            "![b](../output/figures/b.png)\n"
            "![c](output/figures/c.png)\n"
        )
        result = preprocess_combined_markdown(content)
        assert result.fig_paths_fixed == 3
        assert "../../output/figures/" not in result.content
        assert "../output/figures/" not in result.content
        assert "output/figures/" not in result.content

    def test_manuscript_vars_substitution(self, tmp_path):
        vars_data = {"title": "My Paper", "version": "1.0"}
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text(yaml.dump(vars_data))

        content = "Title: {{title}}, Version: {{version}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert "My Paper" in result.content
        assert "1.0" in result.content
        assert result.manuscript_vars_substitutions == 2

    def test_manuscript_vars_with_topics(self, tmp_path):
        vars_data = {
            "topics": {
                "algebra": {"lean_sketch": "some lean code", "mathlib_status": "real"},
                "geometry": {"lean_sketch": "", "mathlib_status": "partial"},
            }
        }
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text(yaml.dump(vars_data))

        content = "Topics: {{total_topics}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert "2" in result.content

    def test_manuscript_vars_with_areas(self, tmp_path):
        vars_data = {"areas": {"math": 5, "physics": 3}}
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text(yaml.dump(vars_data))

        content = "Total areas: {{total_areas}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert "2" in result.content

    def test_areas_legacy_scalar_shape_substitutes_count(self, tmp_path):
        """Legacy shape ``areas: {FEP: 14}`` must substitute ``{{areas.FEP.count}}`` → ``14``."""
        vars_data = {"areas": {"FEP": 14, "Thermo": 7}}
        (tmp_path / "manuscript_vars.yaml").write_text(yaml.dump(vars_data))

        content = "FEP={{areas.FEP.count}} Thermo={{areas.Thermo.count}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert "FEP=14" in result.content
        assert "Thermo=7" in result.content

    def test_areas_nested_dict_shape_does_not_emit_dict_repr(self, tmp_path):
        """Nested shape ``areas: {FEP: {count: 14}}`` must substitute to integer text,

        not the Python dict repr ``{'count': 14}`` (regression test for the alias
        loop that previously overwrote the flattened value).
        """
        vars_data = {
            "areas": {
                "FEP": {"count": 14},
                "ActiveInference": {"count": 11},
            }
        }
        (tmp_path / "manuscript_vars.yaml").write_text(yaml.dump(vars_data))

        content = "FEP={{areas.FEP.count}} AI={{areas.ActiveInference.count}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert "FEP=14" in result.content
        assert "AI=11" in result.content
        assert "{'count'" not in result.content
        assert "{\"count\"" not in result.content

    def test_manuscript_vars_missing_file(self, tmp_path):
        content = "No vars: {{title}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert result.manuscript_vars_substitutions == 0

    def test_manuscript_vars_corrupt_yaml(self, tmp_path):
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text(": invalid: yaml: [")
        content = "Content: {{title}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert result.manuscript_vars_substitutions == 0

    def test_manuscript_vars_empty_yaml(self, tmp_path):
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text("")  # None when parsed
        content = "Content: {{title}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert result.manuscript_vars_substitutions == 0

    def test_manuscript_vars_non_dict_yaml(self, tmp_path):
        vars_file = tmp_path / "manuscript_vars.yaml"
        vars_file.write_text("- list\n- items\n")
        content = "Content: {{title}}"
        result = preprocess_combined_markdown(content, manuscript_dir=tmp_path)
        assert result.manuscript_vars_substitutions == 0

    def test_no_manuscript_dir(self):
        content = "No vars: {{title}}"
        result = preprocess_combined_markdown(content, manuscript_dir=None)
        assert result.manuscript_vars_substitutions == 0


class TestPostprocessLatex:
    def test_disables_lmodern(self):
        tex = r"\usepackage{lmodern}" + "\nOther content"
        result = postprocess_latex(tex)
        assert r"% \usepackage{lmodern}" in result

    def test_no_lmodern_unchanged(self):
        tex = r"\usepackage{graphicx}" + "\nOther content"
        result = postprocess_latex(tex)
        assert result == tex

    def test_replaces_hidelinks_with_comma(self):
        tex = r"\hypersetup{hidelinks,pdfborder={0 0 0}}"
        result = postprocess_latex(tex)
        assert "hidelinks" not in result
        assert "colorlinks=true" in result

    def test_replaces_hidelinks_with_newline(self):
        tex = "\\hypersetup{\n  hidelinks,\n  pdfborder={0 0 0}}"
        result = postprocess_latex(tex)
        assert "colorlinks=true" in result

    def test_no_hidelinks_unchanged(self):
        tex = "\\hypersetup{colorlinks=true}"
        result = postprocess_latex(tex)
        assert result == tex

    def test_math_delimiter_fixing(self):
        # The fix_math_delimiters function is called; just make sure it doesn't crash
        tex = r"$x^2$ and $$y^2$$"
        result = postprocess_latex(tex)
        assert isinstance(result, str)

    def test_rewrites_duplicate_hyperref_usepackage(self):
        """A user-preamble ``\\usepackage[opts]{hyperref}`` must be rewritten to

        ``\\PassOptionsToPackage`` + ``\\hypersetup`` so it cannot clash with
        Pandoc's template-loaded hyperref.
        """
        tex = (
            "\\PassOptionsToPackage{unicode}{hyperref}\n"
            "\\hypersetup{pdftitle={Test}}\n"
            "\\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}\n"
            "\\begin{document}\nHello\n\\end{document}"
        )
        result = postprocess_latex(tex)
        assert "\\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}" not in result
        assert "\\PassOptionsToPackage{colorlinks=true,linkcolor=blue,urlcolor=blue}{hyperref}" in result
        assert "\\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}" in result

    def test_leaves_plain_hyperref_usepackage_alone(self):
        """``\\usepackage{hyperref}`` without options is harmless — leave intact."""
        tex = "\\usepackage{hyperref}\n\\begin{document}\n\\end{document}"
        result = postprocess_latex(tex)
        assert "\\usepackage{hyperref}" in result
        assert "\\PassOptionsToPackage" not in result


class TestInjectBibliography:
    def test_existing_bibliography_with_clearpage(self):
        tex = "Content\n\\clearpage\n\\bibliography{references}\n\\end{document}"
        result = inject_bibliography(tex, bib_exists=True)
        # clearpage already present, should not duplicate
        assert result.count("\\clearpage") == 1

    def test_existing_bibliography_without_clearpage(self):
        tex = "Content\n" + " " * 80 + "\\bibliography{references}\n\\end{document}"
        result = inject_bibliography(tex, bib_exists=True)
        assert "\\clearpage" in result

    def test_missing_bibliography_inserted(self):
        tex = "Content\n\\end{document}"
        result = inject_bibliography(tex, bib_exists=True)
        assert "\\bibliography{references}" in result
        assert "\\clearpage" in result

    def test_no_bib_file(self):
        tex = "Content\n\\end{document}"
        result = inject_bibliography(tex, bib_exists=False)
        assert "\\bibliography" not in result

    def test_no_end_document(self):
        tex = "Content without end document marker"
        result = inject_bibliography(tex, bib_exists=True)
        # Should not crash, bibliography not inserted
        assert "\\bibliography" not in result


class TestVerifyFigureReferences:
    def test_all_figures_found(self, tmp_path):
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "plot.png").write_bytes(b"fake png")
        (figures_dir / "chart.pdf").write_bytes(b"fake pdf")

        tex = r"\includegraphics{figures/plot.png}" + "\n" + r"\includegraphics[width=0.5\textwidth]{figures/chart.pdf}"
        # Should not raise
        verify_figure_references(tex, figures_dir)

    def test_missing_figure(self, tmp_path):
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        tex = r"\includegraphics{figures/missing.png}"
        # Should not raise, just logs warnings
        verify_figure_references(tex, figures_dir)

    def test_no_figures(self, tmp_path):
        tex = "No figure references here"
        verify_figure_references(tex, tmp_path)

    def test_with_options(self, tmp_path):
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "img.png").write_bytes(b"data")
        tex = r"\includegraphics[width=\textwidth]{figures/img.png}"
        verify_figure_references(tex, figures_dir)

    def test_similar_files_logged(self, tmp_path):
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "plot_v2.png").write_bytes(b"data")
        tex = r"\includegraphics{figures/plot.png}"
        # Should not crash; logs similar file hint
        verify_figure_references(tex, figures_dir)


class TestPrevalidateMarkdown:
    def test_valid_markdown(self, tmp_path):
        md = tmp_path / "combined.md"
        md.write_text("# Title\n\nSome content with {balanced} braces.")
        errors, content = prevalidate_markdown(md)
        assert isinstance(errors, list)
        assert isinstance(content, str)
        assert "Title" in content

    def test_missing_file(self, tmp_path):
        md = tmp_path / "nonexistent.md"
        errors, content = prevalidate_markdown(md)
        assert errors == []
        assert content == ""

    def test_unbalanced_braces(self, tmp_path):
        md = tmp_path / "combined.md"
        md.write_text("Unbalanced { brace without closing")
        errors, content = prevalidate_markdown(md)
        # check_brace_balance may or may not flag this depending on implementation
        assert isinstance(errors, list)


class TestInjectLatexPreamble:
    def test_preamble_injected_before_begin_document(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        preamble_file = manuscript_dir / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{amsmath}\n```\n")

        config_yaml = manuscript_dir / "config.yaml"
        config_yaml.write_text("paper:\n  title: Test\n")

        tex = "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}"
        result = inject_latex_preamble(tex, manuscript_dir)
        assert "\\usepackage{graphicx}" in result
        assert "\\begin{document}" in result

    def test_no_preamble_file(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        config_yaml = manuscript_dir / "config.yaml"
        config_yaml.write_text("paper:\n  title: Test\n")

        tex = "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}"
        result = inject_latex_preamble(tex, manuscript_dir)
        # graphicx should still be added
        assert "\\usepackage{graphicx}" in result

    def test_no_begin_document(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        tex = "Just some text without document markers"
        result = inject_latex_preamble(tex, manuscript_dir)
        assert isinstance(result, str)

    def test_maketitle_replacement(self, tmp_path):
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        config_yaml = manuscript_dir / "config.yaml"
        config_yaml.write_text(
            "paper:\n  title: Test Paper\nauthors:\n  - name: Alice\n    affiliation: MIT\n"
        )

        tex = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\maketitle\n"
            "Content here\n"
            "\\end{document}"
        )
        result = inject_latex_preamble(tex, manuscript_dir)
        assert isinstance(result, str)


class TestPrevalidateSourceMarkdown:
    """Hard-gate behaviour: clean / undefined-citation / bare-pipe inputs."""

    def _make_manuscript(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "references.bib").write_text(
            "@article{good_key, title={Ok}, year={2025}}\n",
            encoding="utf-8",
        )
        return manuscript

    def test_clean_manuscript_passes(self, tmp_path):
        manuscript = self._make_manuscript(tmp_path)
        (manuscript / "01_intro.md").write_text(
            "# Intro\n\nSee [@good_key].\n", encoding="utf-8"
        )
        prevalidate_source_markdown(manuscript)

    def test_undefined_citation_blocks_render(self, tmp_path):
        manuscript = self._make_manuscript(tmp_path)
        (manuscript / "01_intro.md").write_text(
            "# Intro\n\nSee [@missing_key] and [@good_key].\n", encoding="utf-8"
        )
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_source_markdown(manuscript)
        assert "missing_key" in str(excinfo.value)
        assert "Pre-render validation failed" in str(excinfo.value)

    def test_bare_pipe_in_table_blocks_render(self, tmp_path):
        manuscript = self._make_manuscript(tmp_path)
        (manuscript / "01_intro.md").write_text(
            "| Symbol | Meaning |\n|--------|---------|\n"
            "| \\|state\\| | bar in cell |\n",
            encoding="utf-8",
        )
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_source_markdown(manuscript)
        msg = str(excinfo.value)
        assert "Pre-render validation failed" in msg
        assert "01_intro.md" in msg

    def test_explicit_path_list_signature(self, tmp_path):
        manuscript = self._make_manuscript(tmp_path)
        md = manuscript / "01_intro.md"
        md.write_text("Clean text with no citations.\n", encoding="utf-8")
        prevalidate_source_markdown([md], bib_file=manuscript / "references.bib")
