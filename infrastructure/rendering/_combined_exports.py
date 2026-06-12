"""Combined PDF/HTML/DOCX/EPUB export helpers for the rendering pipeline."""

from __future__ import annotations

import subprocess
import traceback
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.diagnostic import DiagnosticReporter, DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.transmission_bookends import is_transmission_bookend
from infrastructure.rendering import RenderManager

logger = get_logger(__name__)


def combined_source_files(md_files: list[Path]) -> list[Path]:
    """Return combined-render inputs, ignoring missing generated transmission bookends."""
    combined_files: list[Path] = []
    for path in md_files:
        if path.exists() or not is_transmission_bookend(path):
            combined_files.append(path)
    return combined_files


html_combined_source_files = combined_source_files


def resolve_combined_markdown(manuscript_dir: Path) -> Path | None:
    """Find the combined-manuscript markdown produced by the combined-PDF pipeline."""
    if manuscript_dir.name == "manuscript" and manuscript_dir.parent.name == "output":
        project_root = manuscript_dir.parent.parent
    else:
        project_root = manuscript_dir.parent
    candidates = [
        project_root / "output" / "pdf" / "_combined_manuscript.md",
        project_root / "output" / "tex" / "_combined_manuscript.md",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def resolve_bibliography(manuscript_dir: Path) -> Path | None:
    """Return the first .bib in the manuscript dir, or None if not found."""
    bibs = sorted(manuscript_dir.glob("*.bib"))
    return bibs[0] if bibs else None


def render_combined_docx(
    manager: RenderManager,
    manuscript_dir: Path,
    project_name: str,
    reporter: DiagnosticReporter,
) -> None:
    """Render the combined DOCX from the preprocessed combined markdown."""
    from infrastructure.rendering.docx_renderer import render_docx

    combined_md = resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] DOCX rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    docx_dir = Path(manager.config.docx_dir)
    docx_dir.mkdir(parents=True, exist_ok=True)
    out_path = docx_dir / f"{project_name}_combined.docx"
    bibliography = resolve_bibliography(manuscript_dir)

    import shutil

    extra_args = [
        "--resource-path=" + str(manuscript_dir),
        "--resource-path=" + str(manager.config.figures_dir),
    ]
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        extra_args.extend(["--filter", crossref])
    else:
        logger.warning("pandoc-crossref not on PATH; DOCX @fig:/@sec:/@tbl:/@eq: will not resolve.")
    if bibliography is not None:
        extra_args.extend(["--citeproc", f"--bibliography={bibliography}"])

    import yaml as _yaml
    from infrastructure.rendering._pdf_title_page import _load_render_config, build_pandoc_metadata

    config, _ = _load_render_config(manuscript_dir)
    if isinstance(config, dict):
        meta = build_pandoc_metadata(config)
        if meta:
            meta_path = docx_dir / "_docx_metadata.yaml"
            with meta_path.open("w", encoding="utf-8") as handle:
                _yaml.safe_dump(meta, handle, allow_unicode=True, sort_keys=False)
            extra_args.append(f"--metadata-file={meta_path}")

    logger.debug("\n" + "=" * BANNER_WIDTH)
    logger.info("Generating combined DOCX manuscript...")
    try:
        result = render_docx(
            combined_md,
            out_path,
            bibliography=None,
            pandoc_path=manager.config.pandoc_path,
            extra_args=extra_args,
        )
        logger.info(f"✅ Generated combined DOCX: {result.output_path.name} ({result.size_bytes / 1024:.1f} KB)")
    except RenderingError as re:
        logger.warning(f"⚠️  Rendering error generating combined DOCX: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
    except (OSError, subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
        logger.warning(f"⚠️  Unexpected error generating combined DOCX: {e}")


def render_combined_epub(
    manager: RenderManager,
    manuscript_dir: Path,
    project_name: str,
    reporter: DiagnosticReporter,
) -> None:
    """Render the combined EPUB from the preprocessed combined markdown."""
    from infrastructure.rendering.epub_renderer import render_epub

    combined_md = resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] EPUB rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    epub_dir = Path(manager.config.epub_dir)
    epub_dir.mkdir(parents=True, exist_ok=True)
    out_path = epub_dir / f"{project_name}_combined.epub"
    bibliography = resolve_bibliography(manuscript_dir)

    logger.debug("\n" + "=" * BANNER_WIDTH)
    logger.info("Generating combined EPUB manuscript...")
    try:
        result = render_epub(
            combined_md,
            out_path,
            bibliography=bibliography,
            pandoc_path=manager.config.pandoc_path,
        )
        logger.info(f"✅ Generated combined EPUB: {result.output_path.name} ({result.size_bytes / 1024:.1f} KB)")
    except RenderingError as re:
        logger.warning(f"⚠️  Rendering error generating combined EPUB: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
    except (OSError, subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
        logger.warning(f"⚠️  Unexpected error generating combined EPUB: {e}")


def render_combined_outputs(
    manager: RenderManager,
    md_files: list[Path],
    manuscript_dir: Path,
    project_name: str,
    reporter: DiagnosticReporter,
    rendered_count: int,
) -> None:
    """Generate the combined PDF / HTML / DOCX / EPUB manuscripts."""
    config = manager.config

    if config.enable_pdf:
        logger.debug("\n" + "=" * BANNER_WIDTH)
        logger.info("Generating combined PDF manuscript...")
        try:
            combined_pdf = manager.render_combined_pdf(combined_source_files(md_files), manuscript_dir, project_name)
            logger.info(f"✅ Generated combined PDF: {combined_pdf.name}")
        except RenderingError as re:
            logger.error(f"❌ Rendering error generating combined PDF: {re.message}")
            reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.ERROR))
            if rendered_count > 0:
                logger.info(f"ℹ️  Note: {rendered_count} individual PDF(s) were generated despite combined PDF failure.")
        except (OSError, subprocess.SubprocessError, ValueError, TypeError) as e:
            logger.error(f"❌ Unexpected error generating combined PDF: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Full traceback:\n{traceback.format_exc()}")
            if hasattr(e, "stderr") and e.stderr:
                logger.error(f"  Full stderr:\n{e.stderr}")
            if hasattr(e, "stdout") and e.stdout:
                logger.error(f"  Full stdout:\n{e.stdout}")
            try:
                combined_md_path = manuscript_dir.parent / "output" / "tex" / "_combined_manuscript.md"
                if combined_md_path.exists():
                    logger.error(f"  Combined markdown: {combined_md_path} ({combined_md_path.stat().st_size} bytes)")
            except OSError as stat_err:
                logger.debug(f"  Could not stat combined markdown file: {stat_err}")
            logger.warning("  This is an unexpected error - please report this issue")
    else:
        logger.info("[skip] PDF rendering disabled in config (render.formats.pdf=false)")

    if config.enable_html:
        logger.debug("\n" + "=" * BANNER_WIDTH)
        logger.info("Generating combined HTML manuscript...")
        try:
            manager.render_combined_web(combined_source_files(md_files), manuscript_dir, project_name)
        except RenderingError as re:
            logger.warning(f"⚠️  Rendering error generating combined HTML: {re.message}")
            reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            logger.warning(f"⚠️  Unexpected error generating combined HTML: {e}")
    else:
        logger.info("[skip] HTML rendering disabled in config (render.formats.html=false)")

    if config.enable_docx:
        render_combined_docx(manager, manuscript_dir, project_name, reporter)
    else:
        logger.debug("[skip] DOCX rendering disabled in config (default; render.formats.docx=true to enable)")

    if config.enable_epub:
        render_combined_epub(manager, manuscript_dir, project_name, reporter)
    else:
        logger.debug("[skip] EPUB rendering disabled in config (default; render.formats.epub=true to enable)")
