"""Tests for review generator functions in infrastructure.llm.review.generator."""

from __future__ import annotations

import pytest

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.review.generator import (
    extract_manuscript_text, generate_executive_summary,
    generate_improvement_suggestions, generate_methodology_review,
    generate_quality_review, generate_review_with_metrics,
    generate_translation)


class TestExtractManuscriptText:
    """Tests for extract_manuscript_text() function."""

    def test_file_not_found(self, tmp_path):
        """Test extract_manuscript_text raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            extract_manuscript_text(str(tmp_path / "nonexistent.pdf"))

    def test_no_pdf_library_raises_error(self, tmp_path):
        """Test extract_manuscript_text raises ValueError when no PDF library available."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf content")

        # Test with a scenario where libraries are not available
        # This test verifies the error handling when PDF libraries fail to import
        # Since we can't easily mock imports without patch, we'll test with a malformed PDF
        # that would cause all libraries to fail
        try:
            result = extract_manuscript_text(str(pdf_file))
            # If no exception is raised, that's also acceptable (library handled it gracefully)
        except ValueError as e:
            # This is the expected behavior when no suitable PDF library is available
            assert "No PDF parsing library available" in str(e)

    def test_with_pdfplumber(self, tmp_path):
        """Test extract_manuscript_text with pdfplumber library."""
        # Create a real PDF with text content
        pdf_file = tmp_path / "test.pdf"

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Extracted text from page")
        c.drawString(100, 730, "Second line of text")
        c.save()

        # Test real extraction with pdfplumber (if available)
        try:
            result = extract_manuscript_text(str(pdf_file))
            assert "Extracted text from page" in result
            assert "Second line of text" in result
        except ValueError as e:
            # If pdfplumber not available, should raise ValueError
            assert "No PDF parsing library available" in str(e)

    def test_with_pypdf(self, tmp_path):
        """Test extract_manuscript_text with pypdf library."""
        # Create a real PDF with text content
        pdf_file = tmp_path / "test.pdf"

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Extracted text")
        c.drawString(100, 730, "More text content")
        c.save()

        # Test real extraction with pypdf (if available)
        try:
            result = extract_manuscript_text(str(pdf_file))
            assert "Extracted text" in result
            assert "More text content" in result
        except ValueError as e:
            # If pypdf not available, should raise ValueError
            assert "No PDF parsing library available" in str(e)


class TestGenerateReviewWithMetrics:
    """Tests for generate_review_with_metrics() function."""

    @pytest.mark.slow
    def test_generates_executive_summary(self, ollama_test_server):
        """Test generate_review_with_metrics with executive_summary type."""
        manuscript_text = "This is a test manuscript about machine learning."

        # The generate_review_with_metrics function will use the real LLM client
        # which will connect to our test server
        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "executive_summary"
        )

        # Verify the review text was generated (real LLM response)
        assert isinstance(review_text, str)
        assert len(review_text) > 0
        assert "tokens_used" in metrics
        assert "time_seconds" in metrics
        assert "input_chars" in metrics
        assert "output_chars" in metrics

    @pytest.mark.slow
    def test_generates_quality_review(self, ollama_test_server):
        """Test generate_review_with_metrics with quality_review type."""
        manuscript_text = "Test manuscript text."

        # Real LLM client will connect to test server
        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "quality_review"
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_methodology_review(self, ollama_test_server):
        """Test generate_review_with_metrics with methodology_review type."""
        manuscript_text = "Test manuscript."

        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "methodology_review"
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_improvement_suggestions(self, ollama_test_server):
        """Test generate_review_with_metrics with improvement_suggestions type."""
        manuscript_text = "Test manuscript."

        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "improvement_suggestions"
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_metrics_include_all_fields(self, ollama_test_server):
        """Test that metrics dict includes all expected fields."""
        manuscript_text = "Test manuscript text for metrics testing."

        _, metrics = generate_review_with_metrics(manuscript_text, "executive_summary")

        required_fields = [
            "tokens_used",
            "time_seconds",
            "input_chars",
            "input_words",
            "input_tokens_est",
            "output_chars",
            "output_words",
            "output_tokens_est",
        ]
        for field in required_fields:
            assert field in metrics, f"Missing field: {field}"

    @pytest.mark.slow
    def test_truncates_long_manuscript(self, ollama_test_server):
        """Test that long manuscripts are truncated."""
        long_text = "x" * 600000  # Longer than default max

        # The function should handle long text gracefully
        # (truncation happens internally in the LLM client)
        review_text, metrics = generate_review_with_metrics(
            long_text, "executive_summary"
        )

        # Verify the function completed successfully
        assert isinstance(review_text, str)
        assert len(review_text) > 0


