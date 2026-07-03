"""Ebook generation orchestrator script.

This thin orchestrator coordinates ebook generation from the combined
markdown manuscript using the infrastructure rendering module:
1. Discovers the combined markdown file in the project's output directory
2. Renders EPUB, MOBI, and DOCX formats (unless skipped via --skip-formats)
3. Copies generated ebook files to output/ebook/ under the project's output
4. Reports results with file sizes

Stage 07 of the pipeline orchestration (opt-in ebook stage).

Exit codes:
    0: All requested ebook formats generated successfully
    1: Ebook generation failed (missing pandoc/calibre, or source files absent)
    2: Graceful skip — combined markdown not found (allow_skip compatible)
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from infrastructure.core.config.loader import load_config
from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering._combined_exports import (
    resolve_combined_markdown,
    rewrite_pdf_figure_refs_to_raster,
)
from infrastructure.rendering.epub_renderer import render_epub
from infrastructure.rendering.mobi_renderer import render_mobi
from infrastructure.rendering.docx_renderer import render_docx

# Set up logger for this module
logger = get_logger(__name__)

_ALL_FORMATS = ("epub", "mobi", "docx")


def _load_manuscript_metadata(project_root: Path) -> tuple[str | None, str | None, str]:
    """Return ``(title, author, language)`` from ``manuscript/config.yaml``.

    Without these, pandoc emits EPUB/MOBI output with no ``dc:title``/
    ``dc:creator`` at all and a ``dc:language`` that falls back to the host
    locale (e.g. the POSIX "C" locale becomes the literal, invalid value
    "C") — both of which real-world converters (Amazon KDP's ingestion
    pipeline) can reject outright rather than merely warn about.
    """
    config = load_config(project_root / "manuscript" / "config.yaml")
    if not config:
        return None, None, "en"

    paper = config.get("paper") or {}
    title = str(paper["title"]).strip() if isinstance(paper, dict) and paper.get("title") else None

    authors_raw = config.get("authors") or []
    author = None
    if isinstance(authors_raw, list) and authors_raw:
        first = authors_raw[0]
        if isinstance(first, dict) and first.get("name"):
            author = str(first["name"]).strip()

    metadata_block = config.get("metadata") or {}
    language = "en"
    if isinstance(metadata_block, dict) and metadata_block.get("language"):
        language = str(metadata_block["language"]).strip() or "en"

    return title, author, language


def _find_combined_markdown(project_root: Path) -> Path | None:
    """Find the combined markdown file produced by earlier pipeline stages.

    Delegates to ``resolve_combined_markdown()`` (the same lookup the
    combined-EPUB/DOCX renderers already use in production) rather than a
    separate glob pattern — the real convention is
    ``output/pdf/_combined_manuscript.md`` or ``output/tex/_combined_manuscript.md``,
    which the previous ``*_combined.md``/``combined*.md`` glob patterns here
    never actually matched (confirmed against real project output:
    ``blake_bimetalism``, ``template_code_project`` both use
    ``_combined_manuscript.md`` — this stage silently 2/graceful-skipped on
    every real project before this fix).
    """
    return resolve_combined_markdown(project_root / "output" / "manuscript")


def _format_size(size_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"


def run_ebook_generation(
    repo_root: Path,
    project: str,
    *,
    skip_formats_arg: str = "",
    cover_image_arg: str | None = None,
) -> int:
    """Execute ebook generation orchestration."""
    log_header(f"STAGE 11: Ebook Generation (Project: {project})", logger)

    project_root = resolve_project_root(repo_root, project)

    # Resolve cover image path if provided
    cover_image: Path | None = None
    if cover_image_arg:
        cover_image = Path(cover_image_arg)
        if not cover_image.is_absolute():
            cover_image = repo_root / cover_image
        if not cover_image.is_file():
            logger.warning("Cover image not found: %s — continuing without cover", cover_image)
            cover_image = None

    # Determine which formats to skip
    skip_formats = {fmt.strip().lower() for fmt in skip_formats_arg.split(",") if fmt.strip()}
    active_formats = [fmt for fmt in _ALL_FORMATS if fmt not in skip_formats]
    if not active_formats:
        logger.warning("All formats are skipped — nothing to do")
        return 0

    logger.info("Active ebook formats: %s", ", ".join(active_formats))
    if skip_formats:
        logger.info("Skipped formats: %s", ", ".join(sorted(skip_formats)))

    # Find combined markdown
    combined_md = _find_combined_markdown(project_root)
    if combined_md is None:
        logger.warning(
            "No combined markdown file found in %s/output/ — "
            "run the PDF rendering stage first (exit 2 = graceful skip)",
            project_root,
        )
        return 2

    logger.info("Source markdown: %s", combined_md)

    # Prepare output directory
    ebook_out_dir = project_root / "output" / "ebook"
    ebook_out_dir.mkdir(parents=True, exist_ok=True)

    # Derive a base filename from the project name (last path component)
    project_slug = project_root.name

    title, author, language = _load_manuscript_metadata(project_root)
    logger.info("Manuscript metadata: title=%r author=%r language=%r", title, author, language)

    # Combined manuscripts reference figures as .pdf (correct for LaTeX, but
    # PDF is not embeddable as an inline EPUB/MOBI/DOCX image — pandoc silently
    # fails to embed such refs, which is a confirmed real-world cause of
    # Amazon KDP rejecting an uploaded EPUB outright). Rewrite to the raster
    # sibling before handing off to the ebook renderers; render from the
    # rewritten copy, not the original.
    original_text = combined_md.read_text(encoding="utf-8")
    rewritten_text = rewrite_pdf_figure_refs_to_raster(original_text, combined_md)
    figures_dir = project_root / "output" / "figures"
    pandoc_extra_args_list = [
        "--resource-path=" + str(combined_md.parent),
        "--resource-path=" + str(figures_dir),
        "--resource-path=" + str(figures_dir.parent),
    ]

    # Without pandoc-crossref, {#fig-x}-style targets (e.g. a manual
    # "[see Figure](#fig-x)" link) don't reliably resolve to a real anchor —
    # confirmed via epubcheck RSC-012 "Fragment identifier is not defined" on
    # a real manuscript. Mirrors the same filter render_combined_docx already
    # applies in _combined_exports.py.
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        pandoc_extra_args_list.extend(["--filter", crossref])
    else:
        logger.warning("pandoc-crossref not on PATH; @fig:/@sec:/@tbl:/@eq: cross-references will not resolve.")

    results: dict[str, tuple[bool, str]] = {}  # format → (success, message)

    try:
        with tempfile.TemporaryDirectory(prefix="ebook_gen_") as tmp_dir:
            render_source = Path(tmp_dir) / combined_md.name
            render_source.write_text(rewritten_text, encoding="utf-8")

            # ── EPUB ──────────────────────────────────────────────────────
            if "epub" in active_formats:
                epub_path = ebook_out_dir / f"{project_slug}.epub"
                logger.info("Rendering EPUB → %s", epub_path)
                try:
                    epub_result = render_epub(
                        render_source,
                        epub_path,
                        cover_image=cover_image,
                        title=title,
                        author=author,
                        language=language,
                        extra_args=list(pandoc_extra_args_list),
                    )
                    size_str = _format_size(epub_result.size_bytes)
                    logger.info(
                        "  ✅ EPUB: %s  (%s, %.1fs)",
                        epub_path.name,
                        size_str,
                        epub_result.duration_seconds,
                    )
                    results["epub"] = (True, f"{size_str} in {epub_result.duration_seconds:.1f}s")
                except Exception as exc:
                    logger.error("  ❌ EPUB rendering failed: %s", exc)
                    results["epub"] = (False, str(exc))

            # ── MOBI ──────────────────────────────────────────────────────
            if "mobi" in active_formats:
                mobi_path = ebook_out_dir / f"{project_slug}.mobi"
                logger.info("Rendering MOBI → %s", mobi_path)
                try:
                    mobi_result = render_mobi(
                        render_source,
                        mobi_path,
                        cover_image=cover_image,
                        title=title,
                        author=author,
                        language=language,
                        pandoc_extra_args=list(pandoc_extra_args_list),
                    )
                    size_str = _format_size(mobi_result.size_bytes)
                    logger.info(
                        "  ✅ MOBI: %s  (%s, %.1fs)",
                        mobi_path.name,
                        size_str,
                        mobi_result.duration_seconds,
                    )
                    results["mobi"] = (True, f"{size_str} in {mobi_result.duration_seconds:.1f}s")
                except Exception as exc:
                    logger.error("  ❌ MOBI rendering failed: %s", exc)
                    results["mobi"] = (False, str(exc))

            # ── DOCX ──────────────────────────────────────────────────────
            if "docx" in active_formats:
                docx_path = ebook_out_dir / f"{project_slug}.docx"
                logger.info("Rendering DOCX → %s", docx_path)
                try:
                    docx_result = render_docx(
                        render_source,
                        docx_path,
                        title=title,
                        author=author,
                        extra_args=list(pandoc_extra_args_list),
                    )
                    size_str = _format_size(docx_result.size_bytes)
                    logger.info(
                        "  ✅ DOCX: %s  (%s, %.1fs)",
                        docx_path.name,
                        size_str,
                        docx_result.duration_seconds,
                    )
                    results["docx"] = (True, f"{size_str} in {docx_result.duration_seconds:.1f}s")
                except Exception as exc:
                    logger.error("  ❌ DOCX rendering failed: %s", exc)
                    results["docx"] = (False, str(exc))

    except Exception as exc:
        logger.error("Unexpected error during ebook generation: %s", exc, exc_info=True)
        return 1

    # ── Summary ───────────────────────────────────────────────────────────
    successes = [fmt for fmt, (ok, _) in results.items() if ok]
    failures = [fmt for fmt, (ok, _) in results.items() if not ok]

    logger.info("")
    logger.info("Ebook generation summary:")
    for fmt, (ok, msg) in results.items():
        icon = "✅" if ok else "❌"
        logger.info("  %s %s: %s", icon, fmt.upper(), msg)

    output_files = list(ebook_out_dir.glob("*"))
    if output_files:
        logger.info("Output directory: %s", ebook_out_dir)
        for f in sorted(output_files):
            size_str = _format_size(f.stat().st_size) if f.is_file() else "dir"
            logger.info("  %s  (%s)", f.name, size_str)

    if failures and not successes:
        logger.error("❌ All ebook formats failed")
        return 1

    if failures:
        logger.warning("⚠️  Some ebook formats failed: %s", ", ".join(failures))
        # Partial success — still return 0 so the pipeline continues
        return 0

    log_success(
        f"✅ Ebook generation complete — {len(successes)} format(s): {', '.join(successes)}",
        logger,
    )
    return 0


__all__ = ["run_ebook_generation"]
