"""Tests for infrastructure.rendering._pdf_preflight module.

Tests brace balance checking in markdown content.
"""

from __future__ import annotations


from infrastructure.rendering._pdf_preflight import check_brace_balance


class TestCheckBraceBalance:
    """Tests for check_brace_balance."""

    def test_balanced_content_no_warnings(self):
        content = "# Section {#sec:intro}\n\nSome content with {bold} text."
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_empty_content(self):
        warnings = check_brace_balance("")
        assert warnings == []

    def test_no_braces(self):
        warnings = check_brace_balance("Plain text without any braces at all.")
        assert warnings == []

    def test_unbalanced_opening_brace(self):
        content = "Some text with { an unclosed brace."
        warnings = check_brace_balance(content)
        assert len(warnings) > 0
        assert any("unbalanced" in w.lower() for w in warnings)

    def test_unbalanced_closing_brace(self):
        content = "Some text with } an extra closing brace."
        warnings = check_brace_balance(content)
        assert len(warnings) > 0

    def test_latex_command_braces_balanced(self):
        content = "The equation \\textbf{bold text} is fine."
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_latex_command_with_optional_args(self):
        content = "\\usepackage[utf8]{inputenc}"
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_fenced_code_block_ignored(self):
        content = "```\n{ unbalanced in code }\n```"
        warnings = check_brace_balance(content)
        # Braces in code blocks should not count (they are stripped)
        assert warnings == []

    def test_inline_code_ignored(self):
        content = "Use `{key: value}` in your config."
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_header_attribute_balanced(self):
        content = "## Introduction {#sec:intro}"
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_header_attribute_unbalanced(self):
        content = "## Introduction {#sec:intro"
        warnings = check_brace_balance(content)
        assert len(warnings) > 0

    def test_multiple_balanced_braces(self):
        content = "{a} {b} {c}"
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_nested_balanced_braces(self):
        content = "{{nested}}"
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_complex_latex_document(self):
        content = """# Title {#sec:title}

\\begin{equation}
E = mc^{2}
\\end{equation}

Some text with \\cite{ref1} and \\citep{ref2}.
"""
        warnings = check_brace_balance(content)
        assert warnings == []

    def test_multiline_unbalanced(self):
        content = "Line 1 {\nLine 2\nLine 3"
        warnings = check_brace_balance(content)
        assert len(warnings) > 0