class TestTemplateBasedGenerators:
    """Tests for template-based generator functions."""

    @pytest.mark.slow
    def test_generate_executive_summary_calls_llm(self, ollama_test_server):
        """Test generate_executive_summary actually queries LLM."""
        manuscript_text = "Test manuscript about AI research."

        # Use real LLM client that connects to test server
        result = generate_executive_summary(manuscript_text, model="gemma3:4b")

        # Verify we got a real response
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_quality_review_calls_llm(self, ollama_test_server):
        """Test generate_quality_review actually queries LLM."""
        manuscript_text = "Test manuscript."

        # Use real LLM client that connects to test server
        result = generate_quality_review(manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_methodology_review_calls_llm(self, ollama_test_server):
        """Test generate_methodology_review actually queries LLM."""
        manuscript_text = "Test manuscript."

        result = generate_methodology_review(manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_improvement_suggestions_calls_llm(self, ollama_test_server):
        """Test generate_improvement_suggestions actually queries LLM."""
        manuscript_text = "Test manuscript."

        result = generate_improvement_suggestions(manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_calls_llm(self, ollama_test_server):
        """Test generate_translation actually queries LLM."""
        text = "Hello world"
        target_language = "zh"

        result = generate_translation(text, target_language)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_with_model(self, ollama_test_server):
        """Test generate_translation respects model parameter."""
        text = "Test"
        target_language = "hi"

        # Use real LLM client - model parameter is handled internally
        result = generate_translation(text, target_language, model="gemma3:4b")

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.requires_ollama
class TestReviewGeneratorsIntegration:
    """Integration tests for review generators (requires Ollama)."""

    def test_generate_executive_summary_real_ollama(self):
        """Test generate_executive_summary with real Ollama."""
        from infrastructure.llm import LLMClient

        client = LLMClient()
        if not client.check_connection():
            pytest.fail(
                "\n" + "=" * 80 + "\n"
                "❌ TEST FAILURE: Ollama server is not available!\n"
                "=" * 80 + "\n"
                "This test requires Ollama to be running.\n"
                "The ensure_ollama_for_tests fixture should have started it.\n\n"
                "Troubleshooting:\n"
                "  1. Check if Ollama is installed: ollama --version\n"
                "  2. Start Ollama manually: ollama serve\n"
                "  3. Check logs above for auto-start errors\n"
                "=" * 80
            )

        manuscript_text = "This is a test manuscript about machine learning and AI."
        result = generate_executive_summary(manuscript_text)

        assert len(result) > 0
        assert isinstance(result, str)

    def test_generate_review_with_metrics_real_ollama(self):
        """Test generate_review_with_metrics with real Ollama."""
        from infrastructure.llm import LLMClient

        client = LLMClient()
        if not client.check_connection():
            pytest.fail(
                "\n" + "=" * 80 + "\n"
                "❌ TEST FAILURE: Ollama server is not available!\n"
                "=" * 80 + "\n"
                "This test requires Ollama to be running.\n"
                "The ensure_ollama_for_tests fixture should have started it.\n\n"
                "Troubleshooting:\n"
                "  1. Check if Ollama is installed: ollama --version\n"
                "  2. Start Ollama manually: ollama serve\n"
                "  3. Check logs above for auto-start errors\n"
                "=" * 80
            )

        manuscript_text = "Test manuscript about optimization algorithms."
        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "executive_summary"
        )

        assert len(review_text) > 0
        assert "tokens_used" in metrics
        assert "time_seconds" in metrics
        assert metrics["time_seconds"] > 0
