"""Tests for infrastructure.literature.llm_operations module.

Tests for advanced LLM operations including literature reviews, comparative analysis,
and research gap identification.
"""

import time
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch
import tempfile

from infrastructure.literature.llm_operations import (
    LiteratureLLMOperations,
    LLMOperationResult,
)
from infrastructure.literature.library_index import LibraryEntry


class TestLLMOperationResult:
    """Test LLMOperationResult dataclass."""

    def test_result_creation(self):
        """Test creating an LLMOperationResult."""
        result = LLMOperationResult(
            operation_type="literature_review",
            papers_used=5,
            citation_keys=["paper1", "paper2"],
            output_text="Generated review text",
            generation_time=10.5,
            tokens_estimated=1000
        )
        
        assert result.operation_type == "literature_review"
        assert result.papers_used == 5
        assert len(result.citation_keys) == 2
        assert result.output_text == "Generated review text"
        assert result.generation_time == 10.5
        assert result.tokens_estimated == 1000

    def test_result_defaults(self):
        """Test LLMOperationResult with default values."""
        result = LLMOperationResult(
            operation_type="test",
            papers_used=0,
            citation_keys=[],
            output_text=""
        )
        
        assert result.output_path is None
        assert result.generation_time == 0.0
        assert result.tokens_estimated == 0
        assert result.metadata == {}


class TestLiteratureLLMOperations:
    """Test LiteratureLLMOperations class."""

    def test_initialization(self):
        """Test initializing LLMOperations."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        assert operations.llm_client == mock_client

    @patch('infrastructure.literature.llm_operations.Path')
    def test_generate_literature_review_no_summaries(self, mock_path_class):
        """Test generating literature review without summaries."""
        mock_client = Mock()
        mock_client.query.return_value = "Generated literature review"
        
        operations = LiteratureLLMOperations(mock_client)
        
        # Create mock papers
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author 1"],
                year=2024,
                abstract="Abstract 1"
            ),
            LibraryEntry(
                citation_key="paper2",
                title="Paper 2",
                authors=["Author 2"],
                year=2023,
                abstract="Abstract 2"
            )
        ]
        
        # Mock summary paths to not exist - create a chainable mock
        def path_side_effect(path_str):
            mock_path = Mock()
            mock_path.exists.return_value = False
            # Support / operator - must accept self as first parameter
            def truediv(self, other):
                new_mock = Mock()
                new_mock.exists.return_value = False
                new_mock.__truediv__ = truediv  # Support chaining
                return new_mock
            mock_path.__truediv__ = truediv
            return mock_path
        
        mock_path_class.side_effect = path_side_effect
        
        result = operations.generate_literature_review(papers, focus="general", max_papers=10)
        
        assert result.operation_type == "literature_review"
        assert result.papers_used == 2
        assert len(result.citation_keys) == 2
        assert "Generated literature review" in result.output_text
        assert result.generation_time > 0

    @patch('infrastructure.literature.llm_operations.Path')
    def test_generate_literature_review_with_summaries(self, mock_path_class):
        """Test generating literature review with summaries."""
        mock_client = Mock()
        mock_client.query.return_value = "Review with summaries"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author 1"],
                year=2024,
                abstract="Abstract 1"
            )
        ]
        
        # Mock summary file exists - create a chainable mock
        def path_side_effect(path_str):
            mock_path = Mock()
            # Check if this is the summary path
            if "paper1_summary" in str(path_str) or "summaries" in str(path_str):
                mock_path.exists.return_value = True
                mock_path.read_text.return_value = "---\nSummary content here\n---"
            else:
                mock_path.exists.return_value = False
            # Support / operator - must accept self as first parameter
            def truediv(self, other):
                new_mock = Mock()
                if "paper1_summary" in str(other) or "summaries" in str(path_str):
                    new_mock.exists.return_value = True
                    new_mock.read_text.return_value = "---\nSummary content here\n---"
                else:
                    new_mock.exists.return_value = False
                new_mock.__truediv__ = truediv  # Support chaining
                return new_mock
            mock_path.__truediv__ = truediv
            return mock_path
        
        mock_path_class.side_effect = path_side_effect
        
        result = operations.generate_literature_review(papers)
        
        assert result.operation_type == "literature_review"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_generate_literature_review_max_papers(self):
        """Test that max_papers limit is respected."""
        mock_client = Mock()
        mock_client.query.return_value = "Review"
        
        operations = LiteratureLLMOperations(mock_client)
        
        # Create 10 papers
        papers = [
            LibraryEntry(
                citation_key=f"paper{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024,
                abstract="Abstract"
            )
            for i in range(10)
        ]
        
        result = operations.generate_literature_review(papers, max_papers=5)
        
        assert result.papers_used == 5
        assert len(result.citation_keys) == 5

    def test_generate_science_communication(self):
        """Test generating science communication narrative."""
        mock_client = Mock()
        mock_client.query.return_value = "Science communication narrative"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract="Abstract"
            )
        ]
        
        result = operations.generate_science_communication(papers, audience="general")
        
        assert result.operation_type == "science_communication"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_generate_comparative_analysis(self):
        """Test generating comparative analysis."""
        mock_client = Mock()
        mock_client.query.return_value = "Comparative analysis"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract="Abstract 1"
            ),
            LibraryEntry(
                citation_key="paper2",
                title="Paper 2",
                authors=["Author"],
                year=2023,
                abstract="Abstract 2"
            )
        ]
        
        result = operations.generate_comparative_analysis(papers, aspect="methodology")
        
        assert result.operation_type == "comparative_analysis"
        assert result.papers_used == 2
        mock_client.query.assert_called_once()

    def test_identify_research_gaps(self):
        """Test identifying research gaps."""
        mock_client = Mock()
        mock_client.query.return_value = "Research gaps identified"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract="Abstract"
            )
        ]
        
        result = operations.identify_research_gaps(papers, domain="machine learning")
        
        assert result.operation_type == "research_gaps"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_analyze_citation_network(self):
        """Test analyzing citation network."""
        mock_client = Mock()
        mock_client.query.return_value = "Citation network analysis"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract="Abstract"
            )
        ]
        
        result = operations.analyze_citation_network(papers)
        
        assert result.operation_type == "citation_network"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_save_result(self):
        """Test saving operation result to file."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        result = LLMOperationResult(
            operation_type="test",
            papers_used=1,
            citation_keys=["paper1"],
            output_text="Test output"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            saved_path = operations.save_result(result, output_dir)
            
            assert saved_path.exists()
            assert "Test output" in saved_path.read_text()
            assert result.output_path == saved_path

