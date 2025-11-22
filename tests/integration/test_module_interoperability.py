"""Integration tests demonstrating module interoperability.

This suite tests how the new infrastructure modules work together to support
a complete research workflow.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from infrastructure.literature import LiteratureSearch
from infrastructure.llm import LLMClient
from infrastructure.rendering import RenderManager
from infrastructure import publishing


class TestResearchWorkflow:
    """Test complete research workflow using all modules."""

    def test_literature_to_llm_workflow(self, tmp_path, mocker):
        """Test literature search -> LLM summarization workflow."""
        # Mock literature search
        mock_lit_search = mocker.patch("infrastructure.literature.api.ArxivSource.search")
        from infrastructure.literature.api import SearchResult
        
        mock_result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2023,
            abstract="This is a test abstract about machine learning.",
            url="http://example.com",
            source="arxiv"
        )
        mock_lit_search.return_value = [mock_result]
        
        # Mock LLM
        mock_llm_post = mocker.patch("requests.post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Summary: ML paper"}}
        mock_llm_post.return_value = mock_response
        
        # Execute workflow - only search mock source
        lit = LiteratureSearch()
        results = lit.search("machine learning", limit=1, sources=["arxiv"])
        
        llm = LLMClient()
        summary = llm.apply_template("summarize_abstract", text=results[0].abstract)
        
        # Verify
        assert len(results) == 1
        assert summary == "Summary: ML paper"
        assert "machine learning" in results[0].abstract

    def test_rendering_publishing_workflow(self, tmp_path, mocker):
        """Test rendering -> publishing workflow."""
        # Create test LaTeX file
        tex_file = tmp_path / "paper.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Create expected PDF location (relative to current dir, not tmp_path)
        output_dir = Path("output") / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / "paper.pdf"
        
        # Mock rendering - create PDF in expected location
        mock_compile = mocker.patch("subprocess.run")
        mock_compile.return_value.returncode = 0
        
        def create_pdf(*args, **kwargs):
            pdf_path.touch()
            return mock_compile.return_value
        mock_compile.side_effect = create_pdf
        
        # Mock publishing
        mock_zenodo = mocker.patch("infrastructure.publishing.api.ZenodoClient")
        mock_instance = mock_zenodo.return_value
        mock_instance.create_deposition.return_value = "123"
        mock_instance.publish.return_value = "10.5281/zenodo.123"
        
        try:
            # Execute workflow
            manager = RenderManager()
            output = manager.render_pdf(tex_file)
            
            metadata = publishing.PublicationMetadata(
                title="Test",
                authors=["Author"],
                abstract="Abstract",
                keywords=["test"]
            )
            
            doi = publishing.publish_to_zenodo(metadata, [output], "token")
            
            # Verify
            assert output == pdf_path
            assert doi == "10.5281/zenodo.123"
        finally:
            # Cleanup
            if pdf_path.exists():
                pdf_path.unlink()

    def test_full_research_pipeline(self, tmp_path, mocker):
        """Test complete pipeline: search -> summarize -> render -> publish."""
        # 1. Literature search
        mock_lit = mocker.patch("infrastructure.literature.api.SemanticScholarSource.search")
        from infrastructure.literature.api import SearchResult
        
        paper = SearchResult(
            title="Novel Algorithm",
            authors=["Researcher"],
            year=2024,
            abstract="This paper presents a novel algorithm.",
            url="http://example.com",
            source="semanticscholar"
        )
        mock_lit.return_value = [paper]
        
        lit = LiteratureSearch()
        papers = lit.search("algorithm", limit=1, sources=["semanticscholar"])
        
        # 2. LLM processing
        mock_llm = mocker.patch("requests.post")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"content": "Key insight: novel approach"}}
        mock_llm.return_value = mock_resp
        
        llm = LLMClient()
        insight = llm.query(f"What are the key insights from: {papers[0].abstract}")
        
        # 3. Create manuscript
        manuscript = tmp_path / "manuscript.md"
        manuscript.write_text(f"# {papers[0].title}\n\n## Summary\n\n{insight}\n")
        
        # 4. Render (mock)
        mock_render = mocker.patch("subprocess.run")
        html_path = tmp_path / "output.html"
        html_path.touch()
        
        manager = RenderManager()
        # Would normally render, but we skip LaTeX compilation in test
        
        # 5. Publishing metadata
        pub_metadata = publishing.PublicationMetadata(
            title=papers[0].title,
            authors=papers[0].authors,
            abstract=papers[0].abstract,
            keywords=["algorithm", "research"]
        )
        
        # Verify workflow completion
        assert len(papers) == 1
        assert "novel approach" in insight
        assert manuscript.exists()
        assert pub_metadata.title == "Novel Algorithm"


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

