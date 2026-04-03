"""Tests for infrastructure.validation.repo.known_exceptions — expanded coverage."""

from infrastructure.validation.repo.known_exceptions import (
    is_valid_directory_reference,
    is_template_pattern,
    is_code_example,
    is_table_artifact,
    is_code_block_artifact,
    is_mermaid_artifact,
    is_latex_reference,
)


class TestIsValidDirectoryReference:
    def test_known_directory(self):
        assert is_valid_directory_reference("infrastructure/") is True

    def test_known_directory_exact(self):
        assert is_valid_directory_reference("scripts/") is True

    def test_unknown_directory(self):
        assert is_valid_directory_reference("unknown_dir/") is False

    def test_subdirectory_of_known(self):
        assert is_valid_directory_reference("infrastructure/core/") is True

    def test_stripped_match(self):
        """Leading/trailing whitespace stripped before matching."""
        assert is_valid_directory_reference("  docs/  ") is True

    def test_base_dir_match(self):
        """Directory ending with / where base matches known dir."""
        assert is_valid_directory_reference("tests/") is True


class TestIsTemplatePattern:
    def test_curly_brace_template(self):
        assert is_template_pattern("projects/{name}/src") is True

    def test_angle_bracket_template(self):
        assert is_template_pattern("infrastructure/<module>/core") is True

    def test_no_template(self):
        assert is_template_pattern("infrastructure/core/exceptions.py") is False


class TestIsCodeExample:
    def test_your_project(self):
        assert is_code_example("projects/your_project/src") is True

    def test_example_com(self):
        assert is_code_example("https://example.com/path") is True

    def test_real_path(self):
        assert is_code_example("infrastructure/core/exceptions.py") is False

    def test_my_project(self):
        assert is_code_example("projects/my_project/scripts") is True

    def test_analysis_py(self):
        assert is_code_example("scripts/analysis.py") is True


class TestIsTableArtifact:
    def test_closing_bracket(self):
        assert is_table_artifact("path]") is True

    def test_closing_paren(self):
        assert is_table_artifact("path)") is True

    def test_backtick(self):
        assert is_table_artifact("path`") is True

    def test_normal_path(self):
        assert is_table_artifact("infrastructure/core") is False


class TestIsCodeBlockArtifact:
    def test_newline(self):
        assert is_code_block_artifact("path\nmore") is True

    def test_carriage_return(self):
        assert is_code_block_artifact("path\rmore") is True

    def test_ends_with_paren(self):
        assert is_code_block_artifact("infrastructure/core)") is True

    def test_ends_with_bracket(self):
        assert is_code_block_artifact("path]") is True

    def test_ends_with_brace(self):
        assert is_code_block_artifact("path}") is True

    def test_ends_with_pipe(self):
        assert is_code_block_artifact("path|") is True

    def test_normal_path(self):
        assert is_code_block_artifact("infrastructure/core") is False


class TestIsMermaidArtifact:
    def test_backslash_n(self):
        assert is_mermaid_artifact("text\\nmore") is True

    def test_br_tag(self):
        assert is_mermaid_artifact("text<br/>more") is True

    def test_br_no_slash(self):
        assert is_mermaid_artifact("text<br>more") is True

    def test_normal_path(self):
        assert is_mermaid_artifact("infrastructure/core") is False


class TestIsLatexReference:
    def test_ref(self):
        assert is_latex_reference("\\ref{fig:1}") is True

    def test_cite(self):
        assert is_latex_reference("\\cite{smith2020}") is True

    def test_eqref(self):
        assert is_latex_reference("\\eqref{eq:main}") is True

    def test_label(self):
        assert is_latex_reference("\\label{sec:intro}") is True

    def test_not_latex(self):
        assert is_latex_reference("infrastructure/core.py") is False
