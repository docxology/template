"""Tests for infrastructure.literature.llm.operations module.

Tests for advanced LLM operations including literature reviews, comparative analysis,
and research gap identification.
"""

import time
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch
import tempfile

from infrastructure.literature.llm import (
    LiteratureLLMOperations,
    LLMOperationResult,
)
from infrastructure.literature.library import LibraryEntry


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

    @patch('infrastructure.literature.llm.operations.Path')
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

    @patch('infrastructure.literature.llm.operations.Path')
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

    def test_generate_literature_review_empty_papers(self):
        """Test generating literature review with empty papers list."""
        mock_client = Mock()
        mock_client.query.return_value = "Empty review"
        
        operations = LiteratureLLMOperations(mock_client)
        
        result = operations.generate_literature_review([], focus="general")
        
        assert result.operation_type == "literature_review"
        assert result.papers_used == 0
        assert len(result.citation_keys) == 0
        mock_client.query.assert_called_once()

    @patch('infrastructure.literature.llm.operations.Path')
    def test_generate_literature_review_summary_read_error(self, mock_path_class):
        """Test generating literature review when summary read fails."""
        mock_client = Mock()
        mock_client.query.return_value = "Review with fallback"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract="Abstract 1"
            )
        ]
        
        # Mock summary path exists but read_text raises exception
        def path_side_effect(path_str):
            mock_path = Mock()
            if "paper1_summary" in str(path_str) or "summaries" in str(path_str):
                mock_path.exists.return_value = True
                mock_path.read_text.side_effect = IOError("Read error")
            else:
                mock_path.exists.return_value = False
            def truediv(self, other):
                new_mock = Mock()
                if "paper1_summary" in str(other) or "summaries" in str(path_str):
                    new_mock.exists.return_value = True
                    new_mock.read_text.side_effect = IOError("Read error")
                else:
                    new_mock.exists.return_value = False
                new_mock.__truediv__ = truediv
                return new_mock
            mock_path.__truediv__ = truediv
            return mock_path
        
        mock_path_class.side_effect = path_side_effect
        
        result = operations.generate_literature_review(papers)
        
        # Should fallback to abstract
        assert result.operation_type == "literature_review"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_generate_science_communication_many_papers(self):
        """Test generating science communication with many papers."""
        mock_client = Mock()
        mock_client.query.return_value = "Narrative"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key=f"paper{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024,
                abstract=f"Abstract {i}"
            )
            for i in range(20)
        ]
        
        result = operations.generate_science_communication(papers, audience="researchers")
        
        assert result.operation_type == "science_communication"
        assert result.papers_used == 20
        assert len(result.citation_keys) == 20
        assert result.metadata["audience"] == "researchers"

    def test_generate_science_communication_no_abstract(self):
        """Test generating science communication with papers having no abstract."""
        mock_client = Mock()
        mock_client.query.return_value = "Narrative"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract=None  # No abstract
            )
        ]
        
        result = operations.generate_science_communication(papers)
        
        assert result.operation_type == "science_communication"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_generate_comparative_analysis_single_paper(self):
        """Test generating comparative analysis with single paper."""
        mock_client = Mock()
        mock_client.query.return_value = "Analysis"
        
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
        
        result = operations.generate_comparative_analysis(papers, aspect="results")
        
        assert result.operation_type == "comparative_analysis"
        assert result.papers_used == 1
        assert result.metadata["aspect"] == "results"

    def test_generate_comparative_analysis_many_papers(self):
        """Test generating comparative analysis with many papers."""
        mock_client = Mock()
        mock_client.query.return_value = "Analysis"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key=f"paper{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024 - i,
                abstract=f"Abstract {i}"
            )
            for i in range(10)
        ]
        
        result = operations.generate_comparative_analysis(papers, aspect="datasets")
        
        assert result.operation_type == "comparative_analysis"
        assert result.papers_used == 10
        assert result.metadata["aspect"] == "datasets"

    def test_identify_research_gaps_many_papers(self):
        """Test identifying research gaps with many papers."""
        mock_client = Mock()
        mock_client.query.return_value = "Gaps identified"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key=f"paper{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024,
                abstract=f"Abstract {i}"
            )
            for i in range(15)
        ]
        
        result = operations.identify_research_gaps(papers, domain="machine learning")
        
        assert result.operation_type == "research_gaps"
        assert result.papers_used == 15
        assert result.metadata["domain"] == "machine learning"

    def test_identify_research_gaps_no_abstract(self):
        """Test identifying research gaps with papers having no abstract."""
        mock_client = Mock()
        mock_client.query.return_value = "Gaps"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=2024,
                abstract=None
            )
        ]
        
        result = operations.identify_research_gaps(papers)
        
        assert result.operation_type == "research_gaps"
        assert result.papers_used == 1
        mock_client.query.assert_called_once()

    def test_analyze_citation_network_many_papers(self):
        """Test analyzing citation network with many papers."""
        mock_client = Mock()
        mock_client.query.return_value = "Network analysis"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key=f"paper{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024,
                abstract=f"Abstract {i}"
            )
            for i in range(25)
        ]
        
        result = operations.analyze_citation_network(papers)
        
        assert result.operation_type == "citation_network"
        assert result.papers_used == 25
        assert len(result.citation_keys) == 25

    def test_analyze_citation_network_no_year(self):
        """Test analyzing citation network with papers having no year."""
        mock_client = Mock()
        mock_client.query.return_value = "Network"
        
        operations = LiteratureLLMOperations(mock_client)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author"],
                year=None,  # No year
                abstract="Abstract"
            )
        ]
        
        result = operations.analyze_citation_network(papers)
        
        assert result.operation_type == "citation_network"
        assert result.papers_used == 1

    def test_save_result_nested_directory(self):
        """Test saving result to nested directory structure."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        result = LLMOperationResult(
            operation_type="test",
            papers_used=1,
            citation_keys=["paper1"],
            output_text="Test output"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "deep" / "path"
            
            saved_path = operations.save_result(result, output_dir)
            
            assert saved_path.exists()
            assert output_dir.exists()
            assert "Test output" in saved_path.read_text()

    def test_save_result_with_metadata(self):
        """Test saving result with metadata."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        result = LLMOperationResult(
            operation_type="test",
            papers_used=2,
            citation_keys=["paper1", "paper2"],
            output_text="Test output",
            metadata={"key1": "value1", "key2": 42}
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            saved_path = operations.save_result(result, output_dir)
            content = saved_path.read_text()
            
            assert "key1" in content
            assert "value1" in content
            assert "key2" in content
            assert "42" in content

    def test_save_result_existing_directory(self):
        """Test saving result when directory already exists."""
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
            output_dir.mkdir(exist_ok=True)  # Create directory first
            
            saved_path = operations.save_result(result, output_dir)
            
            assert saved_path.exists()
            assert "Test output" in saved_path.read_text()

    def test_llm_client_query_failure(self):
        """Test handling LLM client query failure."""
        mock_client = Mock()
        mock_client.query.side_effect = Exception("LLM API error")
        
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
        
        # Should propagate exception
        with pytest.raises(Exception, match="LLM API error"):
            operations.generate_literature_review(papers)

    def test_token_estimation_accuracy(self):
        """Test that token estimation is calculated."""
        mock_client = Mock()
        mock_client.query.return_value = "This is a test response with multiple words for token estimation"
        
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
        
        result = operations.generate_literature_review(papers)
        
        # Token estimation should be calculated (rough estimate: words * 1.3)
        assert result.tokens_estimated > 0
        # Should be roughly proportional to response length
        word_count = len(mock_client.query.return_value.split())
        expected_tokens = int(word_count * 1.3)
        assert abs(result.tokens_estimated - expected_tokens) < 5  # Allow small variance

    def test_generation_time_tracking(self):
        """Test that generation time is tracked accurately."""
        mock_client = Mock()
        
        def slow_query(prompt):
            time.sleep(0.1)  # Simulate slow generation
            return "Response"
        
        mock_client.query.side_effect = slow_query
        
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
        
        result = operations.generate_literature_review(papers)
        
        # Generation time should be at least 0.1 seconds
        assert result.generation_time >= 0.1
        assert result.generation_time < 1.0  # But not too long

    def test_save_result_file_path_format(self):
        """Test that saved file has correct format and naming."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        result = LLMOperationResult(
            operation_type="literature_review",
            papers_used=1,
            citation_keys=["paper1"],
            output_text="Test output"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            saved_path = operations.save_result(result, output_dir)
            
            # Filename should start with operation type
            assert saved_path.name.startswith("literature_review_")
            # Should end with .md
            assert saved_path.name.endswith(".md")
            # Should contain timestamp
            assert "_" in saved_path.stem

    def test_save_result_content_structure(self):
        """Test that saved file has proper content structure."""
        mock_client = Mock()
        operations = LiteratureLLMOperations(mock_client)
        
        result = LLMOperationResult(
            operation_type="test_operation",
            papers_used=3,
            citation_keys=["paper1", "paper2", "paper3"],
            output_text="Main content here",
            generation_time=5.5,
            tokens_estimated=1000,
            metadata={"param1": "value1"}
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            saved_path = operations.save_result(result, output_dir)
            content = saved_path.read_text()
            
            # Should contain operation type
            assert "Test Operation" in content
            # Should contain papers used
            assert "3" in content
            # Should contain citation keys
            assert "paper1" in content
            assert "paper2" in content
            assert "paper3" in content
            # Should contain generation time
            assert "5.5" in content
            # Should contain token estimate
            assert "1000" in content
            # Should contain metadata
            assert "param1" in content
            assert "value1" in content
            # Should contain main content
            assert "Main content here" in content

