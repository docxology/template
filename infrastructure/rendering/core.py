"""Core logic for rendering module."""
from __future__ import annotations

from typing import Optional, List
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.web_renderer import WebRenderer
from infrastructure.rendering.poster_renderer import PosterRenderer

logger = get_logger(__name__)


class RenderManager:
    """Orchestrates rendering of all output formats."""

    def __init__(self, config: Optional[RenderingConfig] = None, 
                 manuscript_dir: Optional[Path] = None, figures_dir: Optional[Path] = None):
        self.config = config or RenderingConfig.from_env()
        self.manuscript_dir = manuscript_dir
        self.figures_dir = figures_dir
        self.pdf_renderer = PDFRenderer(self.config)
        self.slides_renderer = SlidesRenderer(self.config)
        self.web_renderer = WebRenderer(self.config)
        self.poster_renderer = PosterRenderer(self.config)

    def render_all(self, source_file: Path) -> List[Path]:
        """Render all supported formats for a source file.
        
        For markdown files, generates:
        - Beamer slides (presentation format)
        - HTML web version
        """
        outputs = []
        
        # Determine what to render based on extension/type
        if source_file.suffix == '.tex':
            # LaTeX usually means PDF or Poster
            outputs.append(self.pdf_renderer.render(source_file))
            
        elif source_file.suffix == '.md':
            # Markdown supports slides and web formats
            # 1. Beamer slides for presentation
            outputs.append(self.render_slides(source_file, format="beamer"))
            # 2. HTML web version
            outputs.append(self.web_renderer.render(source_file))
            
        return outputs

    def render_markdown_pdf(self, source_file: Path) -> Path:
        """Render individual markdown file to PDF."""
        return self.pdf_renderer.render_markdown(source_file)

    def render_pdf(self, source_file: Path) -> Path:
        """Render PDF."""
        return self.pdf_renderer.render(source_file)

    def render_slides(self, source_file: Path, format: str = "beamer") -> Path:
        """Render slides with figure path resolution."""
        return self.slides_renderer.render(
            source_file, 
            format=format,
            manuscript_dir=self.manuscript_dir,
            figures_dir=self.figures_dir
        )

    def render_web(self, source_file: Path) -> Path:
        """Render HTML."""
        return self.web_renderer.render(source_file)

    def render_combined_pdf(self, source_files: List[Path], manuscript_dir: Path) -> Path:
        """Render combined PDF from multiple markdown files.
        
        Args:
            source_files: List of markdown files in order to combine
            manuscript_dir: Directory containing manuscript files (for preamble/bib)
            
        Returns:
            Path to generated combined PDF file
        """
        logger.info(f"Rendering combined PDF from {len(source_files)} files...")
        return self.pdf_renderer.render_combined(source_files, manuscript_dir)

