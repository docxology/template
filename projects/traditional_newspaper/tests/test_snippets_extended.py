"""Extended tests for ``newspaper.snippets``."""

import pytest

import newspaper.snippets as snippets
from newspaper.snippets import (
    classified_line,
    dateline,
    headline,
    pull_quote,
    section_label,
)


def test_escape_latex_fragment_backslash() -> None:
    """Backslash is expanded first; braces in ``\\textbackslash{}`` are then escaped."""
    assert snippets._escape_latex_fragment("\\") == r"\textbackslash\{\}"


@pytest.mark.parametrize(
    ("raw", "expected_piece"),
    [
        ("{", r"\{"),
        ("}", r"\}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("^", r"\textasciicircum{}"),
        ("~", r"\textasciitilde{}"),
    ],
)
def test_escape_latex_fragment_specials(raw: str, expected_piece: str) -> None:
    out = snippets._escape_latex_fragment(raw)
    assert expected_piece in out


def test_dateline_wraps_italic() -> None:
    s = dateline("City, March 22, 2026")
    assert r"\textit" in s
    assert "City" in s


def test_section_label_small_caps() -> None:
    s = section_label("NATIONAL")
    assert r"\textsc" in s
    assert "NATIONAL" in s


def test_pull_quote_uses_quote_env() -> None:
    s = pull_quote("A short pull quote.")
    assert r"\begin{quote}" in s
    assert r"\end{quote}" in s
    assert "pull quote" in s


def test_classified_line_bold_item() -> None:
    s = classified_line("FOR SALE", "Typewriter")
    assert r"\textbf" in s
    assert "FOR SALE" in s
    assert "Typewriter" in s


def test_classified_line_item_only() -> None:
    s = classified_line("LOST")
    assert "LOST" in s
    assert r"\textit" not in s


def test_headline_still_escapes_percent() -> None:
    s = headline("100% complete")
    assert r"\%" in s or "100" in s
