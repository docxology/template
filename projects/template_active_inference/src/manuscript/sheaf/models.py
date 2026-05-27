"""Data models for sheaf manuscript composition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

CoverageColor = Literal["black", "white", "gray"]
CoverageStatus = Literal["present", "absent", "missing"]


def coverage_cell_symbol(color: CoverageColor) -> str:
    if color == "black":
        return "P"
    if color == "gray":
        return "M"
    return "—"


ImradBlock = Literal["introduction", "methods", "results", "discussion", "appendix"]
SectionKind = Literal["group", "section"]


class MissingTrackPolicy(str, Enum):
    SKIP = "skip"
    WARN = "warn"
    ERROR = "error"


@dataclass(frozen=True)
class TrackSpec:
    id: str
    order: int
    renderer: str
    label: str
    optional: bool = False


@dataclass(frozen=True)
class SheafDefaults:
    missing_track: MissingTrackPolicy = MissingTrackPolicy.SKIP


@dataclass(frozen=True)
class SheafSection:
    id: str
    title: str
    short: str
    order: int
    tracks: dict[str, str]
    output_name: str
    kind: SectionKind = "section"
    imrad: ImradBlock = "methods"
    depth: int = 1
    compose: bool = True
    track_order: tuple[str, ...] | None = None
    include_tracks: tuple[str, ...] | None = None
    exclude_tracks: tuple[str, ...] | None = None

    def should_compose(self) -> bool:
        return self.compose and self.kind == "section"


@dataclass(frozen=True)
class SheafManifest:
    defaults: SheafDefaults
    sections: tuple[SheafSection, ...]
    registry_path: Path


@dataclass
class ManifestIssue:
    level: str
    code: str
    message: str


@dataclass(frozen=True)
class ComposeOptions:
    enabled_tracks: frozenset[str] | None = None
    section_ids: frozenset[str] | None = None
    missing_track: MissingTrackPolicy | None = None
    strict: bool = False


@dataclass(frozen=True)
class TrackRegistry:
    tracks: dict[str, TrackSpec]
    renderer_suffixes: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class ComposeResult:
    paths: list[Path]
    issues: list[ManifestIssue]


@dataclass(frozen=True)
class CoverageCell:
    track_id: str
    bound: bool
    path: str | None
    status: CoverageStatus
    color: CoverageColor


@dataclass(frozen=True)
class CoverageSectionRow:
    section_id: str
    title: str
    cells: tuple[CoverageCell, ...]
    kind: SectionKind = "section"
    imrad: ImradBlock = "methods"
    depth: int = 1
    compose: bool = True


@dataclass(frozen=True)
class CoverageMatrix:
    track_ids: tuple[str, ...]
    sections: tuple[CoverageSectionRow, ...]

    def gray_cells(self) -> list[tuple[str, str]]:
        missing: list[tuple[str, str]] = []
        for row in self.sections:
            for cell in row.cells:
                if cell.color == "gray":
                    missing.append((row.section_id, cell.track_id))
        return missing


DEFAULT_REGISTRY_REL = Path("manuscript/sheaf/tracks.yaml")
DEFAULT_MANIFEST_REL = Path("manuscript/sheaf/manifest.yaml")

COVERAGE_COLORS: dict[CoverageColor, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "gray": "#808080",
}
