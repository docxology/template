"""Format-aware validation for rendered manuscript deliverables.

The render, validation, and copy stages must agree about which publication
formats are enabled.  This module loads the effective YAML/environment format
configuration and validates canonical artifacts without falling back to a
different output tree.  In particular, a stale combined PDF cannot satisfy an
HTML-only validation or copy gate.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from collections.abc import Callable, Collection
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.publishing.transmission_bookends import is_transmission_bookend
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files

logger = get_logger(__name__)

RENDER_FORMATS: frozenset[str] = frozenset({"pdf", "html", "slides", "docx", "epub"})


def render_config_manuscript_dir(project_root: Path) -> Path:
    """Return the manuscript tree whose render toggles govern current outputs.

    Stage 3 prefers a populated, variable-injected ``output/manuscript`` tree
    during post-render verification and otherwise uses the canonical source
    manuscript.  Later gates use the same rule so YAML and environment
    precedence cannot drift between stages.
    """

    injected = project_root / "output" / "manuscript"
    if injected.exists() and any(injected.glob("*.md")):
        return injected
    return resolve_source_manuscript_dir(project_root)


def load_effective_rendering_config(
    project_root: Path,
    *,
    env: dict[str, str] | None = None,
) -> RenderingConfig:
    """Load render toggles using the same YAML/env precedence as Stage 3."""

    manuscript_dir = render_config_manuscript_dir(project_root)
    config_path = manuscript_dir / "config.yaml"
    project_config: dict[str, Any] | None = None
    if config_path.is_file():
        try:
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(f"Could not read rendering configuration {config_path}: {exc}") from exc
        if loaded is not None and not isinstance(loaded, dict):
            raise ValueError(f"Rendering configuration must be a mapping: {config_path}")
        project_config = loaded
    config = RenderingConfig.from_project_config(project_config, env=env)
    if (project_root / "scripts" / "_render_pdf_override.py").is_file():
        # Stage 3 delegates this legacy hook as a PDF-only renderer and its
        # verifier deliberately ignores the normal multi-format toggles.  Keep
        # Stages 4 and 5 on that same contract instead of defaulting to missing
        # HTML/slides deliverables when an override project has no format block.
        return replace(
            config,
            enable_pdf=True,
            enable_html=False,
            enable_slides=False,
            enable_docx=False,
            enable_epub=False,
        )
    return config


def enabled_render_formats(config: RenderingConfig) -> frozenset[str]:
    """Return canonical names for every format enabled in *config*."""

    toggles = {
        "pdf": config.enable_pdf,
        "html": config.enable_html,
        "slides": config.enable_slides,
        "docx": config.enable_docx,
        "epub": config.enable_epub,
    }
    return frozenset(name for name, enabled in toggles.items() if enabled)


def _canonical_paths(output_dir: Path, project_basename: str) -> dict[str, tuple[Path, ...]]:
    """Return renderer-owned canonical artifacts for stale-output checks."""

    pdf_dir = output_dir / "pdf"
    web_dir = output_dir / "web"
    slides_dir = output_dir / "slides"
    docx_dir = output_dir / "docx"
    epub_dir = output_dir / "epub"
    return {
        "pdf": tuple(dict.fromkeys([output_dir / f"{project_basename}_combined.pdf", *sorted(pdf_dir.rglob("*.pdf"))])),
        "html": tuple(
            dict.fromkeys(
                [
                    web_dir / "index.html",
                    web_dir / "favicon.ico",
                    *(path for path in sorted(web_dir.glob("*.html")) if "__" in path.stem),
                ]
            )
        ),
        "slides": tuple(sorted((*slides_dir.rglob("*.pdf"), *slides_dir.rglob("*.html")))),
        "docx": tuple(
            dict.fromkeys([docx_dir / f"{project_basename}_combined.docx", *sorted(docx_dir.rglob("*.docx"))])
        ),
        "epub": tuple(
            dict.fromkeys([epub_dir / f"{project_basename}_combined.epub", *sorted(epub_dir.rglob("*.epub"))])
        ),
    }


def _validate_disabled_outputs_absent(
    output_dir: Path,
    project_basename: str,
    enabled_formats: set[str],
) -> bool:
    """Reject canonical artifacts for formats disabled in the effective config."""

    valid = True
    for format_name, paths in _canonical_paths(output_dir, project_basename).items():
        if format_name in enabled_formats:
            continue
        for path in paths:
            if path.exists():
                logger.error("Disabled %s output is still present and may be stale: %s", format_name, path)
                valid = False
    return valid


def remove_disabled_render_outputs(
    output_dir: Path,
    project_name: str,
    enabled_formats: Collection[str],
) -> tuple[Path, ...]:
    """Remove renderer-owned disabled-format artifacts from a copied tree.

    Stage 5 starts with an empty destination and then copies the complete
    project output tree.  A source tree can still contain an old artifact for
    a format disabled in the current configuration, so the copied publication
    tree is filtered before it is accepted.  Broad renderer-owned directories
    are removed for PDF, slides, DOCX, and EPUB.  The web directory is shared
    with project-authored pages, so only canonical renderer-owned HTML and its
    favicon are removed there.  The combined Markdown is cross-format
    provenance evidence and remains paired with its composition receipt even
    when HTML itself is disabled.

    The source project tree is never modified.  Cleanup failures propagate so
    a non-removable stale artifact cannot be accepted as a current output.
    """

    enabled = set(enabled_formats)
    unknown = enabled - RENDER_FORMATS
    if unknown:
        raise ValueError(f"Unknown render format(s): {', '.join(sorted(unknown))}")

    project_basename = Path(project_name).name
    targets: set[Path] = set()
    if "pdf" not in enabled:
        targets.update(
            {
                output_dir / f"{project_basename}_combined.pdf",
                output_dir / "pdf",
            }
        )
    if "slides" not in enabled:
        targets.add(output_dir / "slides")
    if "docx" not in enabled:
        targets.add(output_dir / "docx")
    if "epub" not in enabled:
        targets.add(output_dir / "epub")
    if "html" not in enabled:
        web_dir = output_dir / "web"
        targets.update({web_dir / "index.html", web_dir / "favicon.ico"})
        if web_dir.is_dir():
            targets.update(path for path in web_dir.glob("*.html") if "__" in path.stem)

    removed: list[Path] = []
    for target in sorted(targets):
        if not target.exists() and not target.is_symlink():
            continue
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target)
        logger.info("Removed disabled render output from copied tree: %s", target)
    return tuple(removed)


def _validate_combined_pdf(output_dir: Path, project_basename: str) -> bool:
    """Validate the copied combined PDF without consulting a source fallback."""

    candidates = (
        output_dir / f"{project_basename}_combined.pdf",
        output_dir / "pdf" / f"{project_basename}_combined.pdf",
    )
    actual_reserved = {
        *output_dir.glob("*_combined.pdf"),
        *(output_dir / "pdf").glob("*_combined.pdf"),
    }
    unexpected = sorted(actual_reserved - set(candidates))
    if unexpected:
        for path in unexpected:
            logger.error("Unexpected combined PDF has no current project identity: %s", path)
        return False
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0 and validate_pdf_structure(path):
            log_success(f"Combined PDF valid: {path.name}", logger)
            return True
    logger.error("Combined PDF output missing, empty, or structurally invalid: %s", candidates[0])
    return False


def _validate_combined_html(output_dir: Path) -> bool:
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


def _expected_slide_outputs(output_dir: Path, manuscript_dir: Path) -> list[Path] | None:
    """Return exact Beamer deliverables expected from current manuscript inputs."""

    source_files = discover_manuscript_files(manuscript_dir)
    if not source_files:
        logger.error("No manuscript sources found for enabled slides: %s", manuscript_dir)
        return None

    expected: list[Path] = []
    for source_file in source_files:
        if source_file.suffix != ".md" or is_transmission_bookend(source_file):
            continue
        try:
            source_text = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.error("Could not inspect slide source %s: %s", source_file, exc)
            return None
        if "<!-- render:skip-beamer -->" in source_text:
            continue
        expected.append(output_dir / "slides" / f"{source_file.stem}_slides.pdf")
    return expected


def _validate_slide_outputs(output_dir: Path, manuscript_dir: Path | None) -> bool:
    """Validate structurally complete slide PDFs for the current manuscript."""

    if manuscript_dir is None:
        expected = sorted((output_dir / "slides").glob("*_slides.pdf"))
        if not expected:
            logger.error("No slide outputs found in %s", output_dir / "slides")
            return False
    else:
        discovered = _expected_slide_outputs(output_dir, manuscript_dir)
        if discovered is None:
            return False
        expected = discovered

    if not expected:
        logger.error("Slides are enabled, but no current manuscript source produces a slide deck")
        return False

    slides_dir = output_dir / "slides"
    expected_reserved = {
        *(path for path in expected),
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
    log_success(f"Slide outputs valid: {len(expected)} expected deck(s)", logger)
    return True


def _validate_docx_output(output_dir: Path, project_basename: str) -> bool:
    """Validate the minimum Open Packaging Convention contract for DOCX."""

    path = output_dir / "docx" / f"{project_basename}_combined.docx"
    unexpected = sorted(set((output_dir / "docx").glob("*_combined.docx")) - {path})
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


def _validate_epub_output(output_dir: Path, project_basename: str) -> bool:
    """Validate the required EPUB mimetype and container package members."""

    path = output_dir / "epub" / f"{project_basename}_combined.epub"
    unexpected = sorted(set((output_dir / "epub").glob("*_combined.epub")) - {path})
    if unexpected:
        for candidate in unexpected:
            logger.error("Unexpected combined EPUB has no current project identity: %s", candidate)
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            mimetype_info = archive.getinfo("mimetype")
            mimetype = archive.read("mimetype")
            valid = (
                mimetype == b"application/epub+zip"
                and mimetype_info.compress_type == zipfile.ZIP_STORED
                and "META-INF/container.xml" in archive.namelist()
                and archive.testzip() is None
            )
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        logger.error("Combined EPUB output missing or invalid (%s): %s", path, exc)
        return False
    if not valid:
        logger.error("Combined EPUB output has an invalid package structure: %s", path)
        return False
    log_success(f"Combined EPUB valid: {path.name}", logger)
    return True


def validate_enabled_render_outputs(
    output_dir: Path,
    project_name: str,
    enabled_formats: Collection[str],
    *,
    manuscript_dir: Path | None = None,
    pdf_validator: Callable[[], bool] | None = None,
    reject_disabled: bool = True,
) -> bool:
    """Validate exactly the enabled canonical formats in one output tree.

    ``pdf_validator`` lets Stage 4 retain its established validation contract;
    Stage 5 omits it and validates the copied combined PDF directly.  Source
    fallback lookup is intentionally never used here.
    """

    enabled = set(enabled_formats)
    unknown = enabled - RENDER_FORMATS
    if unknown:
        logger.error("Unknown render format(s): %s", ", ".join(sorted(unknown)))
        return False
    if not enabled:
        logger.error("No render formats are enabled; there is no deliverable to validate")
        return False

    project_basename = Path(project_name).name
    valid = True
    if reject_disabled:
        valid = _validate_disabled_outputs_absent(output_dir, project_basename, enabled)

    checks: list[tuple[str, bool]] = []
    if "pdf" in enabled:
        pdf_valid = (
            pdf_validator() if pdf_validator is not None else _validate_combined_pdf(output_dir, project_basename)
        )
        checks.append(("PDF", pdf_valid))
    if "html" in enabled:
        checks.append(("HTML", _validate_combined_html(output_dir)))
    if "slides" in enabled:
        checks.append(("slides", _validate_slide_outputs(output_dir, manuscript_dir)))
    if "docx" in enabled:
        checks.append(("DOCX", _validate_docx_output(output_dir, project_basename)))
    if "epub" in enabled:
        checks.append(("EPUB", _validate_epub_output(output_dir, project_basename)))

    failed = [name for name, passed in checks if not passed]
    if failed:
        logger.error("Enabled render output validation failed: %s", ", ".join(failed))
        valid = False
    if valid:
        logger.info("Enabled render outputs valid: %s", ", ".join(name for name, _ in checks))
    return valid


__all__ = [
    "RENDER_FORMATS",
    "enabled_render_formats",
    "load_effective_rendering_config",
    "remove_disabled_render_outputs",
    "render_config_manuscript_dir",
    "validate_enabled_render_outputs",
]
