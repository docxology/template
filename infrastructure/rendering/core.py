"""Core logic for rendering module."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.poster_renderer import PosterRenderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.web_renderer import WebRenderer

logger = get_logger(__name__)

# Minimum PDF size in MB; PDFs below this are considered empty/corrupted (matches 1000-byte check in pdf_validator)
_MIN_VALID_PDF_MB = 0.001

class RenderManager:
    """Orchestrates rendering of all output formats."""

    def __init__(
        self,
        config: RenderingConfig | None = None,
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
    ):
        self.config = config or RenderingConfig.from_env()
        self.manuscript_dir = manuscript_dir
        self.figures_dir = figures_dir
        self.pdf_renderer = PDFRenderer(self.config)
        self.slides_renderer = SlidesRenderer(self.config)
        self.web_renderer = WebRenderer(self.config)
        self.poster_renderer = PosterRenderer(self.config)

    def render_all(self, source_file: Path) -> list[Path]:
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
        format_errors: list[tuple[str, Exception]] = []

        # Validate file format
        supported_formats = [".tex", ".md"]
        if source_file.suffix not in supported_formats:
            raise TemplateError(
                f"Unsupported file format: {source_file.suffix}. Supported: {supported_formats}"
            )

        try:
            # Determine what to render based on extension/type
            if source_file.suffix == ".tex":
                # LaTeX usually means PDF or Poster
                logger.info(f"Rendering LaTeX file: {source_file.name}")
                outputs.append(self.pdf_renderer.render(source_file))

            elif source_file.suffix == ".md":
                # Markdown supports slides and web formats
                logger.info(f"Rendering Markdown file: {source_file.name}")

                # 1. Beamer slides for presentation
                try:
                    logger.debug("Rendering Beamer slides...")
                    outputs.append(self.render_slides(source_file, format="beamer"))
                    logger.debug("Beamer slides rendered successfully")
                except (OSError, subprocess.SubprocessError, ValueError) as e:
                    format_errors.append(("beamer", e))
                    # Enhanced error reporting for Beamer slide failures
                    error_msg = f"Failed to render Beamer slides: {str(e)}"

                    # Check if PDF was created but is empty (0.0 KB)
                    try:
                        beamer_pdf = self.slides_renderer.render(source_file, format="beamer")
                        if beamer_pdf.exists():
                            size_mb = beamer_pdf.stat().st_size / (1024 * 1024)
                            if size_mb < _MIN_VALID_PDF_MB:
                                error_msg += f" (PDF created but empty: {size_mb:.3f} MB)"
                                error_msg += f" - Check LaTeX compilation log: {beamer_pdf.parent / beamer_pdf.stem}.log"  # noqa: E501
                            else:
                                error_msg += f" (PDF created: {size_mb:.2f} MB)"
                    except (OSError, AttributeError) as pdf_check_err:
                        logger.debug(f"Failed to check PDF status: {pdf_check_err}")

                    logger.warning(error_msg)

                    # Provide additional context if available
                    if hasattr(e, "context") and e.context:
                        log_file = e.context.get("log_file")
                        if log_file:
                            logger.warning(f"  LaTeX log file: {log_file}")

                    logger.warning("  Continuing with other formats...")
                    # Continue with other formats

                # 2. HTML web version
                try:
                    logger.debug("Rendering HTML web version...")
                    outputs.append(self.web_renderer.render(source_file))
                    logger.debug("HTML web version rendered successfully")
                except (OSError, subprocess.SubprocessError, ValueError) as e:
                    format_errors.append(("html", e))
                    logger.warning(f"Failed to render HTML: {e}")
                    # Continue - some formats may still succeed

            if not outputs:
                failed_formats = ", ".join(f"{fmt}: {err}" for fmt, err in format_errors)
                raise TemplateError(
                    f"No outputs generated for {source_file.name}. "
                    f"All formats failed: {failed_formats}"
                )

            if format_errors:
                failed_names = ", ".join(fmt for fmt, _ in format_errors)
                logger.warning(
                    f"Partial success for {source_file.name}: "
                    f"{len(outputs)} format(s) succeeded, "
                    f"{len(format_errors)} failed ({failed_names})"
                )

            logger.info(f"Successfully rendered {len(outputs)} format(s) for {source_file.name}")
            return outputs

        except TemplateError:
            # Re-raise TemplateError as-is
            raise
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"Unexpected error during rendering of {source_file.name}: {e}")
            raise TemplateError(f"Rendering failed: {e}") from e

    def render_markdown_pdf(self, source_file: Path) -> Path:
        """Render individual markdown file to PDF."""
        return self.pdf_renderer.render_markdown(source_file)

    def render_pdf(self, source_file: Path) -> Path:
        """Render a source file to PDF format.

        Delegates to the PDFRenderer for actual rendering. Supports both LaTeX (.tex)
        and Markdown (.md) source files.

        Args:
            source_file: Path to the source file to render. Must be a .tex or .md file.

        Returns:
            Path to the generated PDF file.

        Raises:
            RenderingError: If the source file format is unsupported or rendering fails.
        """
        return self.pdf_renderer.render(source_file)

    def render_slides(self, source_file: Path, format: str = "beamer") -> Path:
        """Render slides with figure path resolution."""
        return self.slides_renderer.render(
            source_file,
            format=format,
            manuscript_dir=self.manuscript_dir,
            figures_dir=self.figures_dir,
        )

    def render_web(self, source_file: Path) -> Path:
        """Render a source file to HTML web format.

        Delegates to the WebRenderer for actual rendering. Converts Markdown files
        to standalone HTML pages suitable for web viewing.

        Args:
            source_file: Path to the Markdown source file to render.

        Returns:
            Path to the generated HTML file.

        Raises:
            RenderingError: If the source file cannot be read or rendering fails.
        """
        return self.web_renderer.render(source_file)

    def render_combined_pdf(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
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

    def render_combined_web(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
        """Render combined HTML from multiple markdown files.

        Args:
            source_files: List of markdown files in order to combine
            manuscript_dir: Directory containing manuscript files
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined HTML file (index.html)
        """
        logger.info(f"Rendering combined HTML from {len(source_files)} files...")
        return self.web_renderer.render_combined(source_files, manuscript_dir, project_name)
