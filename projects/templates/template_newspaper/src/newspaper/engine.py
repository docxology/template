"""Top-level render engine: turn an :class:`Edition` into a print-ready PDF.

This is the single entry point the orchestration scripts and tests call. It
registers fonts, builds the stylesheet, opens a canvas at the configured trim
size, renders every page via :mod:`newspaper.layout`, and writes the PDF. It
returns a :class:`RenderResult` summarising page count and any over-set pages so
callers can verify the artifact instead of trusting that it "should work".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.pdfgen.canvas import Canvas

from .config import NewspaperConfig, load_newspaper_config
from .content import Edition, load_edition
from .layout import render_page
from .typography import build_stylesheet, register_fonts


@dataclass
class RenderResult:
    """Summary of a render, suitable for JSON serialisation and assertions."""

    output_path: Path
    page_count: int
    oversets: dict[int, int] = field(default_factory=dict)

    @property
    def all_pages_fit(self) -> bool:
        return not self.oversets

    def to_dict(self) -> dict[str, object]:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "all_pages_fit": self.all_pages_fit,
            "oversets": {str(k): v for k, v in self.oversets.items()},
        }


def render_edition(
    edition: Edition,
    config: NewspaperConfig,
    *,
    project_root: Path,
    output_path: Path | str,
) -> RenderResult:
    """Render ``edition`` to ``output_path`` and return a :class:`RenderResult`."""
    output_path = Path(output_path)
    geom = config.geometry()
    fonts = register_fonts()
    styles = build_stylesheet(fonts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(
        str(output_path),
        pagesize=(geom.width, geom.height),
        invariant=True,
    )
    c.setTitle(f"{edition.nameplate} — {edition.date}")
    c.setAuthor(edition.nameplate)
    c.setSubject(f"{edition.city}, {edition.state}")

    spot = config.spot()
    oversets: dict[int, int] = {}
    for page in edition.pages:
        # White page ground (newsprint stays paper-white in this template).
        c.setFillColor(white)
        c.rect(0, 0, geom.width, geom.height, stroke=0, fill=1)
        result = render_page(c, page, edition, geom, config, styles, fonts, project_root, spot=spot)
        if result.overset_flowables:
            oversets[page.number] = result.overset_flowables
        c.showPage()

    c.save()
    return RenderResult(output_path=output_path, page_count=edition.page_count, oversets=oversets)


def build_and_render(
    project_root: Path | str,
    *,
    content_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> RenderResult:
    """Convenience: load config + edition from ``content/`` and render the PDF."""
    project_root = Path(project_root)
    content_dir = Path(content_dir) if content_dir else project_root / "content"
    config = load_newspaper_config(content_dir)
    edition = load_edition(content_dir)
    if output_path is None:
        output_path = project_root / "output" / "pdf" / f"{config.output_basename}.pdf"
    return render_edition(edition, config, project_root=project_root, output_path=Path(output_path))


__all__ = ["RenderResult", "render_edition", "build_and_render"]
