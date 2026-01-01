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

        Args:
            source_file: Path to source file to render

        Returns:
            List of paths to generated output files

        Raises:
            TemplateError: If rendering fails or source file doesn't exist
        """
        from infrastructure.core.exceptions import TemplateError

        if not source_file.exists():
            raise TemplateError(f"Source file does not exist: {source_file}")

        outputs = []

        # Validate file format
        supported_formats = ['.tex', '.md']
        if source_file.suffix not in supported_formats:
            raise TemplateError(f"Unsupported file format: {source_file.suffix}. Supported: {supported_formats}")

        try:
            # Determine what to render based on extension/type
            if source_file.suffix == '.tex':
                # LaTeX usually means PDF or Poster
                logger.info(f"Rendering LaTeX file: {source_file.name}")
                outputs.append(self.pdf_renderer.render(source_file))

            elif source_file.suffix == '.md':
                # Markdown supports slides and web formats
                logger.info(f"Rendering Markdown file: {source_file.name}")

                # 1. Beamer slides for presentation
                try:
                    logger.debug("Rendering Beamer slides...")
                    outputs.append(self.render_slides(source_file, format="beamer"))
                    logger.debug("Beamer slides rendered successfully")
                except Exception as e:
                    # Enhanced error reporting for Beamer slide failures
                    error_msg = f"Failed to render Beamer slides: {str(e)}"

                    # Check if PDF was created but is empty (0.0 KB)
                    try:
                        beamer_pdf = self.slides_renderer.render(source_file, format="beamer")
                        if beamer_pdf.exists():
                            size_mb = beamer_pdf.stat().st_size / (1024 * 1024)
                            if size_mb < 0.001:  # Less than 1KB
                                error_msg += f" (PDF created but empty: {size_mb:.3f} MB)"
                                error_msg += f" - Check LaTeX compilation log: {beamer_pdf.parent / beamer_pdf.stem}.log"
                            else:
                                error_msg += f" (PDF created: {size_mb:.2f} MB)"
                    except:
                        pass  # Ignore errors when checking PDF status

                    logger.warning(error_msg)

                    # Provide additional context if available
                    if hasattr(e, 'context') and e.context:
                        log_file = e.context.get('log_file')
                        if log_file:
                            logger.warning(f"  LaTeX log file: {log_file}")

                    logger.warning("  Continuing with other formats...")
                    # Continue with other formats

                # 2. HTML web version
                try:
                    logger.debug("Rendering HTML web version...")
                    outputs.append(self.web_renderer.render(source_file))
                    logger.debug("HTML web version rendered successfully")
                except Exception as e:
                    logger.warning(f"Failed to render HTML: {e}")
                    # Continue - some formats may still succeed

            if not outputs:
                raise TemplateError(f"No outputs generated for {source_file.name}")

            logger.info(f"Successfully rendered {len(outputs)} format(s) for {source_file.name}")
            return outputs

        except TemplateError:
            # Re-raise TemplateError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during rendering of {source_file.name}: {e}")
            raise TemplateError(f"Rendering failed: {e}") from e

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

    def render_combined_pdf(self, source_files: List[Path], manuscript_dir: Path, project_name: str = "project") -> Path:
        """Render combined PDF from multiple markdown files.

        Args:
            source_files: List of markdown files in order to combine
            manuscript_dir: Directory containing manuscript files (for preamble/bib)
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined PDF file
        """
        logger.info(f"Rendering combined PDF from {len(source_files)} files...")
        return self.pdf_renderer.render_combined(source_files, manuscript_dir, project_name)

