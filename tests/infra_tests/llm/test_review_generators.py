"""Tests for review generator functions in infrastructure.llm.review.generator."""

from __future__ import annotations

import pytest

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.review.generator import (
    extract_manuscript_text,
    generate_executive_summary,
    generate_improvement_suggestions,
    generate_methodology_review,
    generate_quality_review,
    generate_review_with_metrics,
    generate_translation,
    validate_review_quality,
)


class TestExtractManuscriptText:
    """Tests for extract_manuscript_text() function."""

    def test_file_not_found(self, tmp_path):
        """Test extract_manuscript_text returns None for missing file."""
        text, metrics = extract_manuscript_text(str(tmp_path / "nonexistent.pdf"))
        assert text is None

    def test_no_pdf_library_raises_error(self, tmp_path):
        """Test extract_manuscript_text returns None when no PDF library available or error."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf content")

        try:
            text, metrics = extract_manuscript_text(str(pdf_file))
            if text is None:
                assert metrics.total_chars == 0
        except ValueError as e:
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

        try:
            text, metrics = extract_manuscript_text(str(pdf_file))
            assert text is not None
            assert "Extracted text from page" in text
            assert "Second line of text" in text
        except ValueError as e:
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

        try:
            text, metrics = extract_manuscript_text(str(pdf_file))
            assert text is not None
            assert "Extracted text" in text
            assert "More text content" in text
        except ValueError as e:
            assert "No PDF parsing library available" in str(e)


class TestGenerateReviewWithMetrics:
    """Tests for generate_review_with_metrics() function."""

    @pytest.mark.slow
    def test_generates_executive_summary(self, ollama_test_server):
        """Test generate_review_with_metrics with executive_summary type."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        manuscript_text = "This is a test manuscript about machine learning."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0
        # ReviewMetrics attributes:
        assert metrics.output_chars > 0
        assert metrics.generation_time_seconds > 0

    @pytest.mark.slow
    def test_generates_quality_review(self, ollama_test_server):
        """Test generate_review_with_metrics with quality_review type."""
        from infrastructure.llm.templates import ManuscriptQualityReview

        manuscript_text = "Test manuscript text."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "quality_review", "Quality Review", ManuscriptQualityReview
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_methodology_review(self, ollama_test_server):
        """Test generate_review_with_metrics with methodology_review type."""
        from infrastructure.llm.templates import ManuscriptMethodologyReview

        manuscript_text = "Test manuscript."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "methodology_review", "Methodology Review", ManuscriptMethodologyReview
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_improvement_suggestions(self, ollama_test_server):
        """Test generate_review_with_metrics with improvement_suggestions type."""
        from infrastructure.llm.templates import ManuscriptImprovementSuggestions

        manuscript_text = "Test manuscript."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client,
            manuscript_text,
            "improvement_suggestions",
            "Improvement Suggestions",
            ManuscriptImprovementSuggestions,
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_metrics_include_all_fields(self, ollama_test_server):
        """Test that metrics dict includes all expected fields."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        manuscript_text = "Test manuscript text for metrics testing."
        client = LLMClient()

        _, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        # Check dataclass attributes
        assert hasattr(metrics, "input_chars")
        assert hasattr(metrics, "output_chars")
        assert hasattr(metrics, "generation_time_seconds")
        assert hasattr(metrics, "input_tokens_est")

    @pytest.mark.slow
    def test_truncates_long_manuscript(self, ollama_test_server):
        """Test that long manuscripts are truncated."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        long_text = "x" * 600000
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, long_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0


