from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Character:
    character_id: str
    name: str
    shape: str
    family_shape: str
    fill: str
    accent: str
    role: str


@dataclass(frozen=True)
class PageSpec:
    number: int
    slug: str
    title: str
    scene: str
    text: str
    overlay_box: bool
    palette: tuple[str, str, str, str]

    @property
    def filename(self) -> str:
        if self.number == 0:
            return "00_cover.png"
        return f"{self.number:02d}_{self.slug}.png"


@dataclass(frozen=True)
class StorybookSpec:
    title: str
    subtitle: str
    output_pdf: Path
    page_width: int
    page_height: int
    characters: tuple[Character, ...]
    pages: tuple[PageSpec, ...]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def page_by_slug(self, slug: str) -> PageSpec:
        for page in self.pages:
            if page.slug == slug:
                return page
        raise KeyError(f"No storybook page with slug {slug!r}")

    def page_by_number(self, number: int) -> PageSpec:
        for page in self.pages:
            if page.number == number:
                return page
        raise KeyError(f"No storybook page numbered {number}")


@dataclass(frozen=True)
class RenderResult:
    output_path: Path
    page_count: int
    image_paths: tuple[Path, ...]
    manifest_path: Path
    summary_path: Path

    def to_dict(self) -> dict[str, object]:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "image_paths": [str(path) for path in self.image_paths],
            "manifest_path": str(self.manifest_path),
            "summary_path": str(self.summary_path),
        }
