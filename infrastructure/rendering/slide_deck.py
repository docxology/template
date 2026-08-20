"""Generic slide-deck content model + ReportLab PDF renderer.

This module is the PDF-generation sibling of :mod:`infrastructure.rendering.pptx_deck`
— both consume the same :class:`DeckContent` so a PDF and a PPTX built from
identical content stay in exact slide-count/text parity. It is deliberately
generic (no pitch-deck-specific or project-specific strings appear here): any
project that needs slide-shaped output can build a :class:`DeckContent` and
call :func:`render_pdf`.

Follows the ``template_newspaper`` / ``template_storybook`` precedent of using
ReportLab directly (not the LaTeX/pandoc manuscript pipeline) for layout-heavy,
non-manuscript output — but as a project-agnostic *format* renderer, it lives in
``infrastructure/rendering/`` alongside :mod:`infrastructure.rendering.docx_renderer`
and :mod:`infrastructure.rendering.epub_renderer` rather than in a single
project's ``src/`` (unlike the newspaper/storybook column-layout engines, a
slide deck is a generic, reusable output shape, not a domain-specific one).

**Theme**: black + white base with three configurable highlight colors
(:class:`DeckTheme`) — pass all three the same hex for a monochrome deck, or
distinct hex values for a multi-accent palette.

**Diligence deep-links**: a :class:`Slide` may carry a ``source`` citation
(e.g. a repo-relative path). When ``source_base_url`` is passed to
:func:`render_pdf` / the PPTX sibling, that citation renders as a real
clickable hyperlink (``canvas.linkURL`` in the PDF, a run hyperlink in the
PPTX) to ``source_base_url + source`` — every factual slide can point
straight at the file that backs its claim.

**Per-slide QR deep-link**: a :class:`Slide` may also carry a ``qr_url`` —
when set, a scannable QR code (reusing
:func:`infrastructure.steganography.barcode_generators.generate_qr_code`) is
drawn in the bottom-right corner of the slide (and made clickable in the PDF
too, via `canvas.linkURL`). Intended use: point it at that slide's own
standalone, citable location on GitHub (see the pitch-deck project's
``src/standalone_slides.py``), so a photo of a printed or projected slide can
be traced back to its exact source — not just the deck as a whole.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: 16:9 widescreen page, matching standard slide-deck aspect ratio.
PAGE_SIZE = landscape((10 * inch, 5.625 * inch))
MARGIN = 0.55 * inch

# Font sizes — shared across the PDF and PPTX renderers (`pptx_deck.py` imports
# these directly) so both stay in exact size parity, not just text/slide-count
# parity. Sized for real presentation use (screen-shared/projected 16:9, not
# read up close like body text) — a bullet list readable from the back of a
# room needs to be meaningfully larger than default document body text.
TITLE_FONT_SIZE = 36
SUBTITLE_FONT_SIZE = 18
SECTION_FONT_SIZE = 33
CONTENT_HEADER_FONT_SIZE = 24
CONTENT_BODY_FONT_SIZE = 18
STAT_TITLE_FONT_SIZE = 22
STAT_VALUE_FONT_SIZE = 68
STAT_LABEL_FONT_SIZE = 19
QUOTE_FONT_SIZE = 25
QUOTE_ATTRIBUTION_FONT_SIZE = 16
DIAGRAM_HEADER_FONT_SIZE = 22
SOURCE_FOOTER_FONT_SIZE = 9

#: Bottom-right QR code side length.
QR_SIZE = 0.62 * inch

# Shared PDF/PPTX title and content geometry.  Both renderers consume these
# point-valued constants so they cannot silently diverge through format-local
# width estimates or text-box heuristics.
SLIDE_TEXT_WIDTH_PT = PAGE_SIZE[0] - 2 * MARGIN
HELVETICA_FONT_NAME = "Helvetica"
HELVETICA_BOLD_FONT_NAME = "Helvetica-Bold"
MIN_SINGLE_LINE_FONT_SIZE_PT = 14
CONTENT_BODY_LINE_HEIGHT_PT = 21.0
CONTENT_BULLET_GAP_PT = 0.46 * inch * 0.25
CONTENT_BODY_FIRST_BASELINE_PT = PAGE_SIZE[1] - 1.35 * inch
CONTENT_PROTECTED_FLOOR_PT = 0.12 * inch + QR_SIZE + 0.15 * inch

# Section-divider geometry is expressed once in points so the PPTX renderer
# can place its title frame and rule in the same non-intersecting bands as the
# ReportLab path.  The PPTX frame is deliberately bounded above the rule;
# allowing the default one-inch text box to straddle the rule lets Office and
# LibreOffice draw the rule through the title glyphs.
SECTION_RULE_BOTTOM_PT = PAGE_SIZE[1] / 2 - 2
SECTION_RULE_HEIGHT_PT = 3.0
SECTION_RULE_TOP_FROM_TOP_PT = PAGE_SIZE[1] - SECTION_RULE_BOTTOM_PT - SECTION_RULE_HEIGHT_PT
SECTION_TITLE_BASELINE_PT = PAGE_SIZE[1] / 2 + 0.25 * inch
SECTION_TITLE_RULE_GAP_PT = 0.15 * inch
SECTION_TITLE_BOX_HEIGHT_PT = SECTION_FONT_SIZE * 1.2
SECTION_TITLE_BOX_TOP_PT = SECTION_RULE_TOP_FROM_TOP_PT - SECTION_TITLE_RULE_GAP_PT - SECTION_TITLE_BOX_HEIGHT_PT

# Diagram figures occupy one shared, footer-safe content box.  The top starts
# below the 0.75-inch header and its accent rule; the bottom is the same
# protected floor used by body text, leaving the source footer and QR code
# unobstructed.  Both PDF and PPTX fit the intrinsic image aspect ratio inside
# this box rather than scaling by width alone.
DIAGRAM_FIGURE_TOP_FROM_TOP_PT = 1.0 * inch
DIAGRAM_FIGURE_BOTTOM_PT = CONTENT_PROTECTED_FLOOR_PT
DIAGRAM_FIGURE_MAX_WIDTH_PT = SLIDE_TEXT_WIDTH_PT
DIAGRAM_FIGURE_MAX_HEIGHT_PT = PAGE_SIZE[1] - DIAGRAM_FIGURE_TOP_FROM_TOP_PT - DIAGRAM_FIGURE_BOTTOM_PT


@dataclass(frozen=True)
class DeckTheme:
    """Black + white base plus three configurable highlight colors.

    Set all three highlights to the same hex for a monochrome deck (e.g. all
    ``"#B3131A"`` red); set distinct values for a multi-accent palette. Every
    other color in a rendered deck derives from these five values — there are
    no other hardcoded colors in the renderer.
    """

    black: str = "#0A0A0A"
    white: str = "#FFFFFF"
    highlight_1: str = "#B3131A"
    highlight_2: str = "#B3131A"
    highlight_3: str = "#B3131A"

    @property
    def black_c(self) -> colors.Color:
        """Return the theme's black color as a ReportLab ``colors.Color``."""
        return colors.HexColor(self.black)

    @property
    def white_c(self) -> colors.Color:
        """Return the theme's white color as a ReportLab ``colors.Color``."""
        return colors.HexColor(self.white)

    @property
    def highlight_1_c(self) -> colors.Color:
        """Return the first highlight color as a ReportLab ``colors.Color``."""
        return colors.HexColor(self.highlight_1)

    @property
    def highlight_2_c(self) -> colors.Color:
        """Return the second highlight color as a ReportLab ``colors.Color``."""
        return colors.HexColor(self.highlight_2)

    @property
    def highlight_3_c(self) -> colors.Color:
        """Return the third highlight color as a ReportLab ``colors.Color``."""
        return colors.HexColor(self.highlight_3)


