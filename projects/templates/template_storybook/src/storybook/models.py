from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Character:
    """Data container for Character."""

    character_id: str
    name: str
    shape: str
    family_shape: str
    fill: str
    accent: str
    role: str


@dataclass(frozen=True)
class PageSpec:
    """Data container for PageSpec."""

    number: int
    slug: str
    title: str
    scene: str
    text: str
    overlay_box: bool
    palette: tuple[str, str, str, str]
    caption_position: str = "bottom"

    @property
    def filename(self) -> str:
        """Process filename."""
        if self.number == 0:
            return "00_cover.png"
        return f"{self.number:02d}_{self.slug}.png"


@dataclass(frozen=True)
class StorybookSpec:
    """Data container for StorybookSpec."""

    title: str
    subtitle: str
    output_pdf: Path
    page_width: int
    page_height: int
    characters: tuple[Character, ...]
    pages: tuple[PageSpec, ...]

    @property
    def page_count(self) -> int:
        """Return the total number of pages."""
        return len(self.pages)

    def page_by_slug(self, slug: str) -> PageSpec:
        """Find a page by its slug."""
        for page in self.pages:
            if page.slug == slug:
                return page
        raise KeyError(f"No storybook page with slug {slug!r}")

    def page_by_number(self, number: int) -> PageSpec:
        """Find a page by its number."""
        for page in self.pages:
            if page.number == number:
                return page
        raise KeyError(f"No storybook page numbered {number}")


@dataclass(frozen=True)
class RenderResult:
    """Data container for RenderResult."""

    output_path: Path
    page_count: int
    image_paths: tuple[Path, ...]
    manifest_path: Path
    summary_path: Path
    contact_sheet_path: Path | None = None

    def to_dict(self, *, root: Path | None = None) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output.

        Generated manifests use project-relative paths when ``root`` is
        provided so a checkout path never becomes publication metadata.
        """

        def serialize(path: Path) -> str:
            if root is not None:
                try:
                    return path.resolve().relative_to(root.resolve()).as_posix()
                except ValueError:
                    pass
            return str(path)

        return {
            "output_path": serialize(self.output_path),
            "page_count": self.page_count,
            "image_paths": [serialize(path) for path in self.image_paths],
            "manifest_path": serialize(self.manifest_path),
            "summary_path": serialize(self.summary_path),
            "contact_sheet_path": serialize(self.contact_sheet_path) if self.contact_sheet_path else None,
        }