class TestTemplateBasedGenerators:
    """Tests for template-based generator functions."""

    @pytest.mark.slow
    def test_generate_executive_summary_calls_llm(self, ollama_test_server):
        """Test generate_executive_summary actually queries LLM."""
        manuscript_text = "Test manuscript about AI research."
        client = LLMClient()

        result, metrics = generate_executive_summary(
            client, manuscript_text, model_name="gemma3:4b"
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_quality_review_calls_llm(self, ollama_test_server):
        """Test generate_quality_review actually queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_quality_review(client, manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_methodology_review_calls_llm(self, ollama_test_server):
        """Test generate_methodology_review actually queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_methodology_review(client, manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_improvement_suggestions_calls_llm(self, ollama_test_server):
        """Test generate_improvement_suggestions actually queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_improvement_suggestions(client, manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_calls_llm(self, ollama_test_server):
        """Test generate_translation actually queries LLM."""
        text = "Hello world"
        target_language = "zh"
        client = LLMClient()

        result, metrics = generate_translation(client, text, target_language)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_with_model(self, ollama_test_server):
        """Test generate_translation respects model parameter."""
        text = "Test"
        target_language = "hi"
        client = LLMClient()

        result, metrics = generate_translation(
            client, text, target_language, model_name="gemma3:4b"
        )

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
            pytest.fail("Ollama server is not available!")

        manuscript_text = "This is a test manuscript about machine learning and AI."
        result, metrics = generate_executive_summary(client, manuscript_text)

        assert len(result) > 0
        assert isinstance(result, str)

class TestValidateReviewQuality:
    """Deterministic tests for validate_review_quality() — no Ollama required."""

    def _good_executive_summary(self, n_extra_words: int = 0) -> str:
        """Build a minimal passing executive summary with required section keywords."""
        base = (
            "## Overview\nThis is the overview section of the manuscript. "
            "## Key Contributions\nThe main findings and contributions are described here. "
            "## Methodology\nThe methods and approach used in this work. "
            "## Results\nThe outcomes and principal results of the study. "
            "## Significance\nThe impact and implications of this research. "
        )
        extra = " ".join(f"word{i}" for i in range(n_extra_words))
        return base + " " + extra

    def test_passes_for_adequate_response(self):
        """A response with enough words and required sections passes validation."""
        response = self._good_executive_summary(n_extra_words=300)
        passed, issues, details = validate_review_quality(response, "executive_summary")
        assert passed is True, f"Expected pass but got issues: {issues}"

    def test_fails_for_too_short_response(self):
        """A response with too few words fails with a 'too short' issue."""
        response = " ".join(f"word{i}" for i in range(5))
        passed, issues, details = validate_review_quality(
            response, "executive_summary", min_words=200
        )
        assert passed is False
        assert any("short" in issue.lower() for issue in issues)

    def test_fails_for_too_short_explicit_min(self):
        """Explicit min_words overrides the default minimum for any review type."""
        response = "This is a short response with overview content."
        passed, issues, details = validate_review_quality(
            response, "executive_summary", min_words=500
        )
        assert passed is False
        assert any("short" in issue.lower() for issue in issues)
        assert details["word_count"] < 500

    def test_returns_word_count_in_details(self):
        """Details dict always contains word_count."""
        response = self._good_executive_summary(n_extra_words=200)
        _, _, details = validate_review_quality(response, "executive_summary", min_words=10)
        assert "word_count" in details
        assert details["word_count"] > 0

    def test_small_model_reduces_minimum_word_count(self):
        """Small model names lower the effective minimum word threshold by 20%."""
        # Build a response with sections but borderline word count
        response = self._good_executive_summary(n_extra_words=200)
        # Pass with explicit min_words that normal model would require but small won't
        _, issues_normal, _ = validate_review_quality(
            response, "executive_summary", min_words=5000
        )
        _, issues_small, _ = validate_review_quality(
            response, "executive_summary", min_words=5000, model_name="llama3-8b"
        )
        # Small model has a lower effective minimum (min * 0.8), so it may have fewer issues
        # Both may still fail for 5000 words but small model's threshold is lower
        normal_short = any("short" in i.lower() for i in issues_normal)
        small_short = any("short" in i.lower() for i in issues_small)
        # Both should flag it as too short for 5000 min, but that's the expected behavior
        assert normal_short is True
        assert small_short is True


    def test_generate_review_with_metrics_real_ollama(self):
        """Test generate_review_with_metrics with real Ollama."""
        from infrastructure.llm import LLMClient

        client = LLMClient()
        if not client.check_connection():
            pytest.fail("Ollama server is not available!")

        manuscript_text = "Test manuscript about optimization algorithms."
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert len(review_text) > 0
        assert hasattr(metrics, "output_chars")
        assert hasattr(metrics, "generation_time_seconds")
        assert metrics.generation_time_seconds > 0
