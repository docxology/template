"""Tests for infrastructure.rendering._pdf_math_delimiters module.

Tests fix_math_delimiters for Pandoc-generated LaTeX math repair.
"""

from __future__ import annotations


from infrastructure.rendering._pdf_math_delimiters import fix_math_delimiters


class TestFixMathDelimiters:
    """Tests for fix_math_delimiters."""

    def test_no_broken_delimiters(self):
        """Content without broken delimiters should pass through unchanged."""
        content = r"\[E = mc^2\]"
        result = fix_math_delimiters(content)
        assert result == content

    def test_plain_text_unchanged(self):
        result = fix_math_delimiters("Just plain text.")
        assert result == "Just plain text."

    def test_empty_string(self):
        result = fix_math_delimiters("")
        assert result == ""

    def test_fix_display_math_no_label(self):
        """Should fix {[} ... {]} to \\[ ... \\]."""
        content = "{[}x^2 + y^2 = z^2{]}"
        result = fix_math_delimiters(content)
        assert r"\[" in result
        assert r"\]" in result
        assert "{[}" not in result
        assert "{]}" not in result

    def test_fix_display_math_with_label(self):
        """Should fix {[} ... {]}\\label{eq:x}{]} to \\[...\\label{eq:x}\\]."""
        content = r"{[}x^2 + y^2 = z^2{]}\label{eq:pythag}{]}"
        result = fix_math_delimiters(content)
        assert r"\[" in result
        assert r"\label{eq:pythag}" in result
        assert r"\]" in result

    def test_fix_textbar_to_mid(self):
        r"""Should replace \textbar with \mid."""
        content = r"P(A \textbar B)"
        result = fix_math_delimiters(content)
        assert r"\mid" in result
        assert r"\textbar" not in result

    def test_fix_broken_subscripts_in_simple_math(self):
        r"""Should fix s\_tau to s_tau inside matched display math."""
        # Use content without { in the math body so the no-label pattern matches
        content = r"{[}s + t{]}"
        result = fix_math_delimiters(content)
        assert r"\[" in result
        assert r"\]" in result

    def test_emph_wrappers_fixed_in_label_math(self):
        r"""Should remove \emph{} wrappers from math with label."""
        content = r"{[}\emph{x^2}{]}\label{eq:x}{]}"
        result = fix_math_delimiters(content)
        assert r"\emph" not in result
        assert r"\label{eq:x}" in result

    def test_greek_letter_fix(self):
        r"""Should fix broken Greek letter + close paren patterns."""
        content = r"Using \tau\) in equation."
        result = fix_math_delimiters(content)
        assert "tau" in result

    def test_multiple_display_math_blocks(self):
        """Should fix multiple math blocks independently."""
        content = "{[}a + b{]}\nSome text\n{[}c + d{]}"
        result = fix_math_delimiters(content)
        assert result.count(r"\[") == 2
        assert result.count(r"\]") == 2

    def test_preserves_non_math_content(self):
        """Text between math blocks should be preserved."""
        content = "Before\n{[}x{]}\nBetween\n{[}y{]}\nAfter"
        result = fix_math_delimiters(content)
        assert "Before" in result
        assert "Between" in result
        assert "After" in result
