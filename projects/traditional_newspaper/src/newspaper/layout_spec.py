"""Physical and typographic constants for tabloid newspaper PDF layout."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewspaperLayout:
    """Immutable layout parameters shared by preamble, tests, and documentation."""

    column_count: int = 3
    column_sep_in: float = 0.22
    paper_width_in: float = 11.0
    paper_height_in: float = 17.0
    margin_in: float = 0.45
    body_font_pt: int = 9

    def geometry_latex_options(self) -> str:
        """Options string for ``geometry`` (no leading comma)."""
        return (
            f"paperwidth={self.paper_width_in}in, "
            f"paperheight={self.paper_height_in}in, "
            f"margin={self.margin_in}in"
        )

    def multicol_sep_latex(self) -> str:
        """Set column separation in LaTeX (requires ``multicol``)."""
        return f"\\setlength{{\\columnsep}}{{{self.column_sep_in}in}}"


LAYOUT = NewspaperLayout()


def column_count_valid(n: int) -> bool:
    """Return True if ``n`` is a reasonable ``multicols`` count (2–8)."""
    return isinstance(n, int) and 2 <= n <= 8
