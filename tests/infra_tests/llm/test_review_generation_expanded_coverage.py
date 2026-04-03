"""Tests for infrastructure.llm.review.generation — expanded coverage for helpers."""



from infrastructure.llm.review.generation import (
    extract_manuscript_text,
    _build_off_topic_retry_prompt,
    _deduplicate_response,
)


class TestExtractManuscriptText:
    def test_file_not_found(self, tmp_path):
        text, metrics = extract_manuscript_text(tmp_path / "nonexistent.pdf")
        assert text is None
        assert metrics.total_chars == 0

    def test_file_not_found_str_path(self, tmp_path):
        text, metrics = extract_manuscript_text(str(tmp_path / "nonexistent.pdf"))
        assert text is None

    def test_valid_pdf(self, tmp_path):
        """Create a real PDF and extract text."""
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "paper.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, "This is a test manuscript about quantum computing")
        c.save()

        text, metrics = extract_manuscript_text(pdf_path)
        assert text is not None
        assert metrics.total_chars > 0
        assert metrics.total_words > 0
        assert metrics.total_tokens_est > 0
        assert metrics.truncated is False

    def test_truncation(self, tmp_path):
        """Test truncation when text exceeds max_input_length."""
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "long.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 8)
        # Write lots of text
        for i in range(100):
            y = 750 - (i * 7)
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(50, y, f"Line {i}: " + "word " * 20)
        c.save()

        text, metrics = extract_manuscript_text(pdf_path, max_input_length=100)
        assert text is not None
        assert metrics.truncated is True
        assert metrics.truncated_chars == 100
        assert "truncated" in text.lower()

    def test_no_truncation_when_unlimited(self, tmp_path):
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "paper.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 700, "Short content")
        c.save()

        text, metrics = extract_manuscript_text(pdf_path, max_input_length=0)
        assert text is not None
        assert metrics.truncated is False


class TestBuildOffTopicRetryPrompt:
    def test_no_off_topic(self):
        result = _build_off_topic_retry_prompt("Original prompt", had_off_topic=False)
        assert result == "Original prompt"

    def test_with_off_topic(self):
        result = _build_off_topic_retry_prompt("Original prompt", had_off_topic=True)
        assert "IMPORTANT" in result or "Original prompt" in result
        # Should contain the original prompt
        assert "Original prompt" in result


class TestDeduplicateResponse:
    def test_no_repetition(self):
        response = "This is a unique response with different content in each part."
        result = _deduplicate_response(response, "fallback")
        assert result == response

    def test_highly_repetitive(self):
        # Create a response with extreme repetition
        repeated = "The same sentence repeated. " * 50
        result = _deduplicate_response(repeated, "best fallback response")
        # Should return either deduped version or best_response
        assert len(result) > 0

    def test_empty_response(self):
        result = _deduplicate_response("", "fallback")
        # Empty string should pass through (no repetition detected)
        assert result == ""

    def test_short_response(self):
        result = _deduplicate_response("Short text", "fallback")
        assert result == "Short text"
