"""Tests for infrastructure/llm/review/metrics.py.

Tests dataclasses and estimate_tokens with real data. No mocks.
"""

from __future__ import annotations

from infrastructure.llm.review.metrics import (
    ReviewMetrics,
    ManuscriptInputMetrics,
    SessionMetrics,
    StreamingMetrics,
    estimate_tokens,
)


class TestEstimateTokens:
    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_four_chars_returns_one(self):
        assert estimate_tokens("abcd") == 1

    def test_eight_chars_returns_two(self):
        assert estimate_tokens("abcdefgh") == 2

    def test_longer_text(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_returns_int(self):
        assert isinstance(estimate_tokens("hello world"), int)

    def test_three_chars_returns_zero(self):
        # Floor division: 3 // 4 == 0
        assert estimate_tokens("abc") == 0

    def test_proportional_to_input_length(self):
        """Tokens must grow linearly with input length (4 chars/token)."""
        results = [estimate_tokens("a" * (n * 4)) for n in range(1, 6)]
        for i in range(1, len(results)):
            assert results[i] == results[i - 1] + 1, "Token estimate must be linearly proportional"

    def test_doubling_input_doubles_tokens(self):
        text = "hello world "
        single = estimate_tokens(text)
        double = estimate_tokens(text * 2)
        assert double == single * 2


class TestReviewMetrics:
    def test_default_values(self):
        m = ReviewMetrics()
        assert m.input_chars == 0
        assert m.output_chars == 0
        assert m.generation_time_seconds == 0.0
        assert m.preview == ""

    def test_can_set_fields(self):
        m = ReviewMetrics(input_chars=100, output_chars=200, generation_time_seconds=1.5)
        assert m.input_chars == 100
        assert m.output_chars == 200
        assert m.generation_time_seconds == 1.5


class TestManuscriptInputMetrics:
    def test_default_values(self):
        m = ManuscriptInputMetrics()
        assert m.total_chars == 0
        assert m.truncated is False

    def test_truncated_flag(self):
        m = ManuscriptInputMetrics(truncated=True, truncated_chars=500)
        assert m.truncated is True
        assert m.truncated_chars == 500


class TestSessionMetrics:
    def test_default_manuscript_is_fresh(self):
        s = SessionMetrics()
        assert isinstance(s.manuscript, ManuscriptInputMetrics)
        assert s.manuscript.total_chars == 0

    def test_reviews_dict_is_empty_by_default(self):
        s = SessionMetrics()
        assert s.reviews == {}

    def test_can_add_review(self):
        s = SessionMetrics()
        s.reviews["quality_review"] = ReviewMetrics(output_chars=300)
        assert "quality_review" in s.reviews

    def test_multiple_reviews_independently_tracked(self):
        s = SessionMetrics()
        s.reviews["review_a"] = ReviewMetrics(output_chars=100)
        s.reviews["review_b"] = ReviewMetrics(output_chars=200)
        assert s.reviews["review_a"].output_chars == 100
        assert s.reviews["review_b"].output_chars == 200
        assert len(s.reviews) == 2

    def test_total_output_chars_from_all_reviews(self):
        s = SessionMetrics()
        s.reviews["r1"] = ReviewMetrics(output_chars=50)
        s.reviews["r2"] = ReviewMetrics(output_chars=75)
        total = sum(r.output_chars for r in s.reviews.values())
        assert total == 125


class TestStreamingMetrics:
    def test_default_values(self):
        m = StreamingMetrics()
        assert m.chunk_count == 0
        assert m.error_count == 0
        assert m.partial_response_saved is False

    def test_timing_fields(self):
        m = StreamingMetrics(first_chunk_time=0.1, last_chunk_time=2.3)
        assert m.first_chunk_time == 0.1
        assert m.last_chunk_time == 2.3
