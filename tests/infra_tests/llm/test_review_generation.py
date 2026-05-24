"""Tests for infrastructure.llm.review.generation — pure function coverage."""


from infrastructure.llm.review.generation import (
    extract_manuscript_text,
    _build_off_topic_retry_prompt,
    _deduplicate_response,
)


class TestExtractManuscriptText:
    def test_nonexistent_pdf(self, tmp_path):
        missing = tmp_path / "nonexistent.pdf"
        text, metrics = extract_manuscript_text(missing)
        assert text is None
        assert metrics.total_chars == 0

    def test_nonexistent_string_path(self, tmp_path):
        text, metrics = extract_manuscript_text(str(tmp_path / "nope.pdf"))
        assert text is None

    def test_real_pdf(self, tmp_path):
        # Create a minimal PDF with reportlab
        try:
            from reportlab.pdfgen import canvas as rl_canvas
        except ImportError:
            import pytest
            pytest.skip("reportlab not installed")

        pdf_path = tmp_path / "test.pdf"
        c = rl_canvas.Canvas(str(pdf_path))
        c.drawString(100, 700, "Hello World Test Content")
        c.save()

        text, metrics = extract_manuscript_text(pdf_path)
        assert text is not None
        assert metrics.total_chars > 0
        assert metrics.total_words > 0
        assert metrics.total_tokens_est > 0
        assert metrics.truncated is False

    def test_truncation(self, tmp_path):
        try:
            from reportlab.pdfgen import canvas as rl_canvas
        except ImportError:
            import pytest
            pytest.skip("reportlab not installed")

        pdf_path = tmp_path / "big.pdf"
        c = rl_canvas.Canvas(str(pdf_path))
        # Write enough text to exceed a small limit
        for i in range(50):
            c.drawString(50, 700 - i * 10, f"Line {i} with some content to generate text")
        c.save()

        text, metrics = extract_manuscript_text(pdf_path, max_input_length=50)
        assert text is not None
        assert metrics.truncated is True
        assert metrics.truncated_chars == 50
        assert "[... truncated" in text


class TestBuildOffTopicRetryPrompt:
    def test_no_off_topic(self):
        prompt = "Review this paper"
        result = _build_off_topic_retry_prompt(prompt, had_off_topic=False)
        assert result == prompt

    def test_off_topic_adds_prefix(self):
        prompt = "Review this paper"
        result = _build_off_topic_retry_prompt(prompt, had_off_topic=True)
        assert "IMPORTANT" in result
        assert prompt in result


class TestDeduplicateResponse:
    def test_no_dedup_needed(self):
        response = "This is a unique response with diverse content about many different topics."
        result = _deduplicate_response(response, "fallback")
        assert result == response

    def test_heavily_repetitive(self):
        # Create a response that repeats the same sentence many times
        sentence = "The methodology is sound and well-described. "
        response = sentence * 100
        best = "This is the best response."
        result = _deduplicate_response(response, best)
        # Either deduped or falls back to best
        assert isinstance(result, str)
        assert len(result) > 0

    def test_moderate_repetition_kept(self):
        # Some repetition but not severe
        parts = [f"Point {i}: This is a unique observation about topic {i}." for i in range(20)]
        response = "\n".join(parts)
        result = _deduplicate_response(response, "fallback")
        assert result == response  # Should keep original
