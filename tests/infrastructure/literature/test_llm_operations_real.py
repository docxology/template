"""Real integration tests for LLM operations with actual Ollama.

These tests use real Ollama LLM to generate literature reviews, comparative analysis,
and other LLM operations. Requires Ollama to be running.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from infrastructure.literature.llm import LiteratureLLMOperations, LLMOperationResult
from infrastructure.literature.library import LibraryEntry


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestRealLLMOperations:
    """Real LLM operations tests with actual Ollama."""

    @pytest.fixture
    def llm_operations(self, ensure_ollama_available):
        """Create LLM operations with real Ollama client."""
        return LiteratureLLMOperations(ensure_ollama_available)

    @pytest.fixture
    def sample_papers(self):
        """Create sample papers for LLM operations."""
        return [
            LibraryEntry(
                citation_key="paper1",
                title="Machine Learning in Physics",
                authors=["Author A", "Author B"],
                year=2020,
                abstract="This paper discusses machine learning applications in physics research. We present novel methods for analyzing physical systems using neural networks.",
                doi="10.1234/test1",
                source="arxiv",
                url="https://example.com/1",
                venue="Journal of Physics",
                citation_count=50,
            ),
            LibraryEntry(
                citation_key="paper2",
                title="Deep Learning for Biology",
                authors=["Author C", "Author D"],
                year=2021,
                abstract="Deep learning methods for biological data analysis. The paper presents convolutional neural networks for protein structure prediction.",
                doi="10.1234/test2",
                source="semanticscholar",
                url="https://example.com/2",
                venue="Nature Biology",
                citation_count=100,
            ),
            LibraryEntry(
                citation_key="paper3",
                title="Neural Networks and Active Inference",
                authors=["Author A", "Author E"],
                year=2022,
                abstract="Neural networks and active inference in cognitive science. This work explores the relationship between predictive processing and neural computation.",
                doi="10.1234/test3",
                source="arxiv",
                url="https://example.com/3",
                venue="Cognitive Science",
                citation_count=75,
            ),
        ]

    def test_real_literature_review(self, llm_operations, sample_papers):
        """Test real literature review generation."""
        result = llm_operations.generate_literature_review(
            papers=sample_papers,
            focus="methods",
            max_papers=3
        )
        
        assert isinstance(result, LLMOperationResult)
        assert result.operation_type == "literature_review"
        assert result.papers_used == len(sample_papers)
        assert result.output_text is not None
        assert len(result.output_text) > 100  # Should have substantial content
        assert result.generation_time > 0
        assert result.tokens_estimated > 0
        assert len(result.citation_keys) == len(sample_papers)

    def test_real_science_communication(self, llm_operations, sample_papers):
        """Test real science communication generation."""
        result = llm_operations.generate_science_communication(
            papers=sample_papers[:2],
            audience="general_public"
        )
        
        assert isinstance(result, LLMOperationResult)
        assert result.operation_type == "science_communication"
        assert result.papers_used == 2
        assert result.output_text is not None
        assert len(result.output_text) > 50
        assert result.generation_time > 0

    def test_real_comparative_analysis(self, llm_operations, sample_papers):
        """Test real comparative analysis."""
        result = llm_operations.generate_comparative_analysis(
            papers=sample_papers,
            aspect="methods"
        )
        
        assert isinstance(result, LLMOperationResult)
        assert result.operation_type == "comparative_analysis"
        assert result.papers_used == len(sample_papers)
        assert result.output_text is not None
        assert len(result.output_text) > 50
        assert "method" in result.output_text.lower() or "approach" in result.output_text.lower()

    def test_real_research_gaps(self, llm_operations, sample_papers):
        """Test real research gap identification."""
        result = llm_operations.identify_research_gaps(
            papers=sample_papers,
            domain="machine learning"
        )
        
        assert isinstance(result, LLMOperationResult)
        assert result.operation_type == "research_gaps"
        assert result.papers_used == len(sample_papers)
        assert result.output_text is not None
        assert len(result.output_text) > 50
        assert result.generation_time > 0

    def test_real_citation_network(self, llm_operations, sample_papers):
        """Test real citation network analysis."""
        result = llm_operations.analyze_citation_network(
            papers=sample_papers
        )
        
        assert isinstance(result, LLMOperationResult)
        assert result.operation_type == "citation_network"
        assert result.papers_used == len(sample_papers)
        assert result.output_text is not None
        assert len(result.output_text) > 50

    def test_real_literature_review_save(self, llm_operations, sample_papers, tmp_path):
        """Test real literature review with file saving."""
        output_dir = tmp_path / "llm_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = llm_operations.generate_literature_review(
            papers=sample_papers,
            focus="general",
            max_papers=3
        )
        
        # Save result
        saved_path = llm_operations._save_result(
            result,
            output_dir=output_dir,
            subdirectory="literature_reviews"
        )
        
        assert saved_path.exists()
        assert saved_path.suffix == ".md"
        content = saved_path.read_text()
        assert len(content) > 0
        assert result.output_text in content


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestRealLiteratureReview:
    """Real literature review generation tests."""

    @pytest.fixture
    def llm_operations(self, ensure_ollama_available):
        """Create LLM operations with real Ollama client."""
        return LiteratureLLMOperations(ensure_ollama_available)

    def test_real_review_with_summaries(self, llm_operations, tmp_path):
        """Test literature review using paper summaries."""
        # Create sample papers with summary files
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir(parents=True)
        
        papers = [
            LibraryEntry(
                citation_key="paper1",
                title="Paper 1",
                authors=["Author 1"],
                year=2024,
                abstract="Abstract 1",
                source="arxiv",
                url="https://example.com/1"
            ),
            LibraryEntry(
                citation_key="paper2",
                title="Paper 2",
                authors=["Author 2"],
                year=2024,
                abstract="Abstract 2",
                source="arxiv",
                url="https://example.com/2"
            ),
        ]
        
        # Create summary files
        (summaries_dir / "paper1_summary.md").write_text("# Paper 1 Summary\n\nKey findings and methods.")
        (summaries_dir / "paper2_summary.md").write_text("# Paper 2 Summary\n\nMain contributions and results.")
        
        result = llm_operations.generate_literature_review(
            papers=papers,
            focus="general",
            max_papers=2
        )
        
        assert result.operation_type == "literature_review"
        assert result.papers_used == 2
        assert result.output_text is not None
        assert len(result.output_text) > 50


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestRealComparativeAnalysis:
    """Real comparative analysis tests."""

    @pytest.fixture
    def llm_operations(self, ensure_ollama_available):
        """Create LLM operations with real Ollama client."""
        return LiteratureLLMOperations(ensure_ollama_available)

    def test_real_compare_methods(self, llm_operations):
        """Test real comparison of methods."""
        papers = [
            LibraryEntry(
                citation_key="p1",
                title="Method A Paper",
                authors=["Author"],
                year=2024,
                abstract="This paper presents Method A for solving problems using neural networks.",
                source="arxiv",
                url="https://example.com"
            ),
            LibraryEntry(
                citation_key="p2",
                title="Method B Paper",
                authors=["Author"],
                year=2024,
                abstract="This paper presents Method B using deep learning approaches.",
                source="arxiv",
                url="https://example.com"
            ),
        ]
        
        result = llm_operations.generate_comparative_analysis(
            papers=papers,
            aspect="methods"
        )
        
        assert result.operation_type == "comparative_analysis"
        assert result.output_text is not None
        assert len(result.output_text) > 50


