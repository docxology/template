"""Core logic for rendering module."""

import subprocess
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.web_renderer import WebRenderer

logger = get_logger(__name__)

# Minimum PDF size in MB; PDFs below this are considered empty/corrupted
# (matches 1000-byte check in pdf_validator)
_MIN_VALID_PDF_MB = 0.001


def _remove_stale_slide_artifacts(slides_dir: Path, source_stem: str) -> None:
    """Remove slide artifacts for a source file when slides are intentionally skipped."""
    for stale in slides_dir.glob(f"{source_stem}_slides.*"):
        try:
            stale.unlink()
        except OSError as cleanup_error:
            logger.debug(f"Could not remove stale slide artefact {stale}: {cleanup_error}")


class RenderManager:
    """Orchestrates rendering of all output formats."""

    def __init__(
        self,
        config: RenderingConfig | None = None,
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
        *,
        slides_renderer: Any = None,
        web_renderer: Any = None,
    ):
        """Initialize the render manager with configuration and directories."""
        self.config = config or RenderingConfig.from_env()
        self.manuscript_dir = manuscript_dir
        self.figures_dir = figures_dir
        self.pdf_renderer = PDFRenderer(self.config)
        self.slides_renderer = slides_renderer or SlidesRenderer(self.config)
        self.web_renderer = web_renderer or WebRenderer(self.config)

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
            TemplateError: If source file doesn't exist, if the file format
                is not supported (.tex or .md), or if all output formats fail
                to render.
        """
        from infrastructure.core.exceptions import TemplateError

        if not source_file.exists():
            raise TemplateError(f"Source file does not exist: {source_file}")

        rendered_paths = []
        format_errors: list[tuple[str, Exception]] = []

        # Validate file format
        supported_formats = [".tex", ".md"]
        if source_file.suffix not in supported_formats:
            raise TemplateError(f"Unsupported file format: {source_file.suffix}. Supported: {supported_formats}")

        try:
            # Determine what to render based on extension/type
            if source_file.suffix == ".tex":
                # LaTeX usually means PDF
                logger.debug(f"Rendering LaTeX file: {source_file.name}")
                if self.config.enable_pdf:
                    rendered_paths.append(self.pdf_renderer.render(source_file))
                else:
                    logger.info(f"Skipping PDF for {source_file.name} (render.formats.pdf=false)")

            elif source_file.suffix == ".md":
                # Markdown supports slides and web formats
                logger.debug(f"Rendering Markdown file: {source_file.name}")
                source_text = source_file.read_text(encoding="utf-8")
                skip_beamer = "<!-- render:skip-beamer -->" in source_text

                # 1. Beamer slides for presentation
                if not self.config.enable_slides:
                    logger.info(f"Skipping Beamer slides for {source_file.name} (render.formats.slides=false)")
                    _remove_stale_slide_artifacts(Path(self.config.slides_dir), source_file.stem)
                elif skip_beamer:
                    logger.info(f"Skipping Beamer slides for {source_file.name} (render:skip-beamer)")
                    _remove_stale_slide_artifacts(Path(self.config.slides_dir), source_file.stem)
                else:
                    try:
                        logger.debug("Rendering Beamer slides...")
                        rendered_paths.append(self.render_slides(source_file, output_format="beamer"))
                        logger.debug("Beamer slides rendered successfully")
                    except (OSError, subprocess.SubprocessError, ValueError, TemplateError) as e:  # noqa: BLE001 — tracked in format_errors; raises if any required format fails
                        format_errors.append(("beamer", e))
                        # Enhanced error reporting for Beamer slide failures
                        error_msg = f"Failed to render Beamer slides: {str(e)}"

                        # Check if PDF was created but is empty (0.0 KB)
                        # Derive expected path from config — do NOT re-invoke the renderer
                        try:
                            beamer_pdf = Path(self.config.slides_dir) / f"{source_file.stem}_slides.pdf"
                            if beamer_pdf.exists():
                                size_mb = beamer_pdf.stat().st_size / (1024 * 1024)
                                if size_mb < _MIN_VALID_PDF_MB:
                                    error_msg += f" (PDF created but empty: {size_mb:.3f} MB)"
                                    error_msg += (
                                        f" - Check LaTeX compilation log: {beamer_pdf.parent / beamer_pdf.stem}.log"  # noqa: E501
                                    )
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
                if self.config.enable_html:
                    try:
                        logger.debug("Rendering HTML web version...")
                        rendered_paths.append(self.web_renderer.render(source_file))
                        logger.debug("HTML web version rendered successfully")
                    except (OSError, subprocess.SubprocessError, ValueError) as e:  # noqa: BLE001 — tracked in format_errors; raises if all formats fail
                        format_errors.append(("html", e))
                        logger.warning(f"Failed to render HTML: {e}")
                        # Continue - some formats may still succeed
                else:
                    logger.info(f"Skipping HTML for {source_file.name} (render.formats.html=false)")

            if not rendered_paths:
                failed_formats = ", ".join(f"{fmt}: {err}" for fmt, err in format_errors)
                raise TemplateError(
                    f"No rendered_paths generated for {source_file.name}. All formats failed: {failed_formats}"
                )

            if format_errors:
                failed_names = ", ".join(fmt for fmt, _ in format_errors)
                failed_formats = "; ".join(f"{fmt}: {err}" for fmt, err in format_errors)
                raise TemplateError(
                    f"Partial rendering failure for {source_file.name}: "
                    f"{len(rendered_paths)} format(s) succeeded, "
                    f"{len(format_errors)} failed ({failed_names}). {failed_formats}"
                )

            logger.debug(f"Successfully rendered {len(rendered_paths)} format(s) for {source_file.name}")
            return rendered_paths

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
        """Render a .tex or .md source file to PDF."""
        return self.pdf_renderer.render(source_file)

    def render_slides(self, source_file: Path, output_format: str = "beamer") -> Path:
        """Render slides with figure path resolution."""
        return self.slides_renderer.render(
            source_file,
            output_format=output_format,
            manuscript_dir=self.manuscript_dir,
            figures_dir=self.figures_dir,
        )

    def render_web(self, source_file: Path) -> Path:
        """Render a Markdown source file to standalone HTML."""
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
