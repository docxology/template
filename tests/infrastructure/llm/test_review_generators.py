"""Tests for review generator functions in infrastructure.llm.review.generator."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

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
)


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
        
        # Mock all PDF libraries as unavailable by patching the import attempts
        import sys
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name in ('pdfplumber', 'pypdf', 'PyPDF2'):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ValueError, match="No PDF parsing library available"):
                extract_manuscript_text(str(pdf_file))
    
    def test_with_pdfplumber(self, tmp_path):
        """Test extract_manuscript_text with pdfplumber library."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf content")
        
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted text from page"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        
        # Create a mock module
        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open = MagicMock(return_value=mock_pdf)
        
        with patch.dict('sys.modules', {'pdfplumber': mock_pdfplumber}):
            result = extract_manuscript_text(str(pdf_file))
            assert result == "Extracted text from page"
    
    def test_with_pypdf(self, tmp_path):
        """Test extract_manuscript_text with pypdf library."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf content")
        
        # Mock pypdf
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted text"
        mock_reader.pages = [mock_page]
        
        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader = MagicMock(return_value=mock_reader)
        
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        
        with patch.dict('sys.modules', {'pypdf': mock_pypdf}):
            with patch('builtins.open', return_value=mock_file):
                result = extract_manuscript_text(str(pdf_file))
                assert result == "Extracted text"


class TestGenerateReviewWithMetrics:
    """Tests for generate_review_with_metrics() function."""
    
    def test_generates_executive_summary(self):
        """Test generate_review_with_metrics with executive_summary type."""
        manuscript_text = "This is a test manuscript about machine learning."
        
        with patch('infrastructure.llm.review.generator.generate_executive_summary') as mock_gen:
            mock_gen.return_value = "Executive summary text"
            
            review_text, metrics = generate_review_with_metrics(
                manuscript_text, "executive_summary"
            )
            
            assert review_text == "Executive summary text"
            assert "tokens_used" in metrics
            assert "time_seconds" in metrics
            assert "input_chars" in metrics
            assert "output_chars" in metrics
            mock_gen.assert_called_once()
    
    def test_generates_quality_review(self):
        """Test generate_review_with_metrics with quality_review type."""
        manuscript_text = "Test manuscript text."
        
        with patch('infrastructure.llm.review.generator.generate_quality_review') as mock_gen:
            mock_gen.return_value = "Quality review text"
            
            review_text, metrics = generate_review_with_metrics(
                manuscript_text, "quality_review"
            )
            
            assert review_text == "Quality review text"
            assert metrics["output_chars"] == len("Quality review text")
            mock_gen.assert_called_once()
    
    def test_generates_methodology_review(self):
        """Test generate_review_with_metrics with methodology_review type."""
        manuscript_text = "Test manuscript."
        
        with patch('infrastructure.llm.review.generator.generate_methodology_review') as mock_gen:
            mock_gen.return_value = "Methodology review"
            
            review_text, metrics = generate_review_with_metrics(
                manuscript_text, "methodology_review"
            )
            
            assert review_text == "Methodology review"
            mock_gen.assert_called_once()
    
    def test_generates_improvement_suggestions(self):
        """Test generate_review_with_metrics with improvement_suggestions type."""
        manuscript_text = "Test manuscript."
        
        with patch('infrastructure.llm.review.generator.generate_improvement_suggestions') as mock_gen:
            mock_gen.return_value = "Improvement suggestions"
            
            review_text, metrics = generate_review_with_metrics(
                manuscript_text, "improvement_suggestions"
            )
            
            assert review_text == "Improvement suggestions"
            mock_gen.assert_called_once()
    
    def test_metrics_include_all_fields(self):
        """Test that metrics dict includes all expected fields."""
        manuscript_text = "Test manuscript text for metrics testing."
        
        with patch('infrastructure.llm.review.generator.generate_executive_summary') as mock_gen:
            mock_gen.return_value = "Summary text"
            
            _, metrics = generate_review_with_metrics(
                manuscript_text, "executive_summary"
            )
            
            required_fields = [
                "tokens_used", "time_seconds", "input_chars", "input_words",
                "input_tokens_est", "output_chars", "output_words", "output_tokens_est"
            ]
            for field in required_fields:
                assert field in metrics, f"Missing field: {field}"
    
    def test_truncates_long_manuscript(self):
        """Test that long manuscripts are truncated."""
        long_text = "x" * 600000  # Longer than default max
        
        with patch('infrastructure.llm.review.generator.generate_executive_summary') as mock_gen:
            mock_gen.return_value = "Summary"
            
            generate_review_with_metrics(long_text, "executive_summary")
            
            # Check that truncation was applied
            call_args = mock_gen.call_args
            assert call_args is not None
            passed_text = call_args[0][0]
            assert len(passed_text) <= 500000  # Default max length


class TestTemplateBasedGenerators:
    """Tests for template-based generator functions."""
    
    def test_generate_executive_summary_calls_llm(self):
        """Test generate_executive_summary actually queries LLM."""
        manuscript_text = "Test manuscript about AI research."
        
        # Patch where LLMClient is imported (inside the function)
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "Generated executive summary"
            mock_client_class.return_value = mock_client
            
            result = generate_executive_summary(manuscript_text, model="test-model")
            
            assert result == "Generated executive summary"
            # Verify LLMClient was instantiated and query was called
            mock_client_class.assert_called_once()
            mock_client.query.assert_called_once()
            # Verify query was called with model parameter
            call_args = mock_client.query.call_args
            assert call_args[1]["model"] == "test-model"
    
    def test_generate_quality_review_calls_llm(self):
        """Test generate_quality_review actually queries LLM."""
        manuscript_text = "Test manuscript."
        
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "Quality review"
            mock_client_class.return_value = mock_client
            
            result = generate_quality_review(manuscript_text)
            
            assert result == "Quality review"
            mock_client.query.assert_called_once()
    
    def test_generate_methodology_review_calls_llm(self):
        """Test generate_methodology_review actually queries LLM."""
        manuscript_text = "Test manuscript."
        
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "Methodology review"
            mock_client_class.return_value = mock_client
            
            result = generate_methodology_review(manuscript_text)
            
            assert result == "Methodology review"
            mock_client.query.assert_called_once()
    
    def test_generate_improvement_suggestions_calls_llm(self):
        """Test generate_improvement_suggestions actually queries LLM."""
        manuscript_text = "Test manuscript."
        
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "Improvement suggestions"
            mock_client_class.return_value = mock_client
            
            result = generate_improvement_suggestions(manuscript_text)
            
            assert result == "Improvement suggestions"
            mock_client.query.assert_called_once()
    
    def test_generate_translation_calls_llm(self):
        """Test generate_translation actually queries LLM."""
        text = "Hello world"
        target_language = "zh"
        
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "你好世界"
            mock_client_class.return_value = mock_client
            
            result = generate_translation(text, target_language)
            
            assert result == "你好世界"
            mock_client.query.assert_called_once()
    
    def test_generate_translation_with_model(self):
        """Test generate_translation respects model parameter."""
        text = "Test"
        target_language = "hi"
        
        with patch('infrastructure.llm.LLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.query.return_value = "Translation"
            mock_client_class.return_value = mock_client
            
            generate_translation(text, target_language, model="custom-model")
            
            call_args = mock_client.query.call_args
            assert call_args[1]["model"] == "custom-model"


@pytest.mark.requires_ollama
class TestReviewGeneratorsIntegration:
    """Integration tests for review generators (requires Ollama)."""
    
    def test_generate_executive_summary_real_ollama(self):
        """Test generate_executive_summary with real Ollama."""
        from infrastructure.llm import LLMClient
        
        client = LLMClient()
        if not client.check_connection():
            pytest.skip("Ollama not available")
        
        manuscript_text = "This is a test manuscript about machine learning and AI."
        result = generate_executive_summary(manuscript_text)
        
        assert len(result) > 0
        assert isinstance(result, str)
    
    def test_generate_review_with_metrics_real_ollama(self):
        """Test generate_review_with_metrics with real Ollama."""
        from infrastructure.llm import LLMClient
        
        client = LLMClient()
        if not client.check_connection():
            pytest.skip("Ollama not available")
        
        manuscript_text = "Test manuscript about optimization algorithms."
        review_text, metrics = generate_review_with_metrics(
            manuscript_text, "executive_summary"
        )
        
        assert len(review_text) > 0
        assert "tokens_used" in metrics
        assert "time_seconds" in metrics
        assert metrics["time_seconds"] > 0