#: Monochrome-red default — literally "black + white plus 3 highlight colors
#: all red" as a safe, always-available starting palette. Projects override by
#: constructing their own `DeckTheme` (e.g. from `manuscript/config.yaml`).
DEFAULT_THEME = DeckTheme()


@dataclass(frozen=True)
class Slide:
    """One slide's content, independent of render target.

    Attributes:
        title: Slide headline.
        bullets: Body bullet points (rendered as a bulleted list on
            ``content``/``diagram`` slides, on both PDF and PPTX targets).
        kind: Layout hint — ``"title"`` (deck opener/closer), ``"section"``
            (section-divider), ``"content"`` (default: title + bullets),
            ``"stat"`` (one large highlighted number + label), ``"quote"``
            (a pull-quote + attribution), or ``"diagram"`` (title + a large
            full-bleed figure, e.g. a rendered Mermaid diagram).
        notes: Optional speaker notes (PPTX only — ReportLab PDF has no
            notes-pane concept, so these are silently omitted from `render_pdf`).
        figure_path: Optional path to a pre-rendered image (e.g. a matplotlib
            or Mermaid-rendered PNG). Never fetched over the network — local
            file only. Used by ``content`` (small, below bullets) and
            ``diagram`` (large, full-bleed) slides.
        stat_value: Big highlighted figure for ``kind="stat"`` (e.g. "89 tests").
        stat_label: Supporting label below `stat_value` for ``kind="stat"``.
        quote_text: The quotation body for ``kind="quote"``.
        quote_attribution: Who/what is being quoted, for ``kind="quote"``.
        source: Optional diligence citation (e.g. a repo-relative path this
            slide's claim traces to). Rendered as a small footer citation,
            and as a real hyperlink when `render_pdf`/the PPTX renderer is
            given a ``source_base_url``.
        qr_url: Optional fully-formed URL for a per-slide QR deep-link,
            rendered bottom-right on every slide kind. Typically points at
            this exact slide's own standalone page on GitHub (computed by the
            caller — this module never constructs URLs itself), so a photo of
            a projected/printed slide can be traced back to its exact source.
    """

    title: str
    bullets: tuple[str, ...] = ()
    kind: str = "content"
    notes: str = ""
    figure_path: Path | None = None
    stat_value: str = ""
    stat_label: str = ""
    quote_text: str = ""
    quote_attribution: str = ""
    source: str = ""
    qr_url: str = ""


