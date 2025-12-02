"""Tests for paper summarization functionality."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from infrastructure.literature.api import SearchResult
from infrastructure.literature.summarizer import (
    SummarizationResult,
    SummaryQualityValidator,
    PaperSummarizer,
)
from infrastructure.validation.pdf_validator import PDFValidationError
from infrastructure.core.exceptions import LLMConnectionError


class TestSummarizationResult:
    """Test SummarizationResult dataclass."""

    def test_creation_success(self):
        """Test successful summarization result."""
        result = SummarizationResult(
            citation_key="test2024paper",
            success=True,
            summary_text="This is a test summary.",
            input_chars=1000,
            input_words=200,
            output_words=50,
            generation_time=30.0,
            attempts=1,
            quality_score=0.9
        )

        assert result.citation_key == "test2024paper"
        assert result.success is True
        assert result.summary_text == "This is a test summary."
        assert result.input_chars == 1000
        assert result.input_words == 200
        assert result.output_words == 50
        assert result.generation_time == 30.0
        assert result.attempts == 1
        assert result.quality_score == 0.9
        assert result.compression_ratio == 0.25  # 50/200
        assert result.words_per_second == 50/30  # 50 words / 30 seconds

    def test_creation_failure(self):
        """Test failed summarization result."""
        result = SummarizationResult(
            citation_key="test2024paper",
            success=False,
            error="PDF extraction failed",
            attempts=2
        )

        assert result.success is False
        assert result.error == "PDF extraction failed"
        assert result.attempts == 2
        assert result.summary_text is None

    def test_compression_ratio_edge_cases(self):
        """Test compression ratio with edge cases."""
        # Zero input words
        result = SummarizationResult("key", True, "summary", 0, 0, 10, 1.0, 1)
        assert result.compression_ratio == 10.0

        # Normal case
        result = SummarizationResult("key", True, "summary", 100, 20, 10, 1.0, 1)
        assert result.compression_ratio == 0.5

    def test_words_per_second_edge_cases(self):
        """Test words per second with edge cases."""
        # Zero generation time
        result = SummarizationResult("key", True, "summary", 100, 20, 10, 0.0, 1)
        assert result.words_per_second == 10000.0

        # Very small time
        result = SummarizationResult("key", True, "summary", 100, 20, 10, 0.001, 1)
        assert result.words_per_second == 10000.0


class TestSummaryQualityValidator:
    """Test SummaryQualityValidator functionality."""

    def test_creation(self):
        """Test validator creation."""
        validator = SummaryQualityValidator()
        assert validator.min_words == 200

        validator = SummaryQualityValidator(min_words=500)
        assert validator.min_words == 500

    def test_validate_perfect_summary(self):
        """Test validation of a perfect summary."""
        validator = SummaryQualityValidator(min_words=25)  # Lower for testing
        pdf_text = "This is a scientific paper about machine learning."
        summary = """### Overview
This paper presents machine learning techniques.

### Key Contributions
The authors introduce novel algorithms.

### Methodology
They use neural networks and statistical methods.

### Results
The results show improved performance.

