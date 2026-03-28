"""PDF Rendering module."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_combined_renderer import (
    build_pandoc_tex_command,
    inject_bibliography,
    inject_latex_preamble,
    postprocess_latex,
    preprocess_combined_markdown,
    prevalidate_markdown,
    run_pandoc_conversion,
    verify_figure_references,
)
from infrastructure.rendering._pdf_tex_transforms import fix_figure_paths
from infrastructure.rendering._pdf_latex_pipeline import (
    compile_latex_manuscript,
)
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


class PDFRenderer:
    """Handles PDF generation logic."""

    def __init__(self, config: RenderingConfig):
        """Initialize the PDF renderer with configuration."""
        self.config = config

    def _combine_markdown_files(self, source_files: list[Path]) -> str:
        """Combine section markdown files; logic lives in ``_pdf_markdown_combine``."""
        return combine_manuscript_markdown_sections(source_files)

    def render(self, source_file: Path, output_name: str | None = None) -> Path:
        """Render manuscript to PDF.

        This assumes source_file is a LaTeX file or Markdown file to be converted.
        For this implementation, we focus on LaTeX compilation.
        """
        if source_file.suffix == ".tex":
            return compile_latex(
                source_file,
                Path(self.config.pdf_dir),
                compiler=self.config.latex_compiler,
            )

        # Use Markdown rendering for .md files
        if source_file.suffix == ".md":
            return self.render_markdown(source_file)

        raise RenderingError(
            f"Unsupported file format for rendering: {source_file.suffix}",
            context={"source_file": str(source_file), "supported_formats": [".tex", ".md"]},
        )

    def render_markdown(self, source_file: Path, output_name: str | None = None) -> Path:
        """Render a single markdown file to PDF using Pandoc.

        Args:
            source_file: Path to markdown file
            output_name: Optional custom output filename

        Returns:
            Path to generated PDF file

        Raises:
            RenderingError: If Pandoc rendering fails
        """
        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / (output_name or f"{source_file.stem}.pdf")

        # Build resource paths to help pandoc find figures
        resource_paths = []
        manuscript_dir = Path(self.config.manuscript_dir)
        figures_dir = Path(self.config.figures_dir)

        if manuscript_dir.exists():
            resource_paths.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir.exists():
            resource_paths.extend(["--resource-path", str(figures_dir)])

        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-o",
            str(output_file),
            "--pdf-engine=xelatex",
            "--standalone",
        ]

        # Add resource paths
        cmd.extend(resource_paths)

        logger.info(f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}")

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
            )
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render markdown to PDF: {e.stderr}",
                context={"source": str(source_file), "target": str(output_file)},
            ) from e

    def render_combined(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
        """Render multiple markdown files as a combined PDF.

        Combines all source files, applies preamble, and generates a single PDF.

        Args:
            source_files: List of markdown files in order
            manuscript_dir: Directory containing manuscript files
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined PDF

        Raises:
            RenderingError: If combination or rendering fails
        """

        # Log sections being combined
        logger.info("\n" + "=" * 60)
        logger.info("COMBINED MANUSCRIPT RENDERING")
        logger.info("=" * 60)
        logger.info(f"Combining {len(source_files)} section(s):")
        for i, md_file in enumerate(source_files, 1):
            size_kb = md_file.stat().st_size / 1024
            logger.info(f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)")

        total_size_kb = sum(f.stat().st_size for f in source_files) / 1024
        logger.info(f"  {'Total input size:':<48} ({total_size_kb:>6.1f} KB)")
        logger.info("=" * 60 + "\n")

        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        project_basename = Path(project_name).name
        output_file = output_dir / f"{project_basename}_combined.pdf"

        # Remove existing output file to ensure fresh compilation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")

        # Check if bibliography exists
        bib_file = manuscript_dir / "references.bib"
        if not bib_file.exists():
            bib_file = manuscript_dir / "99_references.bib"
        bib_exists = bib_file.exists()

        # Create combined markdown
        combined_tex = output_dir / "_combined_manuscript.tex"
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = self._combine_markdown_files(source_files)

        # Write combined markdown atomically
        _tmp = combined_md.with_suffix(combined_md.suffix + ".tmp")
        try:
            _tmp.write_text(combined_content, encoding="utf-8")
            _tmp.replace(combined_md)
        except Exception:  # noqa: BLE001
            _tmp.unlink(missing_ok=True)
            raise
        logger.debug(
            f"Combined markdown written to: {combined_md} ({len(combined_content)} characters)"
        )

        # Step 1: Preprocess markdown (Mermaid stripping + figure path normalization)
        combined_content, _, n_fig_paths = preprocess_combined_markdown(combined_content)
        if n_fig_paths:
            combined_md.write_text(combined_content, encoding="utf-8")

        # Step 2: Pre-validate markdown for common issues
        logger.info("Converting combined markdown to LaTeX...")
        logger.debug(f"Combined markdown file: {combined_md}")
        _validation_errors, md_content = prevalidate_markdown(combined_md)

        # Step 3: Run Pandoc markdown→LaTeX conversion
        pandoc_cmd = build_pandoc_tex_command(self.config, combined_md, combined_tex, manuscript_dir)
        run_pandoc_conversion(pandoc_cmd, combined_md, source_files, md_content)

        # Step 4: Post-process LaTeX (lmodern, hidelinks, math delimiters)
        tex_content = combined_tex.read_text()
        tex_content = postprocess_latex(tex_content)

        # Step 5: Fix figure paths for LaTeX compilation
        tex_content = fix_figure_paths(tex_content, manuscript_dir, output_dir)

        # Step 6: Inject preamble and title page
        tex_content = inject_latex_preamble(tex_content, manuscript_dir)

        # Step 7: Inject bibliography
        tex_content = inject_bibliography(tex_content, bib_exists)

        # Write final .tex file atomically
        _tmp = combined_tex.with_suffix(combined_tex.suffix + ".tmp")
        try:
            _tmp.write_text(tex_content)
            _tmp.replace(combined_tex)
        except Exception:  # noqa: BLE001
            _tmp.unlink(missing_ok=True)
            raise

        # Step 8: Verify figure references
        figures_dir = Path(self.config.figures_dir)
        verify_figure_references(tex_content, figures_dir)

        # Step 9: Compile LaTeX to PDF with multi-pass xelatex
        return compile_latex_manuscript(
            combined_tex=combined_tex,
            combined_md=combined_md,
            output_dir=output_dir,
            output_file=output_file,
            bib_file=bib_file,
            bib_exists=bib_exists,
            source_files=source_files,
        )