@dataclass(frozen=True)
class DeckContent:
    """A full deck: title/subtitle front matter plus an ordered slide list."""

    title: str
    subtitle: str = ""
    slides: tuple[Slide, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def sections(self) -> tuple[Slide, ...]:
        """Alias for ``slides`` — content-slide count, used for PDF/PPTX parity checks."""
        return self.slides


@dataclass(frozen=True)
class ContentSlideLayout:
    """Exact shared line plan for one content slide.

    ``bullet_lines`` and ``line_baselines_pt`` are consumed directly by both
    renderers.  The plan therefore owns wrapping and vertical-fit decisions;
    PDF and PPTX are not allowed to independently estimate the same text.
    """

    bullet_lines: tuple[tuple[str, ...], ...]
    line_baselines_pt: tuple[tuple[float, ...], ...]
    line_widths_pt: tuple[tuple[float, ...], ...]
    last_glyph_bottom_pt: float
    body_top_pt: float
    body_height_pt: float
    figure_y_pt: float | None = None
    figure_height_pt: float | None = None


@dataclass(frozen=True)
class DiagramFigureLayout:
    """Aspect-preserving figure placement shared by PDF and PPTX.

    ``bottom_pt`` uses ReportLab's bottom-origin coordinates; ``top_pt`` uses
    PowerPoint's top-origin coordinates.  The remaining dimensions are common
    to both formats.
    """

    left_pt: float
    bottom_pt: float
    top_pt: float
    width_pt: float
    height_pt: float


class SlideBudget(Enum):
    """Maximum content-slide counts for the three published deck lengths.

    MEDIUM/LONG raised 25/48 → 32/52 (2026-07-09) for a "scientific integrity
    methods" section, then 32/52 → 38/58 (same day) for an infrastructure/
    introspection section plus an expanded funding/consulting ask. SHORT
    raised 10 → 11 (same day) to fit a real "cite this deck" slide — the
    deck's own citable identity is audience-facing content, not something to
    compress into presenter-only notes just to preserve a slide-count budget.
    """

    SHORT = 11
    MEDIUM = 38
    LONG = 58

    @property
    def max_slides(self) -> int:
        """Return the maximum slide count for this deck budget."""
        return self.value


def filter_deck_for_budget(deck: DeckContent, budget: SlideBudget) -> DeckContent:
    """Return a new :class:`DeckContent` truncated to ``budget.max_slides``.

    Pure function: the same ``(deck, budget)`` pair always yields the same
    output, and slide order/content is never mutated — only trimmed from the
    tail. Title/section slides count toward the budget like any other slide.
    """
    trimmed = deck.slides[: budget.max_slides]
    return DeckContent(
        title=deck.title,
        subtitle=deck.subtitle,
        slides=trimmed,
        metadata=dict(deck.metadata),
    )


def source_url(source: str, source_base_url: str) -> str | None:
    """Build a deep-link URL for a slide's `source` citation, or ``None``.

    Absolute URLs in ``source`` (already starting with ``http``) pass
    through unchanged; a repo-relative path is joined onto
    ``source_base_url``. Returns ``None`` when either piece is empty, so
    callers can render a plain (non-linked) citation.
    """
    if not source:
        return None
    if source.startswith("http://") or source.startswith("https://"):
        return source
    if not source_base_url:
        return None
    return source_base_url.rstrip("/") + "/" + source.lstrip("/")


def render_pdf(
    deck: DeckContent,
    output_path: Path,
    *,
    theme: DeckTheme = DEFAULT_THEME,
    source_base_url: str = "",
) -> Path:
    """Render ``deck`` to a 16:9 slide-shaped PDF at ``output_path``.

    One PDF page per slide (plus the deck title as the first page when the
    first slide isn't already ``kind == "title"``). Uses ReportLab's raw
    canvas API only — no LaTeX/pandoc dependency, matching the
    ``template_newspaper`` precedent for layout-controlled output.

    ``source_base_url`` (e.g. a GitHub blob-view prefix), when given, turns
    every slide's `Slide.source` citation into a real clickable link via
    `canvas.linkURL`. Every slide whose `Slide.qr_url` is set also gets a
    scannable (and clickable) QR code bottom-right.

    Rendered with ``invariant=1`` so two runs against identical `deck`/`theme`
    input produce byte-identical output — ReportLab otherwise stamps
    ``/CreationDate`` with the wall-clock time, which would make "regenerate
    and diff" reproducibility checks (this project's own core claim) fail on
    metadata alone despite identical content.
    """
    if not deck.slides:
        raise RenderingError("Cannot render a deck with zero slides", context={"deck_title": deck.title})
    layouts = validate_deck_layout(deck)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE, invariant=1)
    page_width, page_height = PAGE_SIZE

    needs_title_page = not deck.slides or deck.slides[0].kind != "title"
    if needs_title_page:
        _draw_title_page(c, page_width, page_height, deck.title, deck.subtitle, theme)
        c.showPage()

    for slide, content_layout in zip(deck.slides, layouts, strict=True):
        if slide.kind == "title":
            _draw_title_page(c, page_width, page_height, slide.title, deck.subtitle, theme)
        elif slide.kind == "section":
            _draw_section_slide(c, page_width, page_height, slide.title, theme)
        elif slide.kind == "stat":
            _draw_stat_slide(c, page_width, page_height, slide, theme)
        elif slide.kind == "quote":
            _draw_quote_slide(c, page_width, page_height, slide, theme)
        elif slide.kind == "diagram":
            _draw_diagram_slide(c, page_width, page_height, slide, theme)
        else:
            if content_layout is None:  # pragma: no cover - guarded by validate_deck_layout
                raise RenderingError("Missing content-slide layout", context={"slide_title": slide.title})
            _draw_content_slide(c, page_width, page_height, slide, theme, content_layout)
        _draw_source_footer(c, page_width, slide, theme, source_base_url)
        _draw_qr_code(c, page_width, slide)
        c.showPage()

    c.save()
    return output_path