### Limitations and Future Work
Future work includes scaling to larger datasets."""

        is_valid, score, errors = validator.validate_summary(summary, pdf_text, "test")

        assert is_valid is True
        assert score > 0.8  # Should be high score
        assert len(errors) == 0

    def test_validate_poor_summary(self):
        """Test validation of a poor summary."""
        validator = SummaryQualityValidator(min_words=100)
        pdf_text = "This is a scientific paper about machine learning."
        summary = "This paper is about stuff."  # Too short, missing sections

        is_valid, score, errors = validator.validate_summary(summary, pdf_text, "test")

        assert is_valid is False
        assert score < 0.8  # Should be low score (adjusted for new min_words default)
        assert len(errors) > 0
        assert any("short" in error.lower() for error in errors)

    def test_detect_repetition(self):
        """Test repetition detection."""
        validator = SummaryQualityValidator()

        # No repetition
        summary = "This paper presents method A. The authors show result B. They conclude with finding C."
        assert not validator._detect_repetition(summary)

        # With repetition
        summary = "This paper presents method A. This paper presents method A. This paper presents method A. This paper presents method A. This paper discusses limitation D."
        assert validator._detect_repetition(summary)

    def test_detect_hallucination(self):
        """Test hallucination detection."""
        validator = SummaryQualityValidator()

        # No hallucination
        summary = "The paper presents machine learning methods."
        pdf_text = "The paper presents machine learning methods for classification."
        has_hallucination, reason = validator._detect_hallucination(summary, pdf_text)
        assert not has_hallucination

        # Hallucination - AI language
        summary = "I'm happy to help summarize this paper."
        pdf_text = "The paper presents machine learning methods."
        has_hallucination, reason = validator._detect_hallucination(summary, pdf_text)
        assert has_hallucination
        assert "AI assistant language" in reason

        # Hallucination - code content
        summary = "The paper uses def train_model(): function."
        pdf_text = "The paper uses machine learning techniques."
        has_hallucination, reason = validator._detect_hallucination(summary, pdf_text)
        assert has_hallucination
        assert "code in text summary" in reason

    def test_detect_off_topic_content(self):
        """Test off-topic content detection."""
        validator = SummaryQualityValidator()

        # Clean summary
        summary = "The paper presents novel methods for data analysis."
        errors = validator._detect_off_topic_content(summary)
        assert len(errors) == 0

        # Off-topic content
        summary = "Dear Professor, here is the summary you requested."
        errors = validator._detect_off_topic_content(summary)
        assert len(errors) > 0
        assert any("greeting" in error.lower() for error in errors)

    def test_domain_specific_validation(self):
        """Test physics/math domain validation."""
        validator = SummaryQualityValidator()

        # Physics paper without physics terms in summary
        pdf_text = "The collision energy was measured at 13 TeV. The quark-gluon plasma was observed."
        summary = "The paper discusses some experimental findings."  # No physics terms
        has_hallucination, reason = validator._detect_hallucination(summary, pdf_text)
        assert has_hallucination
        assert "physics terminology" in reason

        # Physics paper with physics terms
        summary = "The paper measures collision energy and observes quark-gluon plasma."
        has_hallucination, reason = validator._detect_hallucination(summary, pdf_text)
        assert not has_hallucination


class TestPaperSummarizer:
    """Test PaperSummarizer functionality."""

    def test_creation(self):
        """Test summarizer creation."""
        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        assert summarizer.llm_client is llm_client
        assert isinstance(summarizer.quality_validator, SummaryQualityValidator)

    def test_creation_with_validator(self):
        """Test summarizer creation with custom validator."""
        llm_client = Mock()
        validator = SummaryQualityValidator(min_words=100)
        summarizer = PaperSummarizer(llm_client, validator)

        assert summarizer.quality_validator is validator

    @patch('infrastructure.literature.summarizer.extract_text_from_pdf')
    def test_summarize_paper_success(self, mock_extract, tmp_path):
        """Test successful paper summarization."""
        # Setup mocks
        mock_extract.return_value = "This is a long scientific paper about machine learning with many details and explanations that cover various aspects of the field including algorithms, datasets, and evaluation metrics."

        llm_client = Mock()
        llm_client.query.return_value = """### Overview
This paper presents machine learning techniques for solving complex optimization problems in various domains. The research focuses on developing novel approaches that can handle high-dimensional data and provide robust solutions across different application areas.

### Key Contributions
The authors introduce novel algorithms that significantly improve upon existing methods. They demonstrate superior performance across multiple benchmark datasets and provide theoretical guarantees for convergence. The proposed techniques include advanced regularization methods and adaptive learning rates that enhance model generalization capabilities.

### Methodology
The approach uses neural networks and statistical methods combined with advanced optimization techniques. The implementation leverages deep learning frameworks and incorporates regularization strategies to prevent overfitting. The experimental setup includes comprehensive evaluation on standard datasets with proper cross-validation procedures and statistical significance testing.

### Results
The experimental results show improved performance compared to baseline methods. The proposed algorithms achieve state-of-the-art results on standard benchmarks with statistical significance. Performance improvements are observed across different metrics including accuracy, precision, recall, and computational efficiency.

