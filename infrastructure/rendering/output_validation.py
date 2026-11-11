"""Read-only format checks shared by the render and publication gates."""

from __future__ import annotations

import re
import zipfile
from collections.abc import Sequence
from logging import Logger
from pathlib import Path

from infrastructure.core.logging.utils import log_success
from infrastructure.rendering._epub_package_validation import validate_epub_package
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure
from infrastructure.rendering._slides_accessibility_reveal import accessible_reveal_output_issues


def validate_combined_html(output_dir: Path, *, logger: Logger) -> bool:
    """Require a non-empty standalone combined HTML document."""

    path = output_dir / "web" / "index.html"
    try:
        if not path.is_file() or path.stat().st_size == 0:
            logger.error("Combined HTML output missing or empty: %s", path)
            return False
        prefix = path.read_text(encoding="utf-8")[:8192].lower()
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("Could not validate combined HTML output %s: %s", path, exc)
        return False
    if not re.search(r"(?:<!doctype\s+html\b|<html(?:\s|>))", prefix):
        logger.error("Combined HTML output is not a standalone HTML document: %s", path)
        return False
    log_success(f"Combined HTML valid: {path.name}", logger)
    return True


def validate_slide_artifacts(
    slides_dir: Path,
    expected: Sequence[Path],
    *,
    slides_profile: str,
    logger: Logger,
) -> bool:
    """Check the reserved deck identities and the profile's required artifacts."""

    expected_reserved = {
        *expected,
        *(path.with_suffix(".html") for path in expected),
    }
    actual_reserved = {
        *slides_dir.glob("*_slides.pdf"),
        *slides_dir.glob("*_slides.html"),
    }
    unexpected = sorted(actual_reserved - expected_reserved)
    if unexpected:
        for path in unexpected:
            logger.error("Unexpected slide output has no current manuscript source: %s", path)
        return False

    invalid = [path for path in expected if not path.is_file() or not validate_pdf_structure(path)]
    if invalid:
        for path in invalid:
            logger.error("Slide output missing or structurally invalid: %s", path)
        return False

    if slides_profile == "accessible":
        invalid_html = [
            (path, accessible_reveal_output_issues(path)) for path in (pdf.with_suffix(".html") for pdf in expected)
        ]
        invalid_html = [(path, issues) for path, issues in invalid_html if issues]
        if invalid_html:
            for path, issues in invalid_html:
                logger.error("Accessible Reveal output missing or invalid: %s (%s)", path, "; ".join(issues))
            return False
    return True


def validate_docx_output(output_dir: Path, project_basename: str, *, logger: Logger) -> bool:
    """Validate one exact DOCX identity across the recursive format tree."""

    path = output_dir / "docx" / f"{project_basename}_combined.docx"
    unexpected = sorted(set((output_dir / "docx").rglob("*_combined.docx")) - {path})
    if unexpected:
        for candidate in unexpected:
            logger.error("Unexpected combined DOCX has no current project identity: %s", candidate)
        return False
    required_members = {"[Content_Types].xml", "word/document.xml"}
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            valid = required_members <= names and archive.testzip() is None
    except (OSError, zipfile.BadZipFile) as exc:
        logger.error("Combined DOCX output missing or invalid (%s): %s", path, exc)
        return False
    if not valid:
        logger.error("Combined DOCX output has an invalid package structure: %s", path)
        return False
    log_success(f"Combined DOCX valid: {path.name}", logger)
    return True


def validate_epub_output(output_dir: Path, project_basename: str, *, logger: Logger) -> bool:
    """Validate one exact EPUB identity and its bounded package contract."""

    path = output_dir / "epub" / f"{project_basename}_combined.epub"
    unexpected = sorted(set((output_dir / "epub").rglob("*_combined.epub")) - {path})
    if unexpected:
        for candidate in unexpected:
            logger.error("Unexpected combined EPUB has no current project identity: %s", candidate)
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            validate_epub_package(archive)
    except (EOFError, KeyError, NotImplementedError, OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        logger.error("Combined EPUB output missing or invalid (%s): %s", path, exc)
        return False
    log_success(f"Combined EPUB valid: {path.name}", logger)
    return True