def _draw_source_footer(c: canvas.Canvas, width: float, slide: Slide, theme: DeckTheme, source_base_url: str) -> None:
    if not slide.source:
        return
    url = source_url(slide.source, source_base_url)
    label = f"Source: {slide.source}"
    font_name, font_size = "Helvetica-Oblique", SOURCE_FOOTER_FONT_SIZE
    c.setFont(font_name, font_size)
    c.setFillColor(colors.HexColor("#8a8f99"))
    text_x, text_y = MARGIN, 0.22 * inch
    c.drawString(text_x, text_y, label)
    if url:
        text_width = c.stringWidth(label, font_name, font_size)
        c.linkURL(url, (text_x, text_y - 2, text_x + text_width, text_y + font_size), relative=0)


def _draw_qr_code(c: canvas.Canvas, width: float, slide: Slide) -> None:
    """Draw a scannable + clickable QR code bottom-right, if `slide.qr_url` is set.

    Reuses `infrastructure.steganography.barcode_generators.generate_qr_code`
    (the same QR generator the steganography layer uses) rather than
    duplicating QR-encoding logic.
    """
    if not slide.qr_url:
        return
    from infrastructure.steganography.barcode_generators import generate_qr_code

    png_bytes = generate_qr_code(slide.qr_url, box_size=3, border=1)
    x = width - MARGIN - QR_SIZE
    y = 0.12 * inch
    c.drawImage(ImageReader(io.BytesIO(png_bytes)), x, y, width=QR_SIZE, height=QR_SIZE, mask="auto")
    c.linkURL(slide.qr_url, (x, y, x + QR_SIZE, y + QR_SIZE), relative=0)


