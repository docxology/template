"""Page composition: build column frames and pour flowables into them.

This module is the bridge between the content model and the canvas. For each
page it draws the furniture (via :mod:`newspaper.furniture`), constructs the
column frames — including an optional narrow left *rail* and a spanning lead
headline — and flows the story/box/figure flowables (built by
:mod:`newspaper.components`) across those frames in reading order.

ReportLab's :meth:`Frame.addFromList` does the hard work of splitting paragraphs
across columns; this module's job is purely to *place the frames correctly* and
hand each its slice of content. Any flowables that do not fit are returned so
the caller can report an over-set page rather than silently dropping copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, Frame

from . import furniture as F
from .components import ad_flowables, box_flowables, story_flowables
from .config import NewspaperConfig
from .content import Ad, Box, Edition, Figure, Page, Story
from .geometry import ColumnGrid, PageGeometry
from .typography import MUTED, Fonts


@dataclass
class PageRender:
    """Outcome of rendering one page."""

    number: int
    overset_flowables: int


def _make_frames(grid: ColumnGrid, top: float, bottom: float) -> list[Frame]:
    height = top - bottom
    frames: list[Frame] = []
    for i in range(grid.n_columns):
        frames.append(
            Frame(
                grid.column_x(i),
                bottom,
                grid.column_width,
                height,
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
                showBoundary=0,
            )
        )
    return frames


def _flow(c: Canvas, frames: list[Frame], flowables: list[Flowable]) -> int:
    items = list(flowables)
    for fr in frames:
        if not items:
            break
        fr.addFromList(items, c)
    return len(items)


def _item_flowables(
    item: Story | Box | Figure | Ad,
    styles,
    fonts: Fonts,
    *,
    measure: float,
    project_root: Path,
    classified: bool = False,
) -> list[Flowable]:
    if isinstance(item, Story):
        return story_flowables(item, styles, fonts, measure=measure, project_root=project_root)
    if isinstance(item, Ad):
        return ad_flowables(item, styles, fonts, width=measure, project_root=project_root)
    if isinstance(item, Box):
        # On a classified page, categories flow densely and unboxed; a "display"
        # box is a boxed house/display ad that keeps its border for variety.
        if classified and item.kind != "display":
            from .components import classified_flowables

            return classified_flowables(item, styles)
        return box_flowables(item, styles, fonts, width=measure)
    # Figure
    from .components import figure_flowables

    return figure_flowables(item, measure, styles, project_root)


def render_page(
    c: Canvas,
    page: Page,
    edition: Edition,
    geom: PageGeometry,
    config: NewspaperConfig,
    styles,
    fonts: Fonts,
    project_root: Path,
    spot: object | None = None,
) -> PageRender:
    """Draw furniture and flow all content for a single page."""
    cols = page.columns or config.columns_default
    gutter = config.gutter_points
    body_bottom = geom.content_bottom + F.FOLIO_HEIGHT + 6

    # --- furniture: top of page -------------------------------------------
    if page.template == "front":
        body_top = F.draw_nameplate(c, edition, geom, styles, fonts, spot=spot)
    else:
        body_top = F.draw_section_band(c, page, edition, geom, styles, fonts, spot=spot)
    F.draw_folio(c, page, edition, geom, fonts)

    # The rail is a fixed-width column on the far left, independent of the main
    # grid, so the main columns keep a generous, readable measure. `page.columns`
    # counts the MAIN columns.
    rail_frame: Frame | None = None
    if page.rail:
        rail_w = config.rail_points
        rail_frame = Frame(
            geom.content_left,
            body_bottom,
            rail_w,
            body_top - body_bottom,
            leftPadding=0,
            rightPadding=8,
            topPadding=0,
            bottomPadding=0,
            showBoundary=0,
        )
        main_left = geom.content_left + rail_w + gutter
        main_width = geom.content_right - main_left
        # Rule separating rail from the main well.
        F._vrule(c, geom.content_left + rail_w + gutter / 2.0, body_bottom, body_top, width=0.8, color=MUTED)
    else:
        main_left = geom.content_left
        main_width = geom.content_width

    main_cols = cols
    main_grid = ColumnGrid(main_left, main_width, main_cols, gutter)
    main_top = body_top

    # --- spanning lead headline -------------------------------------------
    if page.lead is not None:
        lead_h = F.draw_lead_headline(c, page.lead, main_left, body_top, main_width, styles, fonts)
        main_top = body_top - lead_h

    F.draw_column_rules(c, main_grid, main_top, body_bottom)
    main_frames = _make_frames(main_grid, main_top, body_bottom)

    if config.draft_grid:  # pragma: no cover - debug only
        overlay = ([rail_frame] if rail_frame else []) + main_frames
        F.draw_draft_grid(c, overlay)

    # --- flow content ------------------------------------------------------
    overset = 0
    if rail_frame is not None:
        rail_flowables: list[Flowable] = []
        for rail_item in page.rail_items:
            rail_flowables.extend(
                _item_flowables(rail_item, styles, fonts, measure=rail_frame.width, project_root=project_root)
            )
        overset += _flow(c, [rail_frame], rail_flowables)

    main_flowables: list[Flowable] = []
    if page.lead is not None:
        main_flowables.extend(
            story_flowables(
                page.lead,
                styles,
                fonts,
                measure=main_grid.column_width,
                project_root=project_root,
                include_headline=False,
            )
        )
    is_classified = page.template == "classified"
    for main_item in page.main_items:
        main_flowables.extend(
            _item_flowables(
                main_item,
                styles,
                fonts,
                measure=main_grid.column_width,
                project_root=project_root,
                classified=is_classified,
            )
        )
    overset += _flow(c, main_frames, main_flowables)

    return PageRender(number=page.number, overset_flowables=overset)


__all__ = ["PageRender", "render_page"]
