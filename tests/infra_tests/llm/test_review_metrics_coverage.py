"""Tests for infrastructure.llm.review.metrics — comprehensive coverage."""

from infrastructure.llm.review.metrics import (
    ReviewMetrics,
    ManuscriptInputMetrics,
    SessionMetrics,
    StreamingMetrics,
    estimate_tokens,
)


class TestReviewMetrics:
    def test_defaults(self):
        m = ReviewMetrics()
        assert m.input_chars == 0
        assert m.input_words == 0
        assert m.input_tokens_est == 0
        assert m.output_chars == 0
        assert m.output_words == 0
        assert m.output_tokens_est == 0
        assert m.generation_time_seconds == 0.0
        assert m.preview == ""

    def test_custom_values(self):
        m = ReviewMetrics(
            input_chars=1000,
            input_words=200,
            input_tokens_est=250,
            output_chars=5000,
            output_words=1000,
            output_tokens_est=1250,
            generation_time_seconds=3.5,
            preview="This is a preview...",
        )
        assert m.input_chars == 1000
        assert m.output_words == 1000
        assert m.generation_time_seconds == 3.5


class TestManuscriptInputMetrics:
    def test_defaults(self):
        m = ManuscriptInputMetrics()
        assert m.total_chars == 0
        assert m.total_words == 0
        assert m.total_tokens_est == 0
        assert m.truncated is False
        assert m.truncated_chars == 0

    def test_truncated(self):
        m = ManuscriptInputMetrics(
            total_chars=100000,
            total_words=20000,
            total_tokens_est=25000,
            truncated=True,
            truncated_chars=50000,
        )
        assert m.truncated is True
        assert m.truncated_chars == 50000


class TestSessionMetrics:
    def test_defaults(self):
        m = SessionMetrics()
        assert isinstance(m.manuscript, ManuscriptInputMetrics)
        assert m.reviews == {}
        assert m.total_generation_time == 0.0
        assert m.model_name == ""
        assert m.max_input_length == 0
        assert m.warmup_tokens_per_sec == 0.0

    def test_with_reviews(self):
        m = SessionMetrics(
            model_name="gemma:4b",
            max_input_length=100000,
        )
        m.reviews["executive_summary"] = ReviewMetrics(output_words=500)
        m.reviews["quality_review"] = ReviewMetrics(output_words=300)
        assert len(m.reviews) == 2


class TestStreamingMetrics:
    def test_defaults(self):
        m = StreamingMetrics()
        assert m.chunk_count == 0
        assert m.total_chars == 0
        assert m.total_tokens_est == 0
        assert m.streaming_time_seconds == 0.0
        assert m.chunks_per_second == 0.0
        assert m.bytes_per_second == 0.0
        assert m.error_count == 0
        assert m.partial_response_saved is False
        assert m.first_chunk_time == 0.0
        assert m.last_chunk_time == 0.0

    def test_custom_values(self):
        m = StreamingMetrics(
            chunk_count=100,
            total_chars=5000,
            total_tokens_est=1250,
            streaming_time_seconds=2.5,
            chunks_per_second=40.0,
            bytes_per_second=2000.0,
            first_chunk_time=0.1,
            last_chunk_time=2.5,
        )
        assert m.chunks_per_second == 40.0


class TestEstimateTokens:
    def test_basic(self):
        text = "Hello world this is a test"
        tokens = estimate_tokens(text)
        assert tokens > 0

    def test_empty(self):
        tokens = estimate_tokens("")
        assert tokens == 0

    def test_long_text(self):
        text = "word " * 10000
        tokens = estimate_tokens(text)
        assert tokens > 0
        # Roughly 4 chars per token, so 50000 chars ~ 12500 tokens
        assert 5000 < tokens < 25000
