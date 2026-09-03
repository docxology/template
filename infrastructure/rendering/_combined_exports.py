"""Combined PDF/HTML/DOCX/EPUB export helpers for the rendering pipeline."""

from __future__ import annotations

import re
import shutil
import subprocess
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError, TemplateError
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.diagnostic import DiagnosticReporter, DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.transmission_bookends import is_transmission_bookend
from infrastructure.rendering import RenderManager
from infrastructure.rendering._bibliography import pandoc_bibliography_args, resolve_bibliography
from infrastructure.rendering._pandoc_filters import formalism_filter_args
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering._pdf_combined_prevalidate import prevalidate_for_render
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering._pdf_title_page_config import _load_render_config, _rendering_options
from infrastructure.rendering._slides_crossref import COMBINED_AUX_BASENAME
from infrastructure.rendering.manuscript_composition import write_manuscript_composition

logger = get_logger(__name__)

# Matches markdown image refs whose target ends in .pdf, e.g.
# ``](../figures/timeline_dark.pdf){#fig-timeline}`` — captures the path.
# Alt text uses a non-greedy ``.*?`` (not ``[^\]]*``) because captions
# routinely contain nested bracket groups from inline citations, e.g.
# ``![...caption text [@fetter1965development; @laughlin1898bimetallism].](path.pdf)``
# — a negated-class ``[^\]]*`` cannot skip over that inner ``]`` at all, so it
# silently fails to match the *entire* ref (leaving affected figures on their
# broken .pdf reference). Non-greedy ``.*?`` correctly extends past inner
# ``]`` characters that aren't immediately followed by ``(``.
_PDF_IMAGE_REF_RE = re.compile(r"(!\[.*?\]\()([^)\s]+\.pdf)(\)|\s)", re.DOTALL)

_RASTER_EXTENSIONS = (".png", ".jpg", ".jpeg")


def rewrite_pdf_figure_refs_to_raster(markdown_text: str, combined_md_path: Path) -> str:
    """Rewrite ``.pdf`` figure references to a raster sibling for non-PDF output.

    Combined manuscripts are written with PDF figure references (LaTeX embeds
    PDF vector graphics directly), but PDF is not a valid inline-image media
    type for EPUB/MOBI/DOCX — pandoc silently fails to embed such references
    (confirmed via epubcheck: ``RSC-007 Referenced resource ... could not be
    found``), which is what triggered a real KDP "couldn't convert your HTML
    file to Kindle format" rejection on a real book upload. Every project that
    combines PDF figures into its ebook output hits this, not just one.

    For each ``.pdf`` reference, checks whether a raster sibling (``.png``,
    then ``.jpg``/``.jpeg``) exists at the resolved location (relative to
    *combined_md_path*'s directory, matching pandoc's own path resolution)
    and rewrites the reference to point to it. References with no raster
    sibling are left untouched (surfaces as a normal missing-resource error
    rather than silently vanishing).
    """

    def _replace(match: re.Match[str]) -> str:
        prefix, ref_path, suffix = match.group(1), match.group(2), match.group(3)
        resolved = (combined_md_path.parent / ref_path).resolve()
        for ext in _RASTER_EXTENSIONS:
            candidate = resolved.with_suffix(ext)
            if candidate.is_file():
                new_ref = ref_path[: -len(".pdf")] + ext
                return f"{prefix}{new_ref}{suffix}"
        logger.warning("No raster sibling found for PDF figure ref %s; leaving as-is (will fail to embed)", ref_path)
        return match.group(0)

    return _PDF_IMAGE_REF_RE.sub(_replace, markdown_text)


def combined_source_files(md_files: list[Path]) -> list[Path]:
    """Return combined-render inputs, ignoring missing generated transmission bookends."""
    combined_files: list[Path] = []
    for path in md_files:
        if path.exists() or not is_transmission_bookend(path):
            combined_files.append(path)
    return combined_files


html_combined_source_files = combined_source_files