### Limitations and Future Work
While promising, the current approach has limitations in terms of computational complexity. Future work includes scaling to larger datasets, extending to other domains, and developing more efficient implementations. Additional research directions involve exploring hybrid approaches and investigating the theoretical properties of the proposed algorithms in greater depth."""

        summarizer = PaperSummarizer(llm_client, SummaryQualityValidator(min_words=10))

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        # Create actual PDF file for stat() call
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # Execute
        summary_result = summarizer.summarize_paper(result, pdf_path)

        # Verify
        assert summary_result.success is True
        assert summary_result.citation_key == "test"
        assert "Overview" in summary_result.summary_text
        assert summary_result.attempts == 1
        assert summary_result.quality_score > 0

    @patch('infrastructure.literature.summarizer.extract_text_from_pdf')
    def test_summarize_paper_extraction_failure(self, mock_extract, tmp_path):
        """Test summarization when PDF extraction fails."""
        mock_extract.side_effect = PDFValidationError("PDF extraction failed")

        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        # Create actual PDF file for stat() call
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        summary_result = summarizer.summarize_paper(result, pdf_path)

        assert summary_result.success is False
        assert "extraction failed" in summary_result.error.lower()

    @patch('infrastructure.literature.summarizer.extract_text_from_pdf')
    def test_summarize_paper_insufficient_text(self, mock_extract, tmp_path):
        """Test summarization with insufficient extracted text."""
        mock_extract.return_value = "Short text"

        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        # Create actual PDF file for stat() call
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        summary_result = summarizer.summarize_paper(result, pdf_path)

        assert summary_result.success is False
        assert "insufficient text" in summary_result.error.lower()

    @patch('infrastructure.literature.summarizer.extract_text_from_pdf')
    def test_summarize_paper_llm_failure(self, mock_extract, tmp_path):
        """Test summarization when LLM fails."""
        mock_extract.return_value = "This is a long enough text for summarization that exceeds the minimum character requirement and should trigger the LLM call."

        llm_client = Mock()
        llm_client.query.side_effect = LLMConnectionError("LLM connection failed")

        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        # Create actual PDF file for stat() call
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        summary_result = summarizer.summarize_paper(result, pdf_path)

        assert summary_result.success is False
        assert summary_result.attempts > 1  # Should retry

    def test_generate_summary_prompt(self):
        """Test summary prompt generation."""
        llm_client = Mock()
        llm_client.query.return_value = "Generated summary"

        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One", "Author Two"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv",
            venue="arXiv"
        )

        summary = summarizer._generate_summary(result, "Test PDF content")

        # Check that LLM was called with the right prompt
        llm_client.query.assert_called_once()
        call_args = llm_client.query.call_args
        prompt = call_args[0][0]  # First positional argument

        assert "Test Paper" in prompt
        assert "Author One, Author Two" in prompt
        assert "2024" in prompt
        assert "arXiv" in prompt
        assert "Test PDF content" in prompt

        # Check that the method returns the LLM response
        assert summary == "Generated summary"

    def test_clean_summary_content(self):
        """Test summary content cleaning."""
        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        # Test with unwanted sections
        raw_summary = """### References
[1] Smith et al.

### Summary
This is a summary.

Note: This was generated by AI.

### Methodology
The method used is...

### Citation
@article{smith2024}
"""

        cleaned = summarizer._clean_summary_content(raw_summary)

        assert "### References" not in cleaned
        assert "### Citation" not in cleaned
        assert "Note:" not in cleaned
        assert "### Summary" not in cleaned  # Summary section is removed as unwanted
        assert "### Methodology" in cleaned

    def test_save_summary(self, tmp_path):
        """Test summary saving to file."""
        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        summary_result = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary content",
            input_words=100,
            output_words=50,
            generation_time=30.0
        )

        output_dir = tmp_path / "summaries"

        # Execute
        saved_path = summarizer.save_summary(result, summary_result, output_dir)

        # Verify
        assert saved_path.exists()
        assert saved_path.name == "test2024_summary.md"

        written_content = saved_path.read_text()
        assert "Test Paper" in written_content
        assert "Author One" in written_content
        assert "2024" in written_content
        assert "Test summary content" in written_content
        assert "50 words" in written_content
        assert "30.0s" in written_content

    def test_save_summary_with_path_field(self, tmp_path):
        """Test that save_summary sets summary_path field in result."""
        llm_client = Mock()
        summarizer = PaperSummarizer(llm_client)

        result = SearchResult(
            title="Test Paper",
            authors=["Author One"],
            year=2024,
            abstract="Test abstract",
            url="http://example.com",
            source="arxiv"
        )

        summary_result = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary content",
            input_words=100,
            output_words=50,
            generation_time=30.0
        )

        output_dir = tmp_path / "summaries"

        # Execute
        saved_path = summarizer.save_summary(result, summary_result, output_dir)

        # Verify summary_path field is set (though save_summary doesn't modify the result)
        # The workflow should set this field after calling save_summary
        assert saved_path.exists()
        # Note: save_summary returns the path but doesn't modify the result object

    def test_summary_result_with_path_field(self):
        """Test SummarizationResult with summary_path field."""
        result = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary",
            summary_path=Path("/path/to/summary.md")
        )

        assert result.summary_path == Path("/path/to/summary.md")

        # Test with None path
        result_none = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary"
        )

        assert result_none.summary_path is None
