"""Tests for ``newspaper.content``."""

import pytest

from newspaper.content import FIXTURE_SENTENCES, fixture_copy, fixture_paragraph


def test_fixture_sentences_non_empty() -> None:
    assert len(FIXTURE_SENTENCES) >= 4


def test_fixture_paragraph_deterministic() -> None:
    a = fixture_paragraph(seed=5)
    b = fixture_paragraph(seed=5)
    assert a == b
    assert len(a) > 50


def test_fixture_paragraph_differs_by_seed() -> None:
    assert fixture_paragraph(seed=1) != fixture_paragraph(seed=2)


def test_fixture_copy_grows_with_num_paragraphs() -> None:
    one = fixture_copy(1, seed=0)
    three = fixture_copy(3, seed=0)
    assert len(three) > len(one)
    assert three.count("\n\n") == 2


def test_fixture_copy_same_seed_reproducible() -> None:
    assert fixture_copy(2, seed=99) == fixture_copy(2, seed=99)


def test_fixture_copy_requires_positive_count() -> None:
    with pytest.raises(ValueError):
        fixture_copy(0, seed=0)
