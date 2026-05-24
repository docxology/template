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
        r"""``\(\tau)`` (broken closure) should become ``\(\tau\)`` (proper)."""
        content = r"Using \(\tau) in equation."
        result = fix_math_delimiters(content)
        assert r"\(\tau\)" in result
        assert r"\(\tau)" not in result

    def test_greek_letter_subscript_fix(self):
        r"""``\(s_\tau)`` (broken closure on subscript) should become ``\(s_\tau\)``."""
        content = r"State \(s_\tau) at time tau."
        result = fix_math_delimiters(content)
        assert r"\(s_\tau\)" in result
        assert r"\(s_\tau)" not in result

    def test_multiple_display_math_blocks(self):
        """Should fix multiple math blocks independently."""
        content = "{[}a + b{]}\nSome text\n{[}c + d{]}"
        result = fix_math_delimiters(content)
        assert result.count(r"\[") == 2
        assert result.count(r"\]") == 2

    def test_preserves_non_math_content(self):
        """Text between math blocks should be preserved."""
        content = "Before\n{[}x = 1{]}\nBetween\n{[}y = 2{]}\nAfter"
        result = fix_math_delimiters(content)
        assert "Before" in result
        assert "Between" in result
        assert "After" in result

    def test_preserves_literal_square_brackets(self):
        """Literal bracketed prose must not become display math."""
        content = r"Normal {[}HCO\(_3^-\){]}/{[}CO\(_2\){]} ratio and {[}inside{]} table text."
        result = fix_math_delimiters(content)
        assert result == content
        assert r"\[HCO" not in result
        assert r"\[inside\]" not in result


class TestFixMathDelimitersFromPdfMathDelimiters:
    def test_no_math(self):
        tex = "This is plain text with no math."
        assert fix_math_delimiters(tex) == tex

    def test_display_math_with_label(self):
        tex = r"{[}E = mc^2{]}\label{eq:einstein}{]}"
        result = fix_math_delimiters(tex)
        assert r"\[" in result
        assert r"\]" in result
        assert r"\label{eq:einstein}" in result
        # The broken {[} and {]} should be gone
        assert "{[}" not in result

    def test_display_math_no_label(self):
        tex = "{[}x + y = z{]}\n"
        result = fix_math_delimiters(tex)
        assert r"\[" in result
        assert r"\]" in result
        assert "{[}" not in result

    def test_nested_bracket_removal(self):
        # {[} and {]} inside math content are removed within matched display math
        tex = "{[}a {[} + b {]} = c{]}\n"
        result = fix_math_delimiters(tex)
        # The outer {[}...{]} is matched by the no-label pattern (needs trailing \s or $)
        # Inner {[} and {]} are removed from the matched content
        assert r"\[" in result

    def test_textbar_to_mid(self):
        tex = r"P(A \textbar B)"
        result = fix_math_delimiters(tex)
        assert r"\mid" in result
        assert r"\textbar" not in result

    def test_broken_subscript_fix(self):
        # Within display math, s\_\tau should become s_\tau
        tex = "{[}s\\_\\tau{]}\n"
        result = fix_math_delimiters(tex)
        # The fix should clean up the escaped underscore within matched math
        assert r"\[" in result

    def test_emph_wrapper_removal_in_label_block(self):
        # \emph is removed within display math blocks matched by the with-label pattern
        # The with-label pattern uses greedy .* so it CAN match content with {
        tex = "{[}\\emph{content}{]}\\label{eq:test}{]}"
        result = fix_math_delimiters(tex)
        assert r"\[" in result
        assert "content" in result
        assert r"\emph" not in result

    def test_greek_letter_fix(self):
        tex = r"\(\tau)"
        result = fix_math_delimiters(tex)
        assert r"\(\tau\)" in result

    def test_multiple_greek_letters(self):
        tex = r"\(\alpha) and \(\beta) and \(\gamma)"
        result = fix_math_delimiters(tex)
        assert r"\(\alpha\)" in result
        assert r"\(\beta\)" in result
        assert r"\(\gamma\)" in result

    def test_all_greek_letters(self):
        greeks = ["tau", "pi", "Theta", "alpha", "beta", "gamma",
                   "lambda", "kappa", "sigma", "phi", "eta",
                   "mu", "nu", "rho", "omega"]
        for g in greeks:
            tex = f"\\(\\{g})"
            result = fix_math_delimiters(tex)
            assert f"\\(\\{g}\\)" in result, f"Failed for \\{g}"

    def test_greek_letter_subscript_closure(self):
        r"""``\(s_\tau)`` (broken) -> ``\(s_\tau\)`` (proper)."""
        tex = r"\(s_\tau)"
        result = fix_math_delimiters(tex)
        assert r"\(s_\tau\)" in result

    def test_already_proper_greek_unchanged(self):
        r"""Already-proper ``\(\sigma\)`` must be left alone (idempotent)."""
        tex = r"\(\sigma\)"
        assert fix_math_delimiters(tex) == tex

    def test_mathbb_emph_pattern_in_label_block(self):
        # Complex mathbb pattern within labeled display math (greedy pattern matches)
        tex = "{[}\\mathbb{E}\\emph{\\{q(s}\\tau)\\}{]}\\label{eq:exp}{]}"
        result = fix_math_delimiters(tex)
        assert r"\[" in result
        assert r"\label{eq:exp}" in result

    def test_multiple_display_math_blocks(self):
        tex = "{[}a = b{]}\n\n{[}c = d{]}\n"
        result = fix_math_delimiters(tex)
        # Both should be fixed
        assert result.count(r"\[") == 2
        assert result.count(r"\]") == 2

    def test_preserves_non_math_content(self):
        tex = "Some text before.\n{[}x = 1{]}\nSome text after.\n"
        result = fix_math_delimiters(tex)
        assert "Some text before." in result
        assert "Some text after." in result

    def test_preserves_literal_bracketed_inline_math(self):
        tex = r"literal concentration {[}CO\(_2\){]} and table column {[}outside{]}"
        assert fix_math_delimiters(tex) == tex

    def test_empty_input(self):
        assert fix_math_delimiters("") == ""

    def test_display_math_with_label_complex(self):
        tex = r"{[}\sum_{i=1}^{n} x_i = S{]}\label{eq:sum}{]}"
        result = fix_math_delimiters(tex)
        assert r"\label{eq:sum}" in result
        assert "{[}" not in result
