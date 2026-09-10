"""Tests for the LLM validation similarity machinery.

Covers: _normalize_for_comparison, _jaccard_similarity, _tf_cosine_similarity,
_sequence_similarity, plus the composite similarity behavior via the public
repetition-detection API.

No mocks used -- all tests use real data and computations.
"""

from __future__ import annotations

from infrastructure.llm.validation.repetition import detect_repetition
from infrastructure.llm.validation.similarity import (
    _normalize_for_comparison,
    _jaccard_similarity,
    _tf_cosine_similarity,
    _sequence_similarity,
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


class TestCompositeSimilarityViaDetection:
    """The composite similarity drives duplicate detection through the public API.

    The similarity module is internal (its docstring forbids direct imports),
    so the composite behavior is exercised via ``detect_repetition`` threshold
    boundaries: a distinct second section is reported as a duplicate iff the
    pairwise similarity reaches the configured threshold.
    """

    @staticmethod
    def _overlap_text() -> str:
        first = ("the cat sat on the mat " * 5).strip()
        second = ("the dog sat on the mat " * 5).strip()
        return f"## Section\n{first}\n\n## Section\n{second}"

    def test_degenerate_input_reports_no_repetition(self):
        found, examples, ratio = detect_repetition("Short.")
        assert found is False
        assert examples == []
        assert ratio == 1.0

    def test_jaccard_method_scores_partial_overlap(self):
        result = detect_repetition(self._overlap_text(), similarity_threshold=0.5, similarity_method="jaccard")
        assert result.examples
        result = detect_repetition(self._overlap_text(), similarity_threshold=0.99, similarity_method="jaccard")
        assert result.examples == []

    def test_tfidf_method_scores_partial_overlap(self):
        result = detect_repetition(self._overlap_text(), similarity_threshold=0.01, similarity_method="tfidf")
        assert result.examples
        result = detect_repetition(self._overlap_text(), similarity_threshold=0.99, similarity_method="tfidf")
        assert result.examples == []

    def test_hybrid_method_separates_similar_from_disjoint(self):
        result = detect_repetition(self._overlap_text(), similarity_threshold=0.3, similarity_method="hybrid")
        assert result.examples

        disjoint_first = ("quantum physics experiments in laboratory settings " * 4).strip()
        disjoint_second = ("culinary arts and pastry making techniques " * 4).strip()
        disjoint = f"## Section\n{disjoint_first}\n\n## Section\n{disjoint_second}"
        result = detect_repetition(disjoint, similarity_threshold=0.5, similarity_method="hybrid")
        assert result.examples == []

    def test_default_method_is_hybrid(self):
        default = detect_repetition(self._overlap_text(), similarity_threshold=0.3)
        explicit = detect_repetition(self._overlap_text(), similarity_threshold=0.3, similarity_method="hybrid")
        assert default.examples == explicit.examples
