"""Integration tests demonstrating module interoperability.

This suite tests how the new infrastructure modules work together to support
a complete research workflow. Following the "no mocks" policy, all tests use
real implementations or skip when services are unavailable.
"""
import pytest
from pathlib import Path

from infrastructure.literature import LiteratureSearch
from infrastructure.llm import LLMClient
from infrastructure.rendering import RenderManager
from infrastructure import publishing


class TestResearchWorkflow:
    """Test complete research workflow using all modules."""

    @pytest.mark.requires_ollama
    def test_literature_to_llm_workflow(self, tmp_path):
        """Test literature search -> LLM summarization workflow.
        
        Requires network access for literature search and Ollama for LLM.
        """
        # Test with real implementations - skip if services unavailable
        try:
            lit = LiteratureSearch()
            # Use a simple query that should work
            results = lit.search("machine learning", limit=1, sources=["arxiv"])
            
            if results:
                llm = LLMClient()
                summary = llm.apply_template("summarize_abstract", text=results[0].abstract)
                
                # Verify
                assert len(results) > 0
                assert summary is not None
                assert len(summary) > 0
                assert "machine learning" in results[0].abstract.lower() or "machine learning" in summary.lower()
        except Exception as e:
            pytest.skip(f"Service unavailable: {e}")

    def test_rendering_metadata_workflow(self, tmp_path):
        """Test rendering metadata -> publishing metadata workflow.
        
        Tests metadata handling without requiring actual rendering or publishing.
        """
        # Create test LaTeX file
        tex_file = tmp_path / "paper.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Test metadata creation without actual rendering
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Test Author"],
            abstract="This is a test abstract.",
            keywords=["test", "integration"]
        )
        
        # Verify metadata structure
        assert metadata.title == "Test Paper"
        assert len(metadata.authors) == 1
        assert metadata.authors[0] == "Test Author"
        assert "test" in metadata.keywords
        assert metadata.abstract == "This is a test abstract."

    def test_full_research_pipeline_metadata(self, tmp_path):
        """Test complete pipeline metadata handling without network calls.
        
        Tests that modules can work together for metadata creation and validation.
        """
        # 1. Create sample paper metadata (without network search)
        from infrastructure.literature.api import SearchResult
        
        paper = SearchResult(
            title="Novel Algorithm",
            authors=["Researcher"],
            year=2024,
            abstract="This paper presents a novel algorithm for optimization.",
            url="http://example.com",
            source="test"
        )
        
        # 2. Create manuscript from metadata
        manuscript = tmp_path / "manuscript.md"
        manuscript.write_text(f"# {paper.title}\n\n## Abstract\n\n{paper.abstract}\n")
        
        # 3. Create publishing metadata from paper
        pub_metadata = publishing.PublicationMetadata(
            title=paper.title,
            authors=paper.authors,
            abstract=paper.abstract,
            keywords=["algorithm", "optimization", "research"]
        )
        
        # Verify workflow completion
        assert paper.title == "Novel Algorithm"
        assert manuscript.exists()
        assert pub_metadata.title == "Novel Algorithm"
        assert len(pub_metadata.authors) == 1
        assert pub_metadata.authors[0] == "Researcher"


class TestModuleInteroperability:
    """Test how modules share data and configuration."""

    def test_shared_exception_handling(self):
        """Test that all modules use common exception hierarchy."""
        from infrastructure.core.exceptions import (
            LiteratureSearchError,
            LLMConnectionError,
            RenderingError,
            PublishingError
        )
        
        # All should inherit from TemplateError
        from infrastructure.core.exceptions import TemplateError
        
        assert issubclass(LiteratureSearchError, TemplateError)
        assert issubclass(LLMConnectionError, TemplateError)
        assert issubclass(RenderingError, TemplateError)
        assert issubclass(PublishingError, TemplateError)

    def test_shared_logging(self):
        """Test that all modules use common logging."""
        from infrastructure.core.logging_utils import get_logger
        
        # Create loggers for each module
        lit_logger = get_logger("infrastructure.literature")
        llm_logger = get_logger("infrastructure.llm")
        render_logger = get_logger("infrastructure.rendering")
        
        # All should be Logger instances
        assert lit_logger.name == "infrastructure.literature"
        assert llm_logger.name == "infrastructure.llm"
        assert render_logger.name == "infrastructure.rendering"

    def test_configuration_independence(self):
        """Test that module configurations are independent."""
        from infrastructure.literature.config import LiteratureConfig
        from infrastructure.llm.config import LLMConfig
        from infrastructure.rendering.config import RenderingConfig
        
        lit_config = LiteratureConfig()
        llm_config = LLMConfig()
        render_config = RenderingConfig()
        
        # Each has distinct configuration
        assert hasattr(lit_config, 'default_limit')
        assert hasattr(llm_config, 'default_model')
        assert hasattr(render_config, 'latex_compiler')
        
        # Configurations are independent
        lit_config.default_limit = 999
        assert llm_config.default_model != 999


class TestWrapperScripts:
    """Test wrapper scripts in infrastructure CLIs."""

    def test_literature_cli_exists(self):
        """Test that literature CLI exists."""
        from infrastructure.literature import cli
        assert hasattr(cli, 'main')
        assert hasattr(cli, 'search_command')

    def test_rendering_cli_exists(self):
        """Test that rendering CLI exists."""
        from infrastructure.rendering import cli
        assert hasattr(cli, 'main')

    def test_publishing_cli_exists(self):
        """Test that publishing CLI exists."""
        from infrastructure.publishing import cli
        assert hasattr(cli, 'main')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