def _project_root_for_manuscript(manuscript_dir: Path) -> Path:
    """Resolve the owning project root for source or injected manuscripts."""

    if manuscript_dir.name == "manuscript" and manuscript_dir.parent.name == "output":
        return manuscript_dir.parent.parent
    if manuscript_dir.name == "manuscript" and manuscript_dir.parent.name == "docs":
        return manuscript_dir.parent.parent
    return manuscript_dir.parent


def prepare_shared_combined_markdown(
    manager: RenderManager,
    md_files: list[Path],
    manuscript_dir: Path,
    project_name: str,
) -> Path:
    """Write a current combined source for exports and provenance.

    DOCX and EPUB must not depend on a prior PDF run. The shared source is
    rebuilt from the exact ordered manuscript inputs, receives the same generic
    preprocessing as the combined PDF, and is bound to the composition receipt.
    PDF-only and slides-only runs also use it because the HTML renderer is not
    present to emit the cross-format composition evidence in those lanes.
    """

    source_files = combined_source_files(md_files)
    if not source_files:
        raise RenderingError("Cannot prepare combined manuscript without current Markdown inputs")
    profile = manager.config.security()
    for source_file in source_files:
        profile.validate_source(source_file)
    prevalidate_for_render(source_files, bib_file=None)

    project_config, _ = _load_render_config(manuscript_dir)
    combined_content = combine_manuscript_markdown_sections(
        source_files,
        section_breaks=_rendering_options(project_config)["section_breaks"],
    )
    combined_content = preprocess_combined_markdown(
        combined_content,
        manuscript_dir=manuscript_dir,
    ).content

    project_root = _project_root_for_manuscript(manuscript_dir)
    combined_path = project_root / "output" / "web" / "_combined_manuscript.md"
    profile.validate_output(combined_path)
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = combined_path.with_suffix(combined_path.suffix + ".tmp")
    try:
        temporary.write_text(combined_content, encoding="utf-8")
        temporary.replace(combined_path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    write_manuscript_composition(
        project_root,
        project_name,
        source_files,
        combined_path,
        algorithm="shared-combined-markdown-v1",
    )
    logger.info("Prepared shared combined manuscript: %s", combined_path)
    return combined_path


def resolve_combined_markdown(manuscript_dir: Path) -> Path | None:
    """Find the combined-manuscript markdown produced by the combined-PDF pipeline."""
    project_root = _project_root_for_manuscript(manuscript_dir)
    candidates = [
        project_root / "output" / "pdf" / "_combined_manuscript.md",
        project_root / "output" / "tex" / "_combined_manuscript.md",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def render_combined_docx(
    manager: RenderManager,
    manuscript_dir: Path,
    project_name: str,
    reporter: DiagnosticReporter,
    *,
    combined_md: Path | None = None,
) -> None:
    """Render the combined DOCX from the preprocessed combined markdown."""
    from infrastructure.rendering.docx_renderer import render_docx

    combined_md = combined_md or resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] DOCX rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    docx_dir = Path(manager.config.docx_dir)
    docx_dir.mkdir(parents=True, exist_ok=True)
    out_path = docx_dir / f"{Path(project_name).name}_combined.docx"
    bibliographies = resolve_bibliography(manuscript_dir)

    # Image refs in the combined markdown are written as ``figures/<name>``, so
    # the resource path must be the *parent* of the figures dir (e.g. ``output/``),
    # not the figures dir itself — otherwise pandoc silently drops every image.
    figures_dir = Path(manager.config.figures_dir)
    extra_args = [
        "--resource-path=" + str(manuscript_dir),
        "--resource-path=" + str(figures_dir),
        "--resource-path=" + str(figures_dir.parent),
    ]
    # Same numbering as the PDF edition, and ahead of --citeproc below so
    # [@def:...] never reaches citeproc as an unresolved citation.
    extra_args.extend(formalism_filter_args())

    crossref = shutil.which("pandoc-crossref")
    if crossref:
        extra_args.extend(["--filter", crossref])
    else:
        logger.warning("pandoc-crossref not on PATH; DOCX @fig:/@sec:/@tbl:/@eq: will not resolve.")
    if bibliographies:
        extra_args.append("--citeproc")
        extra_args.extend(pandoc_bibliography_args(bibliographies))

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
    *,
    combined_md: Path | None = None,
    epub_renderer: Callable[..., Any] | None = None,
) -> None:
    """Render the combined EPUB from the preprocessed combined markdown."""
    if epub_renderer is None:
        from infrastructure.rendering.epub_renderer import render_epub

        epub_renderer = render_epub

    combined_md = combined_md or resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] EPUB rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    epub_dir = Path(manager.config.epub_dir)
    epub_dir.mkdir(parents=True, exist_ok=True)
    out_path = epub_dir / f"{Path(project_name).name}_combined.epub"
    bibliographies = resolve_bibliography(manuscript_dir)

    # Same resolution contract as DOCX: image refs are ``figures/<name>``, so the
    # figures dir's parent must be on the resource path or pandoc silently drops them.
    figures_dir = Path(manager.config.figures_dir)
    extra_args = [
        "--resource-path=" + str(manuscript_dir),
        "--resource-path=" + str(figures_dir),
        "--resource-path=" + str(figures_dir.parent),
    ]
    # Without pandoc-crossref, {#fig-x} cross-reference targets (e.g. a manual
    # "[see Figure](#fig-x)" link) don't reliably resolve to a real EPUB anchor
    # — confirmed via epubcheck RSC-012 "Fragment identifier is not defined"
    # on a real manuscript. render_combined_docx already adds this filter;
    # EPUB needs the identical treatment, not a partial subset.
    # Same numbering as the PDF and DOCX editions, and ahead of --citeproc below.
    extra_args.extend(formalism_filter_args())

    crossref = shutil.which("pandoc-crossref")
    if crossref:
        extra_args.extend(["--filter", crossref])
    else:
        logger.warning("pandoc-crossref not on PATH; EPUB @fig:/@sec:/@tbl:/@eq: will not resolve.")
    if bibliographies:
        extra_args.append("--citeproc")
        extra_args.extend(pandoc_bibliography_args(bibliographies))

    from infrastructure.rendering._pdf_title_page import (
        _cover_image_alt,
        _cover_image_path,
        _load_render_config,
        build_pandoc_metadata,
    )

    title: str | None = None
    author: str | None = None
    cover_alt: str | None = None
    language = "en"
    config, config_file = _load_render_config(manuscript_dir)
    if isinstance(config, dict):
        metadata = build_pandoc_metadata(config)
        if metadata.get("title"):
            title = str(metadata["title"])
        authors = metadata.get("author") or []
        if isinstance(authors, list) and authors:
            author = "; ".join(str(item) for item in authors)
        elif isinstance(authors, str) and authors:
            author = authors
        raw_metadata = config.get("metadata") or {}
        if isinstance(raw_metadata, dict) and raw_metadata.get("language"):
            language = str(raw_metadata["language"])
        cover_image = _cover_image_path(config, config_file) if config_file is not None else None
        cover_alt = _cover_image_alt(config)
    else:
        cover_image = None

    logger.debug("\n" + "=" * BANNER_WIDTH)
    logger.info("Generating combined EPUB manuscript...")
    try:
        result = epub_renderer(
            combined_md,
            out_path,
            bibliography=None,
            title=title,
            author=author,
            cover_image=cover_image,
            cover_alt=cover_alt,
            language=language,
            pandoc_path=manager.config.pandoc_path,
            extra_args=extra_args,
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
    combined_pdf_succeeded = False

    if config.enable_pdf:
        if config.enable_slides and md_files:
            _clear_stale_combined_aux(manager)
        logger.debug("\n" + "=" * BANNER_WIDTH)
        logger.info("Generating combined PDF manuscript...")
        try:
            combined_pdf = manager.render_combined_pdf(combined_source_files(md_files), manuscript_dir, project_name)
            logger.info(f"✅ Generated combined PDF: {combined_pdf.name}")
            combined_pdf_succeeded = True
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

    # Standalone slide decks are rendered before the combined manuscript so
    # the ordinary per-file pass can proceed in one sweep. The combined PDF is
    # the authoritative numbering surface, however, and only its retained AUX
    # file contains labels defined in other sections. Refresh every enabled
    # deck after that AUX exists so cross-section references cannot ship as
    # unresolved markers. Archive mode reruns Beamer only. The opt-in
    # accessible profile refreshes its atomic Beamer/Reveal pair so both
    # derivatives receive the same current combined-manuscript numbering.
    if config.enable_slides and md_files:
        if combined_pdf_succeeded:
            _refresh_slides_against_combined_aux(manager, md_files)
        elif config.enable_pdf and config.slides_profile == "accessible":
            # The accessible Beamer/Reveal pair is a canonical derivative of
            # the current combined AUX numbering. A failed combined build
            # leaves only the pre-AUX fallback pass (and may have consumed a
            # prior AUX before it was cleared), so neither member is safe to
            # publish. Archive mode retains its historical standalone output.
            _remove_refresh_decks(manager, _slide_refresh_sources(md_files))

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

    shared_combined_md: Path | None = None
    needs_shared_evidence = (
        config.enable_docx
        or config.enable_epub
        or (not config.enable_html and (config.enable_pdf or config.enable_slides))
    )
    if md_files and needs_shared_evidence:
        shared_combined_md = prepare_shared_combined_markdown(
            manager,
            md_files,
            manuscript_dir,
            project_name,
        )

    if config.enable_docx:
        render_combined_docx(
            manager,
            manuscript_dir,
            project_name,
            reporter,
            combined_md=shared_combined_md,
        )
    else:
        logger.debug("[skip] DOCX rendering disabled in config (default; render.formats.docx=true to enable)")

    if config.enable_epub:
        render_combined_epub(
            manager,
            manuscript_dir,
            project_name,
            reporter,
            combined_md=shared_combined_md,
        )
    else:
        logger.debug("[skip] EPUB rendering disabled in config (default; render.formats.epub=true to enable)")


def _refresh_slides_against_combined_aux(
    manager: RenderManager,
    md_files: list[Path],
) -> None:
    """Re-render slide derivatives after the combined PDF writes its label map.

    A section deck cannot resolve labels owned by another section on its first
    standalone compile. ``SlidesRenderer`` resolves those labels from the
    combined manuscript AUX file when it is available, so this refresh is the
    producer-order bridge between the combined PDF and the slide surfaces.
    Accessible mode refreshes the paired Beamer/Reveal contract atomically;
    archive mode retains its historical Beamer-only behavior.
    Missing transmission bookends and explicitly skipped Beamer sources are
    excluded exactly as they are in the ordinary per-file renderer.
    """
    refresh_sources = _slide_refresh_sources(md_files)

    if not refresh_sources:
        return

    try:
        _require_current_combined_aux(manager)
    except RenderingError:
        _remove_refresh_decks(manager, refresh_sources)
        raise

    logger.info(
        "Refreshing %d slide derivative set(s) against the combined manuscript AUX label map",
        len(refresh_sources),
    )
    failures: list[str] = []
    for source_file in refresh_sources:
        output_file = _slide_pdf_path(manager, source_file)
        try:
            output_file.unlink(missing_ok=True)
            if manager.config.slides_profile == "accessible":
                manager.render_accessible_slide_pair(
                    source_file,
                    strict_cross_deck_refs=True,
                )
            else:
                manager.render_slides(
                    source_file,
                    output_format="beamer",
                    strict_cross_deck_refs=True,
                )
        except (TemplateError, OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
            cleanup_failures: list[str] = []
            for refresh_path in _slide_refresh_paths(manager, source_file):
                try:
                    refresh_path.unlink(missing_ok=True)
                except OSError as cleanup_exc:
                    cleanup_failures.append(str(cleanup_exc))
            cleanup_suffix = f"; cleanup failed: {'; '.join(cleanup_failures)}" if cleanup_failures else ""
            failures.append(f"{source_file.name}: {exc}{cleanup_suffix}")
    if failures:
        raise RenderingError(
            "Combined-PDF AUX slide refresh failed; refusing to publish stale standalone decks: " + "; ".join(failures),
            context={"failed_sources": failures},
        )


def _slide_refresh_sources(md_files: list[Path]) -> list[Path]:
    """Return sources whose slide derivatives depend on combined numbering."""

    refresh_sources: list[Path] = []
    for source_file in combined_source_files(md_files):
        if not source_file.is_file():
            continue
        try:
            source_text = source_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise RenderingError(
                f"Could not inspect slide source before AUX refresh: {exc}",
                context={"source": str(source_file)},
            ) from exc
        if not is_transmission_bookend(source_file) and "<!-- render:skip-beamer -->" not in source_text:
            refresh_sources.append(source_file)
    return refresh_sources


def _combined_aux_path(manager: RenderManager) -> Path:
    """Return the retained combined-manuscript AUX path for *manager*."""
    return Path(manager.config.pdf_dir) / COMBINED_AUX_BASENAME


def _clear_stale_combined_aux(manager: RenderManager) -> None:
    """Remove a prior combined AUX so a successful build must produce a current one."""
    aux_path = _combined_aux_path(manager)
    try:
        aux_path.unlink(missing_ok=True)
    except OSError as exc:
        raise RenderingError(
            "Could not clear the stale combined-manuscript AUX before rendering",
            context={"aux_path": str(aux_path), "error": str(exc)},
        ) from exc


def _require_current_combined_aux(manager: RenderManager) -> None:
    """Require a readable, structurally complete AUX from the current combined build."""
    aux_path = _combined_aux_path(manager)
    if not aux_path.is_file():
        raise RenderingError(
            "Combined PDF succeeded without producing the AUX required for Beamer refresh",
            context={"aux_path": str(aux_path)},
        )
    try:
        aux_text = aux_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RenderingError(
            "Combined-manuscript AUX is unreadable; Beamer refresh cannot be verified",
            context={"aux_path": str(aux_path), "error": str(exc)},
        ) from exc
    if not aux_text.strip():
        raise RenderingError(
            "Combined-manuscript AUX is empty; Beamer refresh cannot be verified",
            context={"aux_path": str(aux_path)},
        )

    if not _has_parseable_aux_structure(aux_text):
        raise RenderingError(
            "Combined-manuscript AUX has no parseable LaTeX structure",
            context={"aux_path": str(aux_path)},
        )


def _has_parseable_aux_structure(aux_text: str) -> bool:
    """Recognize a complete TeX command stream with balanced, unescaped braces."""
    first_content = next(
        (line.lstrip() for line in aux_text.splitlines() if line.strip() and not line.lstrip().startswith("%")),
        "",
    )
    if not first_content.startswith("\\") or "\x00" in aux_text:
        return False

    brace_depth = 0
    escaped = False
    in_comment = False
    for character in aux_text:
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if character == "%" and not escaped:
            in_comment = True
            continue
        if character == "{" and not escaped:
            brace_depth += 1
        elif character == "}" and not escaped:
            brace_depth -= 1
            if brace_depth < 0:
                return False
        if character == "\\":
            escaped = not escaped
        else:
            escaped = False
    return brace_depth == 0


def _slide_pdf_path(manager: RenderManager, source_file: Path) -> Path:
    """Return the canonical standalone Beamer PDF path for *source_file*."""
    return Path(manager.config.slides_dir) / f"{source_file.stem}_slides.pdf"


def _slide_refresh_paths(manager: RenderManager, source_file: Path) -> tuple[Path, ...]:
    """Return every derivative owned by the profile's AUX refresh."""

    pdf_path = _slide_pdf_path(manager, source_file)
    if manager.config.slides_profile != "accessible":
        return (pdf_path,)
    return (pdf_path, pdf_path.with_suffix(".html"))


def _remove_refresh_decks(manager: RenderManager, source_files: list[Path]) -> None:
    """Remove first-pass decks when canonical combined numbering is unavailable."""
    cleanup_failures: list[str] = []
    for source_file in source_files:
        for output_file in _slide_refresh_paths(manager, source_file):
            try:
                output_file.unlink(missing_ok=True)
            except OSError as exc:
                cleanup_failures.append(f"{output_file}: {exc}")
    if cleanup_failures:
        raise RenderingError(
            "Could not remove first-pass slide derivatives after combined-PDF dependency failed",
            context={"cleanup_failures": cleanup_failures},
        )
