"""Page and column geometry for the newspaper layout engine.

This module is intentionally **pure** — no ReportLab imports, no I/O. Everything
here is arithmetic over points (1 point = 1/72 inch), which makes the column
mathematics trivially unit-testable. The layout engine (:mod:`newspaper.layout`)
and the furniture renderer (:mod:`newspaper.furniture`) consume these structures
to place frames and draw rules.

The default page is **US Tabloid / Ledger, 11in x 17in, portrait** — the classic
large-format community-newspaper trim. A broadsheet folds a Ledger sheet, so a
Tabloid page reads as a genuine "large-format newsletter" while still rendering
crisply on screen and printing on a single sheet.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Points per inch — ReportLab's native unit is the point.
POINT = 1.0
INCH = 72.0


@dataclass(frozen=True)
class PageGeometry:
    """Trim size and margins for a single page, in points.

    All downstream geometry derives from these eight numbers. Margins are the
    white border outside the printable furniture; the *content box* is the
    rectangle inside the margins where the nameplate, columns and folio live.
    """

    width: float = 11.0 * INCH
    height: float = 17.0 * INCH
    margin_top: float = 0.46 * INCH
    margin_bottom: float = 0.55 * INCH
    margin_left: float = 0.5 * INCH
    margin_right: float = 0.5 * INCH

    @property
    def content_left(self) -> float:
        return self.margin_left

    @property
    def content_right(self) -> float:
        return self.width - self.margin_right

    @property
    def content_width(self) -> float:
        return self.content_right - self.content_left

    @property
    def content_top(self) -> float:
        """Top of the content box (y grows upward in PDF space)."""
        return self.height - self.margin_top

    @property
    def content_bottom(self) -> float:
        return self.margin_bottom

    @property
    def content_height(self) -> float:
        return self.content_top - self.content_bottom


@dataclass(frozen=True)
class ColumnGrid:
    """A horizontal grid of equal columns within a region.

    ``column_x`` returns the left edge of column *i*; ``column_width`` is the
    measure of a single column. Gutters are the whitespace between columns; the
    hairline column rules are drawn centred in each gutter by the furniture
    layer.
    """

    left: float
    width: float
    n_columns: int
    gutter: float = 0.16 * INCH

    def __post_init__(self) -> None:
        if self.n_columns < 1:
            raise ValueError(f"n_columns must be >= 1, got {self.n_columns}")
        if self.width <= 0:
            raise ValueError(f"grid width must be > 0, got {self.width}")
        if self.gutter < 0:
            raise ValueError(f"gutter must be >= 0, got {self.gutter}")
        if self.column_width <= 0:
            raise ValueError(f"{self.n_columns} columns + gutters do not fit in width {self.width:.1f}pt")

    @property
    def total_gutter(self) -> float:
        return self.gutter * (self.n_columns - 1)

    @property
    def column_width(self) -> float:
        return (self.width - self.total_gutter) / self.n_columns

    def column_x(self, index: int) -> float:
        """Left edge of column ``index`` (0-based).

        Raises:
            IndexError: if ``index`` is not in ``0 .. n_columns - 1``.
        """
        if not 0 <= index < self.n_columns:
            raise IndexError(f"column {index} out of range 0..{self.n_columns - 1}")
        return self.left + index * (self.column_width + self.gutter)

    def gutter_centers(self) -> list[float]:
        """X positions of the centre of each interior gutter (rule positions).

        A grid of *n* columns has *n − 1* interior gutters; a single-column
        grid returns an empty list.
        """
        centers: list[float] = []
        for i in range(self.n_columns - 1):
            edge = self.column_x(i) + self.column_width
            centers.append(edge + self.gutter / 2.0)
        return centers

    def right(self) -> float:
        """Right edge of the grid (``left + width``)."""
        return self.left + self.width