def _draw_title_page(
    c: canvas.Canvas, width: float, height: float, title: str, subtitle: str, theme: DeckTheme
) -> None:
    c.setFillColor(theme.black_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(theme.highlight_1_c)
    c.rect(0, height / 2 - 1.05 * inch, 0.12 * inch, 1.9 * inch, fill=1, stroke=0)
    title_bottom = _draw_wrapped(
        c,
        title,
        MARGIN,
        height / 2 + 0.55 * inch,
        width - 2 * MARGIN,
        42,
        theme.white_c,
        "Helvetica-Bold",
        font_size=TITLE_FONT_SIZE,
    )
    if subtitle:
        # Start below wherever the (possibly multi-line) title actually ended,
        # never at a fixed offset — a wrapped two-line title would otherwise
        # overlap a subtitle placed at a title-height-agnostic position.
        _draw_wrapped(
            c,
            subtitle,
            MARGIN,
            title_bottom - 0.2 * inch,
            width - 2 * MARGIN,
            22,
            colors.HexColor("#c9c9c9"),
            "Helvetica",
            font_size=SUBTITLE_FONT_SIZE,
        )


def _draw_section_slide(c: canvas.Canvas, width: float, height: float, title: str, theme: DeckTheme) -> None:
    c.setFillColor(theme.white_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(theme.highlight_1_c)
    c.rect(
        MARGIN,
        SECTION_RULE_BOTTOM_PT,
        width - 2 * MARGIN,
        SECTION_RULE_HEIGHT_PT,
        fill=1,
        stroke=0,
    )
    section_font_size = fit_helvetica_bold_single_line_font_size(
        title, max_width_pt=SLIDE_TEXT_WIDTH_PT, start_size_pt=SECTION_FONT_SIZE
    )
    c.setFont("Helvetica-Bold", section_font_size)
    c.setFillColor(theme.black_c)
    c.drawString(MARGIN, SECTION_TITLE_BASELINE_PT, title)


def _draw_content_slide(
    c: canvas.Canvas,
    width: float,
    height: float,
    slide: Slide,
    theme: DeckTheme,
    layout: ContentSlideLayout,
) -> None:
    c.setFillColor(theme.white_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Header band + title
    c.setFillColor(theme.black_c)
    c.rect(0, height - 0.9 * inch, width, 0.9 * inch, fill=1, stroke=0)
    c.setFillColor(theme.white_c)
    title_font_size = fit_helvetica_bold_single_line_font_size(
        slide.title,
        max_width_pt=SLIDE_TEXT_WIDTH_PT,
        start_size_pt=CONTENT_HEADER_FONT_SIZE,
    )
    c.setFont("Helvetica-Bold", title_font_size)
    c.drawString(MARGIN, height - 0.62 * inch, slide.title)
    c.setFillColor(theme.highlight_1_c)
    c.rect(0, height - 0.92 * inch, width, 0.04 * inch, fill=1, stroke=0)

    # Bullets
    c.setFont("Helvetica", CONTENT_BODY_FONT_SIZE)
    for lines, baselines in zip(layout.bullet_lines, layout.line_baselines_pt, strict=True):
        for line, baseline in zip(lines, baselines, strict=True):
            c.setFillColor(theme.black_c)
            c.drawString(MARGIN, baseline, line)

    if slide.figure_path is not None:
        if slide.figure_path.is_file():
            if layout.figure_y_pt is None or layout.figure_height_pt is None:
                raise RenderingError("Missing content-figure layout", context={"slide_title": slide.title})
            fig_width = width - 2 * MARGIN
            fig_height = layout.figure_height_pt
            fig_y = layout.figure_y_pt
            c.drawImage(
                str(slide.figure_path),
                MARGIN,
                fig_y,
                width=fig_width,
                height=fig_height,
                preserveAspectRatio=True,
                anchor="c",
            )
        else:
            logger.warning(
                "Slide %r declares figure_path=%s but the file does not exist — "
                "rendering the slide without it rather than failing silently.",
                slide.title,
                slide.figure_path,
            )


def _draw_stat_slide(c: canvas.Canvas, width: float, height: float, slide: Slide, theme: DeckTheme) -> None:
    c.setFillColor(theme.white_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(theme.black_c)
    c.setFont("Helvetica-Bold", STAT_TITLE_FONT_SIZE)
    c.drawString(MARGIN, height - 0.7 * inch, slide.title)

    value = slide.stat_value or (slide.bullets[0] if slide.bullets else "")
    c.setFillColor(theme.highlight_2_c)
    c.setFont("Helvetica-Bold", STAT_VALUE_FONT_SIZE)
    c.drawString(MARGIN, height / 2 - 0.1 * inch, value)

    if slide.stat_label:
        c.setFillColor(theme.black_c)
        _draw_wrapped(
            c,
            slide.stat_label,
            MARGIN,
            height / 2 - 0.8 * inch,
            width - 2 * MARGIN,
            22,
            theme.black_c,
            "Helvetica",
            font_size=STAT_LABEL_FONT_SIZE,
        )


def _draw_quote_slide(c: canvas.Canvas, width: float, height: float, slide: Slide, theme: DeckTheme) -> None:
    c.setFillColor(theme.black_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(theme.highlight_3_c)
    c.rect(MARGIN, height / 2 + 0.9 * inch, 0.55 * inch, 0.08 * inch, fill=1, stroke=0)

    quote_bottom = _draw_wrapped(
        c,
        f"“{slide.quote_text}”",
        MARGIN,
        height / 2 + 0.6 * inch,
        width - 2 * MARGIN,
        31,
        theme.white_c,
        "Helvetica-Oblique",
        font_size=QUOTE_FONT_SIZE,
    )
    if slide.quote_attribution:
        c.setFillColor(theme.highlight_3_c)
        c.setFont("Helvetica-Bold", QUOTE_ATTRIBUTION_FONT_SIZE)
        c.drawString(MARGIN, quote_bottom - 0.15 * inch, f"— {slide.quote_attribution}")


def _draw_diagram_slide(c: canvas.Canvas, width: float, height: float, slide: Slide, theme: DeckTheme) -> None:
    c.setFillColor(theme.white_c)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(theme.black_c)
    c.rect(0, height - 0.75 * inch, width, 0.75 * inch, fill=1, stroke=0)
    c.setFillColor(theme.white_c)
    diagram_title_font_size = fit_helvetica_bold_single_line_font_size(
        slide.title,
        max_width_pt=SLIDE_TEXT_WIDTH_PT,
        start_size_pt=DIAGRAM_HEADER_FONT_SIZE,
    )
    c.setFont("Helvetica-Bold", diagram_title_font_size)
    c.drawString(MARGIN, height - 0.51 * inch, slide.title)
    c.setFillColor(theme.highlight_2_c)
    c.rect(0, height - 0.77 * inch, width, 0.04 * inch, fill=1, stroke=0)

    if slide.figure_path is not None:
        if slide.figure_path.is_file():
            figure_layout = plan_diagram_figure_layout(slide.figure_path)
            c.drawImage(
                str(slide.figure_path),
                figure_layout.left_pt,
                figure_layout.bottom_pt,
                width=figure_layout.width_pt,
                height=figure_layout.height_pt,
            )
        else:
            logger.warning(
                "Slide %r declares figure_path=%s but the file does not exist — "
                "rendering the slide without it rather than failing silently.",
                slide.title,
                slide.figure_path,
            )


def plan_diagram_figure_layout(figure_path: Path) -> DiagramFigureLayout:
    """Fit one real image inside the shared diagram content box.

    The intrinsic pixel ratio is the sole sizing input.  No DPI metadata or
    format-local width heuristic can therefore make the two renderers choose
    different geometry.
    """
    image_width, image_height = ImageReader(str(figure_path)).getSize()
    if image_width <= 0 or image_height <= 0:
        raise RenderingError(
            "Diagram figure has invalid intrinsic dimensions",
            context={
                "figure_path": str(figure_path),
                "image_width": image_width,
                "image_height": image_height,
            },
        )

    scale = min(
        DIAGRAM_FIGURE_MAX_WIDTH_PT / image_width,
        DIAGRAM_FIGURE_MAX_HEIGHT_PT / image_height,
    )
    fitted_width = image_width * scale
    fitted_height = image_height * scale
    left = MARGIN + (DIAGRAM_FIGURE_MAX_WIDTH_PT - fitted_width) / 2
    bottom = DIAGRAM_FIGURE_BOTTOM_PT + (DIAGRAM_FIGURE_MAX_HEIGHT_PT - fitted_height) / 2
    top = PAGE_SIZE[1] - bottom - fitted_height
    return DiagramFigureLayout(
        left_pt=left,
        bottom_pt=bottom,
        top_pt=top,
        width_pt=fitted_width,
        height_pt=fitted_height,
    )


def fit_helvetica_bold_single_line_font_size(
    text: str,
    *,
    max_width_pt: float,
    start_size_pt: int,
    min_size_pt: int = MIN_SINGLE_LINE_FONT_SIZE_PT,
) -> int:
    """Return the largest whole-point Helvetica-Bold size that fits exactly.

    This pure ReportLab-metric helper is the single title-sizing authority for
    PDF and PPTX.  It raises at the legibility floor rather than knowingly
    returning a size whose rendered title still overflows.
    """
    for size_pt in range(start_size_pt, min_size_pt - 1, -1):
        if pdfmetrics.stringWidth(text, HELVETICA_BOLD_FONT_NAME, size_pt) <= max_width_pt:
            return size_pt
    measured_width = pdfmetrics.stringWidth(text, HELVETICA_BOLD_FONT_NAME, min_size_pt)
    raise RenderingError(
        "Single-line slide title does not fit at the minimum font size",
        context={
            "title": text,
            "minimum_font_size_pt": min_size_pt,
            "measured_width_pt": round(measured_width, 3),
            "available_width_pt": round(max_width_pt, 3),
        },
    )


def _wrap_content_lines(text: str, *, slide_title: str) -> tuple[str, ...]:
    """Wrap one content bullet with exact Helvetica glyph measurements."""
    words = text.split()
    if not words:
        return ()
    lines: list[str] = []
    current = ""
    for word in words:
        word_width = pdfmetrics.stringWidth(word, HELVETICA_FONT_NAME, CONTENT_BODY_FONT_SIZE)
        if word_width > SLIDE_TEXT_WIDTH_PT:
            raise RenderingError(
                "Content slide contains an unbreakable word wider than the text area",
                context={
                    "slide_title": slide_title,
                    "word": word,
                    "measured_width_pt": round(word_width, 3),
                    "available_width_pt": round(SLIDE_TEXT_WIDTH_PT, 3),
                },
            )
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, HELVETICA_FONT_NAME, CONTENT_BODY_FONT_SIZE) <= SLIDE_TEXT_WIDTH_PT:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return tuple(lines)


def plan_content_slide_layout(slide: Slide) -> ContentSlideLayout:
    """Build and validate the exact content-line plan shared by both formats."""
    bullet_lines: list[tuple[str, ...]] = []
    line_baselines: list[tuple[float, ...]] = []
    line_widths: list[tuple[float, ...]] = []
    cursor_y = CONTENT_BODY_FIRST_BASELINE_PT
    for index, bullet in enumerate(slide.bullets):
        lines = _wrap_content_lines(f"•  {bullet}", slide_title=slide.title)
        baselines = tuple(cursor_y - line_index * CONTENT_BODY_LINE_HEIGHT_PT for line_index in range(len(lines)))
        widths = tuple(pdfmetrics.stringWidth(line, HELVETICA_FONT_NAME, CONTENT_BODY_FONT_SIZE) for line in lines)
        bullet_lines.append(lines)
        line_baselines.append(baselines)
        line_widths.append(widths)
        if baselines:
            cursor_y = baselines[-1] - CONTENT_BODY_LINE_HEIGHT_PT
        if index < len(slide.bullets) - 1:
            cursor_y -= CONTENT_BULLET_GAP_PT

    ascent, descent = pdfmetrics.getAscentDescent(HELVETICA_FONT_NAME, CONTENT_BODY_FONT_SIZE)
    all_baselines = tuple(value for group in line_baselines for value in group)
    last_glyph_bottom = (all_baselines[-1] + descent) if all_baselines else CONTENT_BODY_FIRST_BASELINE_PT
    if last_glyph_bottom < CONTENT_PROTECTED_FLOOR_PT:
        raise RenderingError(
            "Content slide text enters the protected footer/QR band",
            context={
                "slide_title": slide.title,
                "bullet_count": len(slide.bullets),
                "wrapped_line_count": len(all_baselines),
                "last_glyph_bottom_pt": round(last_glyph_bottom, 3),
                "protected_floor_pt": round(CONTENT_PROTECTED_FLOOR_PT, 3),
                "overflow_pt": round(CONTENT_PROTECTED_FLOOR_PT - last_glyph_bottom, 3),
            },
        )

    figure_y: float | None = None
    figure_height: float | None = None
    if slide.figure_path is not None:
        figure_y = CONTENT_PROTECTED_FLOOR_PT
        figure_top = last_glyph_bottom - 0.15 * inch
        figure_height = min(1.9 * inch, figure_top - figure_y)
        if figure_height < 0.6 * inch:
            raise RenderingError(
                "Content slide figure has no non-overlapping space below its bullets",
                context={
                    "slide_title": slide.title,
                    "figure_height_pt": round(figure_height, 3),
                    "minimum_figure_height_pt": round(0.6 * inch, 3),
                },
            )

    body_top = PAGE_SIZE[1] - (CONTENT_BODY_FIRST_BASELINE_PT + ascent)
    body_height = max(
        CONTENT_BODY_LINE_HEIGHT_PT,
        PAGE_SIZE[1] - last_glyph_bottom - body_top,
    )
    return ContentSlideLayout(
        bullet_lines=tuple(bullet_lines),
        line_baselines_pt=tuple(line_baselines),
        line_widths_pt=tuple(line_widths),
        last_glyph_bottom_pt=last_glyph_bottom,
        body_top_pt=body_top,
        body_height_pt=body_height,
        figure_y_pt=figure_y,
        figure_height_pt=figure_height,
    )


def validate_deck_layout(deck: DeckContent) -> tuple[ContentSlideLayout | None, ...]:
    """Preflight every fitted title and content body before target mutation."""
    layouts: list[ContentSlideLayout | None] = []
    for slide in deck.slides:
        if slide.kind == "section":
            fit_helvetica_bold_single_line_font_size(
                slide.title, max_width_pt=SLIDE_TEXT_WIDTH_PT, start_size_pt=SECTION_FONT_SIZE
            )
            layouts.append(None)
        elif slide.kind == "diagram":
            fit_helvetica_bold_single_line_font_size(
                slide.title, max_width_pt=SLIDE_TEXT_WIDTH_PT, start_size_pt=DIAGRAM_HEADER_FONT_SIZE
            )
            if slide.figure_path is not None and slide.figure_path.is_file():
                plan_diagram_figure_layout(slide.figure_path)
            layouts.append(None)
        elif slide.kind in {"title", "stat", "quote"}:
            layouts.append(None)
        else:
            fit_helvetica_bold_single_line_font_size(
                slide.title, max_width_pt=SLIDE_TEXT_WIDTH_PT, start_size_pt=CONTENT_HEADER_FONT_SIZE
            )
            layouts.append(plan_content_slide_layout(slide))
    return tuple(layouts)


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    color: colors.Color,
    font_name: str,
    font_size: float | None = None,
) -> float:
    """Word-wrap ``text`` within ``max_width`` and draw it starting at ``(x, y)``.

    ``font_size`` defaults to a size proportional to ``line_height`` when not
    given explicitly (kept for backward compatibility); every call site in
    this module now passes ``font_size`` explicitly from the module-level
    font-size constants, so multi-line wrapping is always driven by one real
    measurement, never an inferred size.

    Returns the y-coordinate just below the last drawn line, for stacking
    subsequent content (e.g. placing a subtitle beneath a title that may have
    wrapped to more than one line).
    """
    if font_size is None:
        font_size = 13 if line_height <= 15 else 26

    c.setFont(font_name, font_size)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    cursor_y = y
    for line in lines:
        c.setFillColor(color)
        c.drawString(x, cursor_y, line)
        cursor_y -= line_height
    return cursor_y
