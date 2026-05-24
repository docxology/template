"""Tests for infrastructure/llm/validation/similarity.py.

Covers: _normalize_for_comparison, _jaccard_similarity, _tf_cosine_similarity,
_sequence_similarity, _calculate_similarity.

No mocks used -- all tests use real data and computations.
"""

from __future__ import annotations

from infrastructure.llm.validation.similarity import (
    _normalize_for_comparison,
    _jaccard_similarity,
    _tf_cosine_similarity,
    _sequence_similarity,
    _calculate_similarity,
)


class TestNormalizeForComparison:
    """Test _normalize_for_comparison."""

    def test_lowercase(self):
        assert "hello world" in _normalize_for_comparison("Hello World")

    def test_removes_markdown(self):
        result = _normalize_for_comparison("## **Bold** _italic_ `code`")
        assert "#" not in result
        assert "*" not in result
        assert "_" not in result
        assert "`" not in result

    def test_normalizes_whitespace(self):
        result = _normalize_for_comparison("  too   many    spaces  ")
        assert "  " not in result

    def test_replaces_numbers(self):
        result = _normalize_for_comparison("Section 42 has 100 items")
        assert "42" not in result
        assert "100" not in result
        assert "N" in result


class TestJaccardSimilarity:
    """Test _jaccard_similarity."""

    def test_identical_texts(self):
        sim = _jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_completely_different(self):
        sim = _jaccard_similarity("cat dog bird", "car house tree")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = _jaccard_similarity("the cat sat", "the dog sat")
        assert 0.0 < sim < 1.0

    def test_empty_texts(self):
        assert _jaccard_similarity("", "hello") == 0.0
        assert _jaccard_similarity("hello", "") == 0.0
        assert _jaccard_similarity("", "") == 0.0


class TestTfCosineSimilarity:
    """Test _tf_cosine_similarity."""

    def test_identical_texts(self):
        sim = _tf_cosine_similarity("hello world test", "hello world test")
        assert abs(sim - 1.0) < 0.01

    def test_completely_different(self):
        sim = _tf_cosine_similarity("alpha beta gamma", "delta epsilon zeta")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = _tf_cosine_similarity("the quick brown fox", "the slow brown dog")
        assert 0.0 < sim < 1.0

    def test_empty_texts(self):
        assert _tf_cosine_similarity("", "hello") == 0.0
        assert _tf_cosine_similarity("hello", "") == 0.0


class TestSequenceSimilarity:
    """Test _sequence_similarity."""

    def test_identical_texts(self):
        text = "the quick brown fox jumps over the lazy dog"
        sim = _sequence_similarity(text, text)
        assert sim == 1.0

    def test_completely_different(self):
        sim = _sequence_similarity(
            "alpha beta gamma delta epsilon",
            "one two three four five",
        )
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = _sequence_similarity(
            "the quick brown fox jumps over",
            "the quick brown dog runs over",
        )
        assert 0.0 < sim < 1.0

    def test_short_texts(self):
        sim = _sequence_similarity("ab", "cd")
        assert sim == 0.0

    def test_empty_texts(self):
        assert _sequence_similarity("", "hello world test") == 0.0


class TestCalculateSimilarity:
    """Test _calculate_similarity."""

    def test_empty_texts(self):
        assert _calculate_similarity("", "hello") == 0.0
        assert _calculate_similarity("hello", "") == 0.0

    def test_jaccard_method(self):
        sim = _calculate_similarity(
            "the cat sat on the mat",
            "the dog sat on the mat",
            method="jaccard",
        )
        assert 0.0 < sim < 1.0

    def test_tfidf_method(self):
        sim = _calculate_similarity(
            "machine learning algorithms process data",
            "machine learning models analyze data",
            method="tfidf",
        )
        assert 0.0 < sim < 1.0

    def test_hybrid_method(self):
        sim = _calculate_similarity(
            "the quick brown fox jumps over the lazy dog",
            "the quick brown fox jumps over the lazy dog",
            method="hybrid",
        )
        assert sim > 0.9

    def test_different_texts_hybrid(self):
        sim = _calculate_similarity(
            "quantum physics experiments in laboratory settings",
            "culinary arts and pastry making techniques",
            method="hybrid",
        )
        assert sim < 0.5

    def test_default_method_is_hybrid(self):
        sim1 = _calculate_similarity("hello world test", "hello world test")
        sim2 = _calculate_similarity("hello world test", "hello world test", method="hybrid")
        assert abs(sim1 - sim2) < 0.01
