"""ReportLab slide-drawing primitives for the generic PDF deck renderer.

Split from :mod:`infrastructure.rendering.slide_deck` (line-count gate); the
parent module imports these private ``_draw_*`` helpers from here so both
renderers keep consuming one shared drawing implementation. Private companion —
the public API stays in ``slide_deck``.
"""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.slide_deck import (
    CONTENT_BODY_FONT_SIZE,
    CONTENT_HEADER_FONT_SIZE,
    ContentSlideLayout,
    DIAGRAM_HEADER_FONT_SIZE,
    DeckTheme,
    MARGIN,
    QR_SIZE,
    QUOTE_ATTRIBUTION_FONT_SIZE,
    QUOTE_FONT_SIZE,
    RenderingError,
    SECTION_FONT_SIZE,
    SECTION_RULE_BOTTOM_PT,
    SECTION_RULE_HEIGHT_PT,
    SECTION_TITLE_BASELINE_PT,
    SLIDE_TEXT_WIDTH_PT,
    SOURCE_FOOTER_FONT_SIZE,
    STAT_LABEL_FONT_SIZE,
    STAT_TITLE_FONT_SIZE,
    STAT_VALUE_FONT_SIZE,
    SUBTITLE_FONT_SIZE,
    Slide,
    TITLE_FONT_SIZE,
    fit_helvetica_bold_single_line_font_size,
    plan_diagram_figure_layout,
    source_url,
)

logger = get_logger(__name__)


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
