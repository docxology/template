"""Beamer command preparation, ordered TeX transforms, and overflow validation.

The renderer owns subprocess execution and output lifecycle. This module owns
Beamer-specific preparation shared by archive and accessible profiles.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._bibliography import pandoc_bibliography_args, resolve_bibliography
from infrastructure.rendering._slides_codelisting import make_codelisting_slide_safe
from infrastructure.rendering._slides_framebreaks import split_long_slide_frames
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering._slides_tex_figures import normalize_accessible_projection_latex
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_log_quality import parse_latex_log_findings
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable,
)

logger = get_logger(__name__)
_ACCESSIBLE_BEAMER_ASPECT_RATIO = "169"


def _reject_accessible_beamer_overflow(log_file: Path, compiled_pdf: Path) -> None:
    """Discard a Beamer derivative whose fixed accessible layout overflowed."""

    blocked = {r"Overfull \hbox", r"Overfull \vbox"}
    findings = [
        finding
        for finding in parse_latex_log_findings(log_file, blocked_layout_kinds=blocked)
        if finding.kind in blocked
    ]
    if not findings:
        return
    compiled_pdf.unlink(missing_ok=True)
    examples = [f"{finding.kind} at line {finding.line_number}: {finding.message}" for finding in findings[:5]]
    raise RenderingError(
        "[slides.density.beamer-overflow] Accessible Beamer content exceeds its fixed frame geometry",
        context={
            "diagnostic_code": "slides.density.beamer-overflow",
            "log_file": str(log_file),
            "finding_count": len(findings),
            "examples": examples,
        },
        suggestions=[
            "Split the source at a semantic block boundary or shorten the projected excerpt.",
            "Keep complete prose, captions, and tables in the linked canonical HTML manuscript.",
        ],
    )


def _slide_bibliography_args(manuscript_dir: Path | None) -> list[str]:
    """Return the shared bibliography union for a section-level slide deck.

    Slide decks resolve in-text citations but deliberately suppress the repeated
    reference list: the combined manuscript and the dedicated references deck
    remain the reader-facing bibliography surfaces.
    """
    if manuscript_dir is None:
        return []
    bibliographies = resolve_bibliography(manuscript_dir)
    if not bibliographies:
        return []
    return [
        "--citeproc",
        *pandoc_bibliography_args(bibliographies),
        "--metadata",
        "suppress-bibliography=true",
    ]


def beamer_command(
    config: RenderingConfig,
    source_file: Path,
    temp_tex: Path,
    manuscript_dir: Path | None,
    figures_dir: Path | None,
    *,
    slide_level: int,
) -> list[str]:
    """Prepare Pandoc arguments and the profile-specific math header."""
    output_dir = temp_tex.parent
    # Build pandoc command to convert markdown to LaTeX. A fixed slide
    # level is not safe for manuscript sections: when a source contains
    # h3/h4 headings, treating those headings as Beamer blocks wraps a
    # whole results section in one unbreakable box. Choose the deepest
    # present heading (capped at h4) so the source's semantic breaks
    # become frames; the Lua filter below then lets each frame split when
    # its body is still too long.
    slide_level = 2 if config.slides_profile == "accessible" else slide_level
    cmd = [
        config.pandoc_path,
        str(source_file),
        "-t",
        "beamer",
        "-o",
        str(temp_tex),
        "--standalone",
        f"--slide-level={slide_level}",
    ]
    if config.slides_profile == "accessible":
        cmd.extend(
            [
                "-f",
                "json",
                f"--variable=aspectratio:{_ACCESSIBLE_BEAMER_ASPECT_RATIO}",
            ]
        )

    # Apply the allowframebreaks Lua filter so that long sections
    # without h2 sub-headings still split across slides instead of
    # triggering xelatex driver code 256 on overfull vboxes.
    allowframebreaks_filter = Path(__file__).with_name("_beamer_allowframebreaks.lua")
    if config.slides_profile == "archive" and allowframebreaks_filter.exists():
        cmd.extend(["--lua-filter", str(allowframebreaks_filter)])

    # Keep formalism/equation labels source-owned and automatically
    # numbered in the slide deck just as they are in HTML/PDF/DOCX/EPUB.
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd.extend(["--filter", crossref])
    else:
        logger.warning("pandoc-crossref not on PATH; Beamer formalism numbers may remain unresolved.")

    # Beamer does not run citeproc implicitly. Without these arguments, every
    # manuscript citation survives as literal ``[@key]`` text in the
    # reviewer-facing PDF. Use the shared project bibliography union when
    # available; small renderer unit tests and standalone decks without one
    # retain Pandoc's normal no-bibliography behavior.
    cmd.extend(_slide_bibliography_args(manuscript_dir))

    # Inject the math-font subset of the manuscript preamble so
    # \mid, \ll, \gg etc. render cleanly in slide decks without
    # pulling in the full combined-PDF preamble.
    math_header = write_slides_math_header(
        manuscript_dir,
        output_dir,
        accessible_policy=(config.accessible_slide_policy() if config.slides_profile == "accessible" else None),
    )
    if math_header is not None:
        cmd.extend(["-H", str(math_header)])

    # Add resource paths if provided
    if manuscript_dir:
        cmd.extend(["--resource-path", str(manuscript_dir)])
    if figures_dir:
        cmd.extend(["--resource-path", str(figures_dir)])

    return cmd


def transform_beamer_latex(
    tex_content: str,
    config: RenderingConfig,
    *,
    require_seqsplit: Callable[[], None],
) -> str:
    """Apply ordered slide typography fixes and require wrapping capability.

    Cross-deck references and figure paths have already been resolved by the
    renderer. Preserve this order: listing normalization precedes literal
    wrapping; accessible capability validation precedes figure normalization.
    """
    tex_content, codelisting_replacements = make_codelisting_slide_safe(
        tex_content,
        accessible_body_font_pt=(config.slides_body_font_pt if config.slides_profile == "accessible" else None),
    )
    if codelisting_replacements:
        logger.info("Replaced pandoc-crossref's listing float with a Beamer-safe block")

    # Latin Modern's text face does not provide a literal U+2265 glyph
    # in every size used by Beamer. Keep the semantic comparison while
    # routing it through the math font in either text or math mode.
    tex_content = tex_content.replace("≥", r"\ensuremath{\ge}")

    tex_content, texttt_replacements = make_long_texttt_breakable(tex_content)
    if texttt_replacements:
        logger.info("Made %d long monospace path span(s) breakable in slides", texttt_replacements)

    tex_content, literal_replacements = make_known_literals_breakable(tex_content)
    if literal_replacements:
        logger.info("Made %d recurring long label(s) breakable in slides", literal_replacements)

    tex_content, reference_replacements = make_pandoc_reference_tokens_breakable(tex_content)
    if reference_replacements:
        logger.info(
            "Made %d unresolved cross-reference token(s) breakable in slides",
            reference_replacements,
        )

    if config.slides_profile == "accessible" and any(
        (texttt_replacements, literal_replacements, reference_replacements)
    ):
        require_seqsplit()

    if config.slides_profile == "accessible":
        tex_content, normalized_graphics, removed_empty_captions = normalize_accessible_projection_latex(tex_content)
        if normalized_graphics:
            logger.info("Preserved aspect ratio for %d accessible slide figure(s)", normalized_graphics)
        if removed_empty_captions:
            logger.info("Removed %d empty projected caption(s)", removed_empty_captions)

    # A long scientific caption is part of an unbreakable figure
    # environment. Keep the image legible but leave vertical room for
    # its accessibility/source caption on the same frame.
    figure_fraction = (
        f"{config.slides_min_figure_area_percent / 100:.2f}" if config.slides_profile == "accessible" else "0.40"
    )
    tex_content, graphics_replacements = constrain_includegraphics_textheight(
        tex_content,
        figure_fraction,
    )
    if graphics_replacements:
        logger.info("Constrained %d slide figure height bound(s)", graphics_replacements)

    if config.slides_profile == "archive":
        tex_content, framebreak_replacements = split_long_slide_frames(tex_content)
        if framebreak_replacements:
            logger.info(
                "Inserted safe frame breaks in %d dense slide frame(s)",
                framebreak_replacements,
            )

    return tex_content
