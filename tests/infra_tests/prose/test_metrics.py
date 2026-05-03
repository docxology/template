"""Tests for infrastructure.prose.analysis.metrics — real text, no mocks."""

from __future__ import annotations

import pytest

from infrastructure.prose.analysis.metrics import (
    ProseMetrics,
    compute_metrics,
    count_syllables,
    is_complex_word,
    split_paragraphs,
    split_sentences,
    tokenize_words,
)


class TestSyllables:
    @pytest.mark.parametrize(
        "word,expected",
        [
            ("a", 1),
            ("the", 1),
            ("hello", 2),
            ("computer", 3),
            ("optimization", 5),
            ("rhythm", 1),  # one vowel-group; we accept under-count
            ("table", 2),  # silent 'e' is preserved when word ends 'le'
            # "create" -> "creat" → one vowel-group "ea" → silent-e drops to 0,
            # then min(1, 0) = 1. Heuristic under-counts here; documenting.
            ("create", 1),
        ],
    )
    def test_count_syllables(self, word: str, expected: int):
        assert count_syllables(word) == expected

    def test_empty_word(self):
        assert count_syllables("") == 0

    def test_minimum_one(self):
        assert count_syllables("xyz") == 1


class TestComplexWord:
    def test_three_syllables_lower(self):
        assert is_complex_word("computer") is True

    def test_proper_noun_excluded(self):
        assert is_complex_word("Cambridge") is False

    def test_short_word_excluded(self):
        assert is_complex_word("the") is False

    def test_inflected_form_excluded(self):
        assert is_complex_word("computed") is False
        assert is_complex_word("computes") is False
        assert is_complex_word("computing") is False


class TestTokenization:
    def test_words(self):
        assert tokenize_words("Hello, world!") == ["Hello", "world"]

    def test_hyphenated(self):
        assert "self-aware" in tokenize_words("a self-aware system")

    def test_paragraphs(self):
        text = "First.\n\nSecond.\n\n   Third.   "
        assert split_paragraphs(text) == ["First.", "Second.", "Third."]

    def test_sentences(self):
        text = "Hello world. This is a test! Is it?"
        assert split_sentences(text) == [
            "Hello world.",
            "This is a test!",
            "Is it?",
        ]

    def test_empty_inputs(self):
        assert tokenize_words("") == []
        assert split_paragraphs("") == []
        assert split_sentences("") == []


class TestComputeMetrics:
    def test_empty(self):
        m = compute_metrics("")
        assert isinstance(m, ProseMetrics)
        assert m.word_count == 0
        assert m.flesch_reading_ease == 0.0

    def test_simple_text(self):
        text = "The cat sat on the mat. Dogs run fast."
        m = compute_metrics(text)
        assert m.word_count == 9
        assert m.sentence_count == 2
        assert m.avg_words_per_sentence == 4.5
        # Easy text → high FRE
        assert m.flesch_reading_ease > 70

    def test_complex_text_fkgl_higher(self):
        complex_text = (
            "Convex optimization investigates the systematic minimization of "
            "convex objective functions over convex feasible regions. "
            "Algorithmic convergence guarantees rely on mathematical "
            "characterizations of optimality conditions and duality theory."
        )
        m = compute_metrics(complex_text)
        assert m.flesch_kincaid_grade > 12  # graduate-level reading

    def test_paragraphs_counted(self):
        text = "First paragraph here.\n\nSecond paragraph follows."
        m = compute_metrics(text)
        assert m.paragraph_count == 2

    def test_to_dict_round_trips_keys(self):
        m = compute_metrics("Hello world.")
        d = m.to_dict()
        assert "word_count" in d
        assert "flesch_reading_ease" in d
        assert d["word_count"] == 2
