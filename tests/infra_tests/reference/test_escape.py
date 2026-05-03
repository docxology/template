"""Tests for infrastructure.reference.citation.escape."""

from __future__ import annotations

import pytest

from infrastructure.reference.citation.escape import escape_latex, unescape_latex


class TestEscapeLatex:
    def test_empty_string_returns_empty(self):
        assert escape_latex("") == ""

    def test_plain_text_unchanged(self):
        assert escape_latex("Numerical optimization") == "Numerical optimization"

    def test_ampersand_escaped(self):
        assert escape_latex("Springer Science & Business Media") == r"Springer Science \& Business Media"

    def test_percent_escaped(self):
        assert escape_latex("50% increase") == r"50\% increase"

    def test_dollar_escaped(self):
        assert escape_latex("$100") == r"\$100"

    def test_hash_escaped(self):
        assert escape_latex("#tag") == r"\#tag"

    def test_underscore_escaped(self):
        assert escape_latex("snake_case") == r"snake\_case"

    def test_braces_escaped(self):
        assert escape_latex("{group}") == r"\{group\}"

    def test_unicode_preserved(self):
        # Matches the references.bib convention: bare unicode, no escaping.
        assert escape_latex("Méthode générale") == "Méthode générale"
        assert escape_latex("séances de l'Académie") == "séances de l'Académie"

    def test_backslash_replaced(self):
        # A literal backslash is escaped via \textbackslash{}
        assert escape_latex("a\\b") == r"a\textbackslash{}b"

    def test_tilde_replaced(self):
        assert escape_latex("a~b") == r"a\textasciitilde{}b"

    def test_caret_replaced(self):
        assert escape_latex("x^2") == r"x\textasciicircum{}2"


class TestUnescapeLatex:
    def test_empty_string_returns_empty(self):
        assert unescape_latex("") == ""

    def test_plain_text_unchanged(self):
        assert unescape_latex("plain text") == "plain text"

    @pytest.mark.parametrize(
        "raw",
        [
            "Springer Science & Business Media",
            "50% increase",
            "$100 _x #tag {brace}",
            "x^2 a~b",
        ],
    )
    def test_round_trip(self, raw: str):
        assert unescape_latex(escape_latex(raw)) == raw

    def test_unicode_round_trip(self):
        text = "Méthode générale & l'Académie"
        assert unescape_latex(escape_latex(text)) == text
