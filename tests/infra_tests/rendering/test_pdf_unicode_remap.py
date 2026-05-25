"""Tests for infrastructure.rendering._pdf_unicode_remap.

Verifies that prose-only unicode glyphs (e.g. ✓, ≈, α) are rewritten to
LaTeX commands while Verbatim/Highlighting/lstlisting/\\verb regions are
preserved byte-for-byte.
"""

from __future__ import annotations

from infrastructure.rendering._pdf_unicode_remap import (
    UnicodeRemapResult,
    remap_prose_unicode,
)


class TestProseGlyphRemap:
    """Glyphs in prose should be replaced with their LaTeX command equivalents."""

    def test_checkmark(self):
        result = remap_prose_unicode("Status: ✓ verified.")
        assert r"\texorpdfstring{\ensuremath{\checkmark}}{[ok]}" in result.content
        assert "✓" not in result.content
        assert result.replacements == 1

    def test_approx(self):
        result = remap_prose_unicode("Wall-clock ≈ 12 minutes.")
        assert r"\texorpdfstring{\ensuremath{\approx}}{~}" in result.content
        assert "≈" not in result.content

    def test_alpha_sigma(self):
        result = remap_prose_unicode(r"The α-divergence and σ-algebra.")
        assert r"\texorpdfstring{\ensuremath{\alpha}}{alpha}" in result.content
        assert r"\texorpdfstring{\ensuremath{\sigma}}{sigma}" in result.content

    def test_safe_in_moving_argument(self):
        r"""``\texorpdfstring`` makes the replacement safe inside section titles."""
        text = r"\subsubsection{Catalogue ↔ SKETCHES Agreement}"
        result = remap_prose_unicode(text)
        assert r"\texorpdfstring" in result.content
        assert "{<->}" in result.content, "must include plain-ASCII PDF-bookmark form"

    def test_original_problem_glyphs_in_one_pass(self):
        text = "✓ ≈ α σ ≪ ↔ ≥ ≠ ∎ ○ ∣ ⚠"
        result = remap_prose_unicode(text)
        for glyph in "✓≈ασ≪↔≥≠∎○∣⚠":
            assert glyph not in result.content, f"glyph {glyph!r} survived"
        assert result.replacements == 12

    def test_pipe_uses_textbar_not_ensuremath(self):
        """∣ must remap to \\textbar (text mode); \\ensuremath{\\mid} routes
        through unicode-math → lmroman which lacks U+2223 and warns."""
        result = remap_prose_unicode("∣")
        assert r"\textbar" in result.content
        assert r"\ensuremath{\mid}" not in result.content

    def test_extended_greek_lowercase(self):
        """Expanded dict covers full lower-case Greek alphabet (24 letters)."""
        greek = "αβγδεζηθικλμνξπρστυφχψω"
        result = remap_prose_unicode(greek)
        for g in greek:
            assert g not in result.content, f"greek {g!r} not remapped"
        assert result.replacements == len(greek)

    def test_extended_set_theory_logic(self):
        text = "∃ ∀ ∈ ∉ ∅ ⊆ ⊂ ⊇ ⊃ ∪ ∩"
        result = remap_prose_unicode(text)
        for g in "∃∀∈∉∅⊆⊂⊇⊃∪∩":
            assert g not in result.content
        assert r"\exists" in result.content
        assert r"\forall" in result.content

    def test_extended_arrows_and_operators(self):
        text = "→ ↦ ⇒ ⇔ ∂ ∫ ∇ ∞ − × ±"
        result = remap_prose_unicode(text)
        for g in "→↦⇒⇔∂∫∇∞−×±":
            assert g not in result.content
        assert r"\to" in result.content
        assert r"\partial" in result.content

    def test_blackboard_bold_number_sets(self):
        text = "ℕ ℝ ℤ ℚ ℂ"
        result = remap_prose_unicode(text)
        for g in "ℕℝℤℚℂ":
            assert g not in result.content
        assert r"\mathbb{N}" in result.content
        assert r"\mathbb{R}" in result.content

    def test_micro_sign_distinct_from_mu(self):
        """U+00B5 MICRO SIGN and U+03BC GREEK MU both map to the same LaTeX."""
        text = "µ vs μ"
        result = remap_prose_unicode(text)
        assert "µ" not in result.content
        assert "μ" not in result.content
        assert result.content.count(r"\mu") == 2

    def test_per_glyph_counts(self):
        result = remap_prose_unicode("✓ ✓ ≈ α α α")
        assert result.per_glyph_counts["✓"] == 2
        assert result.per_glyph_counts["≈"] == 1
        assert result.per_glyph_counts["α"] == 3

    def test_no_glyphs_returns_unchanged(self):
        text = "Plain ASCII text only."
        result = remap_prose_unicode(text)
        assert result.content == text
        assert result.replacements == 0


class TestVerbatimPreservation:
    """Verbatim / Highlighting / lstlisting blocks must remain byte-for-byte."""

    def test_highlighting_block_preserved(self):
        text = (
            "Prose ✓ before.\n"
            "\\begin{Highlighting}[]\n"
            "theorem foo (μ ν : Measure α) (h : μ ≪ ν) : 0 ≤ klDiv μ ν := by sorry\n"
            "\\end{Highlighting}\n"
            "Prose ✓ after."
        )
        result = remap_prose_unicode(text)
        assert "μ ≪ ν" in result.content, "≪ must be preserved inside Highlighting"
        assert " α" in result.content, "α must be preserved inside Highlighting"
        assert result.content.count(r"\texorpdfstring{\ensuremath{\checkmark}}{[ok]}") == 2
        assert result.content.count("✓") == 0

    def test_verbatim_lower_preserved(self):
        text = "Before ✓\n\\begin{verbatim}\nα β γ ≈\n\\end{verbatim}\nAfter ✓"
        result = remap_prose_unicode(text)
        assert "α β γ ≈" in result.content
        assert result.content.count(r"\texorpdfstring{\ensuremath{\checkmark}}{[ok]}") == 2

    def test_lstlisting_preserved(self):
        text = (
            "Body α before.\n"
            "\\begin{lstlisting}[language=lean4]\n"
            "def f (x : α) : σ := x\n"
            "\\end{lstlisting}\n"
            "Body α after."
        )
        result = remap_prose_unicode(text)
        assert "(x : α)" in result.content
        assert " σ" in result.content
        assert result.content.count(r"\texorpdfstring{\ensuremath{\alpha}}{alpha}") == 2

    def test_verb_inline_preserved(self):
        text = r"Use \verb|μ ≪ ν| inline; prose ≪ outside."
        result = remap_prose_unicode(text)
        assert r"\verb|μ ≪ ν|" in result.content
        assert r"prose \texorpdfstring{\ensuremath{\ll}}{<<} outside" in result.content

    def test_passthrough_preserved(self):
        text = r"Prose α; \passthrough{α} stays literal."
        result = remap_prose_unicode(text)
        assert r"\passthrough{α}" in result.content
        assert r"Prose \texorpdfstring{\ensuremath{\alpha}}{alpha};" in result.content


class TestResult:
    def test_returns_unicode_remap_result(self):
        result = remap_prose_unicode("test ✓")
        assert isinstance(result, UnicodeRemapResult)
        assert hasattr(result, "content")
        assert hasattr(result, "replacements")
        assert hasattr(result, "per_glyph_counts")
