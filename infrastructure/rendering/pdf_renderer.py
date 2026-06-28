"""PDF Rendering module."""

import os
import shutil
import subprocess
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_combined_renderer import (
    build_pandoc_tex_command,
    discover_manuscript_bib_paths,
    inject_bibliography,
    fix_starred_section_nameref_labels,
    inject_latex_preamble,
    postprocess_latex,
    preprocess_combined_markdown,
    prevalidate_markdown,
    prevalidate_source_markdown,
    run_pandoc_conversion,
    verify_figure_references,
)
from infrastructure.publishing.transmission_bookends import transmission_bookends_enabled
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

    def _markdown_pdf_engines(self) -> list[str]:
        candidates = [self.config.latex_compiler, "xelatex", "lualatex", "pdflatex"]
        engines: list[str] = []
        for engine in candidates:
            if engine and engine not in engines and shutil.which(engine):
                engines.append(engine)
        return engines

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

        logger.debug(f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}")

        if shutil.which(self.config.pandoc_path) is None:
            raise RenderingError(
                f"Pandoc not found: {self.config.pandoc_path}",
                context={"source": str(source_file), "target": str(output_file)},
            )

        engines = self._markdown_pdf_engines()
        if not engines:
            raise RenderingError(
                "No LaTeX PDF engine found for markdown rendering",
                context={"source": str(source_file), "target": str(output_file)},
            )

        errors: list[str] = []
        timeout = 8 if os.environ.get("PYTEST_CURRENT_TEST") else 600
        for engine in engines:
            if output_file.exists():
                output_file.unlink()
            cmd = [
                self.config.pandoc_path,
                str(source_file),
                "-o",
                str(output_file),
                f"--pdf-engine={engine}",
                "--standalone",
            ]
            cmd.extend(resource_paths)
            try:
                subprocess.run(  # nosec B603
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return output_file
            except subprocess.CalledProcessError as e:
                errors.append(f"{engine}: {e.stderr.strip() if e.stderr else 'unknown error'}")

        raise RenderingError(
            "Failed to render markdown to PDF with available engines",
            context={"source": str(source_file), "target": str(output_file), "engines": engines, "errors": errors},
        )

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

        logger.info("\n" + "=" * BANNER_WIDTH)
        logger.info("COMBINED MANUSCRIPT RENDERING")
        logger.info("=" * BANNER_WIDTH)
        logger.info(f"Combining {len(source_files)} section(s):")
        for i, md_file in enumerate(source_files, 1):
            size_kb = md_file.stat().st_size / 1024
            logger.info(f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)")

        total_size_kb = sum(f.stat().st_size for f in source_files) / 1024
        logger.info(f"  {'Total input size:':<48} ({total_size_kb:>6.1f} KB)")
        logger.info("=" * BANNER_WIDTH + "\n")

        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        project_basename = Path(project_name).name
        output_file = output_dir / f"{project_basename}_combined.pdf"

        # Remove existing output file to ensure fresh compilation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")

        # All manuscript *.bib files: pre-render citation gate unions them when
        # bib_file=None; LaTeX/BibTeX use \bibliography{stem1,stem2,...}.
        bib_paths = discover_manuscript_bib_paths(manuscript_dir)
        bib_exists = bool(bib_paths)
        bib_stems = ",".join(p.stem for p in bib_paths) if bib_paths else "references"

        combined_tex = output_dir / "_combined_manuscript.tex"
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = combine_manuscript_markdown_sections(source_files)

        # Write combined markdown atomically. Any failure (disk full, encoding
        # error, race between write and replace) must still remove the partial
        # .tmp file before re-raising, so the broad catch is intentional.
        _tmp = combined_md.with_suffix(combined_md.suffix + ".tmp")
        try:
            _tmp.write_text(combined_content, encoding="utf-8")
            _tmp.replace(combined_md)
        except Exception:  # noqa: BLE001 — atomic-write cleanup; re-raised below
            _tmp.unlink(missing_ok=True)
            raise
        logger.debug(f"Combined markdown written to: {combined_md} ({len(combined_content)} characters)")

        # Step 1: Preprocess markdown (Mermaid, figure paths, optional manuscript_vars.yaml)
        combined_content, n_mermaid, n_fig_paths, n_vars = preprocess_combined_markdown(
            combined_content, manuscript_dir=manuscript_dir
        )
        if n_fig_paths or n_mermaid or n_vars:
            combined_md.write_text(combined_content, encoding="utf-8")

        # Step 2: Pre-validate markdown — first the source set (hard gate
        # for Pandoc-pitfall patterns and undefined citations), then the
        # combined file (brace balance).
        prevalidate_source_markdown(
            source_files,
            bib_file=None,
        )
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
        config_path = manuscript_dir / "config.yaml"
        bookends_enabled = transmission_bookends_enabled(config_path) if config_path.is_file() else False
        tex_content = inject_latex_preamble(tex_content, manuscript_dir, skip_title_page=bookends_enabled)

        # Step 7: Inject bibliography
        tex_content = inject_bibliography(
            tex_content,
            bib_exists,
            bib_stems=bib_stems,
            before_end_transmission=bookends_enabled,
        )

        # Step 8: Repair starred-section \\nameref titles after preamble injection
        # (titlesec from preamble.md must be present before the guard runs).
        tex_content, _nameref_fixes = fix_starred_section_nameref_labels(tex_content)

        # Write final .tex file atomically. Any failure (disk full, encoding
        # error, race between write and replace) must still remove the partial
        # .tmp file before re-raising, so the broad catch is intentional.
        _tmp = combined_tex.with_suffix(combined_tex.suffix + ".tmp")
        try:
            _tmp.write_text(tex_content)
            _tmp.replace(combined_tex)
        except Exception:  # noqa: BLE001 — atomic-write cleanup; re-raised below
            _tmp.unlink(missing_ok=True)
            raise

        # Step 9: Verify figure references
        figures_dir = Path(self.config.figures_dir)
        verify_figure_references(tex_content, figures_dir)

        # Step 10: Compile LaTeX to PDF with multi-pass xelatex
        return compile_latex_manuscript(
            combined_tex=combined_tex,
            combined_md=combined_md,
            output_dir=output_dir,
            output_file=output_file,
            bib_files=bib_paths,
            bib_exists=bib_exists,
            source_files=source_files,
        )
