"""Tests for continued fraction utilities."""

import math

import pytest

from continued_fractions import (
    continued_fraction_exact_positive_rational,
    continued_fraction_terms,
    convergents,
    value_from_convergent,
)


def test_continued_fraction_exact_eight_fifths() -> None:
    assert continued_fraction_exact_positive_rational(8, 5) == [1, 1, 1, 2]


def test_convergents_reconstruct_rational() -> None:
    terms = continued_fraction_exact_positive_rational(22, 7)
    last = None
    for pair in convergents(terms):
        last = pair
    assert last is not None
    p, q = last
    assert p / q == pytest.approx(22 / 7)


def test_continued_fraction_terms_phi_starts_with_unit_quotients() -> None:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    terms = continued_fraction_terms(phi, max_terms=12)
    assert terms[0] == 1
    assert all(a == 1 for a in terms[1:8])


def test_continued_fraction_terms_rejects_nonpositive() -> None:
    with pytest.raises(ValueError):
        continued_fraction_terms(0.0)
    with pytest.raises(ValueError):
        continued_fraction_terms(-1.0)


def test_value_from_convergent() -> None:
    assert value_from_convergent(7, 5) == pytest.approx(1.4)


def test_value_from_convergent_zero_denominator() -> None:
    with pytest.raises(ValueError):
        value_from_convergent(1, 0)


def test_continued_fraction_exact_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        continued_fraction_exact_positive_rational(0, 1)
    with pytest.raises(ValueError):
        continued_fraction_exact_positive_rational(1, 0)


def test_convergents_empty_yields_nothing() -> None:
    assert list(convergents([])) == []


def test_continued_fraction_terms_integer_stops() -> None:
    terms = continued_fraction_terms(3.0, max_terms=20)
    assert terms == [3]


def test_continued_fraction_terms_one_point_five() -> None:
    terms = continued_fraction_terms(1.5, max_terms=10, tol=1e-15)
    assert terms[0] == 1
    assert terms[1] == 2
