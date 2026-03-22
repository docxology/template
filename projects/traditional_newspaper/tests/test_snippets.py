"""Tests for ``newspaper.snippets``."""

import pytest

from newspaper.snippets import (
    byline,
    headline,
    multicol_begin,
    multicol_end,
    rule_line,
)


def test_multicol_begin_requires_two_columns() -> None:
    with pytest.raises(ValueError):
        multicol_begin(1)
    assert r"\begin{multicols}{3}" in multicol_begin(3)


def test_multicol_end_closes_environment() -> None:
    assert r"\end{multicols}" in multicol_end()


def test_headline_levels() -> None:
    h1 = headline("Morning Wire")
    assert r"\Large" in h1
    h2 = headline("City Desk", level=2)
    assert r"\large" in h2
    h3 = headline("Brief", level=3)
    assert r"\Large" not in h3 and r"\large" not in h3
    assert "Brief" in h3


def test_headline_escapes_special_chars() -> None:
    h = headline("AT&T 100%")
    assert r"\%" in h or "%" not in h.split("{")[-1]


def test_byline_with_dateline() -> None:
    b = byline("R. Reporter", dateline="March 22, 2026")
    assert "R. Reporter" in b
    assert "2026" in b


def test_byline_without_dateline() -> None:
    b = byline("Staff")
    assert "Staff" in b


def test_rule_line_contains_rule() -> None:
    assert r"\rule" in rule_line()
