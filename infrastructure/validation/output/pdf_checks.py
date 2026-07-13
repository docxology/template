"""PDF-related checks for the output validation pipeline."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files import find_combined_pdf
from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure

logger = get_logger(__name__)


def validate_transmission_bookends(project_root: Path, project_name: str) -> bool:
    """Validate transmission bookend single-page contract when enabled."""
    from infrastructure.publishing.transmission_bookends import transmission_bookends_enabled
    from infrastructure.publishing.transmission_page_check import validate_transmission_bookend_pages

    config_path = resolve_source_manuscript_dir(project_root) / "config.yaml"
    if not transmission_bookends_enabled(config_path):
        return True

    located_pdf = find_combined_pdf(project_root / "output", project_name)
    if located_pdf is None:
        project_basename = Path(project_name).name
        expected_pdf = project_root / "output" / "pdf" / f"{project_basename}_combined.pdf"
        logger.warning("Transmission bookends enabled but combined PDF missing: %s", expected_pdf)
        return False

    log_substep("Validating transmission bookend page span...", logger)
    combined_pdf, _ = located_pdf
    return validate_transmission_bookend_pages(combined_pdf)


def validate_pdfs(project_root: Path) -> bool:
    """Validate generated PDF files under a project output directory."""
    log_substep("Validating PDF files...", logger)

    pdf_dir = project_root / "output" / "pdf"
    slides_dir = project_root / "output" / "slides"

    if not pdf_dir.exists():
        logger.error("PDF directory not found")
        return False

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if slides_dir.exists():
        pdf_files.extend(sorted(slides_dir.glob("*.pdf")))

    if not pdf_files:
        logger.error("No PDF files to validate")
        return False

    valid_count = 0
    for pdf_file in pdf_files:
        try:
            file_size = pdf_file.stat().st_size

            if file_size > 0 and validate_pdf_structure(pdf_file):
                log_success(f"PDF valid: {pdf_file.name} ({file_size} bytes)", logger)
                valid_count += 1
            elif file_size <= 0:
                logger.error("PDF empty: %s", pdf_file.name)
            else:
                logger.error("PDF structurally invalid: %s", pdf_file.name)
        except OSError as exc:
            logger.error("Cannot validate %s: %s", pdf_file.name, exc)

    return valid_count == len(pdf_files)
