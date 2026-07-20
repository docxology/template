"""Load and validate ``manuscript/config.yaml`` — the book's single source of truth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

import yaml

DEFAULT_MANUSCRIPT = Path(__file__).resolve().parent.parent.parent / "manuscript"


@dataclass(frozen=True)
class UnitIntroRef:
    """One part/unit introduction file declared in config."""

    part_id: str
    part_label: str
    part_title: str
    directory: str
    file: str

    @property
    def stem(self) -> str:
        """Intro file stem (no ``.md``)."""
        return self.file[:-3] if self.file.endswith(".md") else self.file

    def path(self, manuscript_dir: Path) -> Path:
        """Absolute path to the unit intro markdown file."""
        return Path(manuscript_dir) / self.directory / self.file


@dataclass(frozen=True)
class ChapterRef:
    """One chapter located within the book structure."""

    part_id: str
    part_label: str
    part_title: str
    directory: str
    file: str
    title: str
    enabled: bool

    @property
    def stem(self) -> str:
        """Chapter file stem (no ``.md``)."""
        return self.file[:-3] if self.file.endswith(".md") else self.file

    def path(self, manuscript_dir: Path) -> Path:
        """Absolute path to the chapter markdown file."""
        return Path(manuscript_dir) / self.directory / self.file


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load the manuscript config YAML into a dict.

    Args:
        path: Path to ``config.yaml`` or to the manuscript directory containing
            it. Defaults to the project's ``manuscript/config.yaml``.
    """
    if path is None:
        config_path = DEFAULT_MANUSCRIPT / "config.yaml"
    else:
        candidate = Path(path)
        config_path = candidate / "config.yaml" if candidate.is_dir() else candidate
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"config root must be a mapping: {config_path}")
    return data


def unit_blocks(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the book's structural blocks.

    The shared renderer (``infrastructure/rendering``) reads the key ``units``;
    this template uses "Part" as the human-facing term, so ``parts`` is accepted
    as an alias. ``units`` wins if both are present.
    """
    # Presence, rather than truthiness, is significant here: an author who
    # explicitly declares ``units: []`` must not silently fall back to a stale
    # legacy ``parts:`` block elsewhere in the file.
    blocks = config["units"] if "units" in config else config.get("parts")
    return blocks if isinstance(blocks, list) else []


def iter_chapters(config: dict[str, Any], *, include_disabled: bool = False) -> list[ChapterRef]:
    """Flatten ``units -> chapters`` into an ordered list of :class:`ChapterRef`."""
    chapters: list[ChapterRef] = []
    for part in unit_blocks(config):
        if not isinstance(part, dict):
            continue
        part_id = part.get("id", "")
        directory_value = part.get("directory", part_id)
        directory = directory_value if isinstance(directory_value, str) else ""
        chapter_entries = part.get("chapters", [])
        if not isinstance(chapter_entries, list):
            continue
        for chapter in chapter_entries:
            if not isinstance(chapter, dict) or not isinstance(chapter.get("file"), str):
                continue
            enabled = bool(chapter.get("enabled", True))
            if not enabled and not include_disabled:
                continue
            chapters.append(
                ChapterRef(
                    part_id=part_id,
                    part_label=str(part.get("label", "")),
                    part_title=part.get("title", ""),
                    directory=directory,
                    file=chapter["file"],
                    title=chapter.get("title", ""),
                    enabled=enabled,
                )
            )
    return chapters


def iter_unit_intros(config: dict[str, Any]) -> list[UnitIntroRef]:
    """Return declared unit introduction files from ``units`` blocks."""
    intros: list[UnitIntroRef] = []
    for part in unit_blocks(config):
        if not isinstance(part, dict):
            continue
        intro_file = part.get("intro_file")
        if not intro_file:
            continue
        part_id = part.get("id", "")
        directory_value = part.get("directory", part_id)
        directory = directory_value if isinstance(directory_value, str) else ""
        intros.append(
            UnitIntroRef(
                part_id=part_id,
                part_label=str(part.get("label", "")),
                part_title=part.get("title", ""),
                directory=directory,
                file=str(intro_file),
            )
        )
    return intros


def declared_chapter_paths(manuscript_dir: Path, config: dict[str, Any]) -> list[Path]:
    """Return every chapter path declared in config."""
    return [chapter.path(manuscript_dir) for chapter in iter_chapters(config, include_disabled=True)]


def declared_unit_intro_paths(manuscript_dir: Path, config: dict[str, Any]) -> list[Path]:
    """Return every unit intro path declared in config."""
    return [intro.path(manuscript_dir) for intro in iter_unit_intros(config)]


def validate_config(config: dict[str, Any]) -> list[str]:
    """Return a list of human-readable structural problems (empty == valid)."""
    issues: list[str] = []

    book = config.get("book")
    if not isinstance(book, dict) or not book.get("title"):
        issues.append("book.title is required")

    parts = unit_blocks(config)
    if not parts:
        issues.append("units must be a non-empty list")
        return issues

    seen_ids: set[str] = set()
    seen_paths: set[tuple[str, str]] = set()
    seen_intro_paths: set[tuple[str, str]] = set()
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            issues.append(f"units[{index}] must be a mapping")
            continue
        pid = part.get("id")
        if not pid:
            issues.append(f"units[{index}] missing id")
            continue
        if not isinstance(pid, str):
            issues.append(f"units[{index}] id must be a string")
            continue
        if pid in seen_ids:
            issues.append(f"duplicate part id: {pid}")
        seen_ids.add(pid)
        if not part.get("title"):
            issues.append(f"part {pid} missing title")
        directory = part.get("directory", pid)
        issues.extend(_validate_relative_path(directory, f"part {pid} directory", directory_only=True))
        chapters = part.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            issues.append(f"part {pid} has no chapters")
            continue
        intro_file = part.get("intro_file")
        if intro_file is not None:
            issues.extend(_validate_relative_path(intro_file, f"part {pid} intro_file", markdown=True))
            if isinstance(directory, str) and isinstance(intro_file, str):
                intro_key = (directory, intro_file)
                if intro_key in seen_intro_paths:
                    issues.append(f"duplicate unit intro path: {directory}/{intro_file}")
                seen_intro_paths.add(intro_key)

        for chapter_index, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                issues.append(f"part {pid} chapter {chapter_index} must be a mapping")
                continue
            file = chapter.get("file")
            if not file:
                issues.append(f"part {pid} has a chapter with no file")
                continue
            issues.extend(_validate_relative_path(file, f"chapter {pid}/{file}", markdown=True))
            if isinstance(directory, str) and isinstance(file, str):
                key = (directory, file)
                if key in seen_paths:
                    issues.append(f"duplicate chapter file/path: {directory}/{file}")
                seen_paths.add(key)
            if not chapter.get("title"):
                issues.append(f"chapter {pid}/{file} missing title")
    return issues


def _validate_relative_path(
    value: Any, field: str, *, markdown: bool = False, directory_only: bool = False
) -> list[str]:
    """Validate a config path before it is joined to the manuscript root.

    Config paths are author-controlled data but are later used by scaffolding,
    audits, and render discovery. Keep them portable and confined to their
    declared part: reject absolute paths, Windows separators, traversal, and
    nested filenames that would bypass the orphan-file checks.
    """
    if not isinstance(value, str) or not value.strip():
        return [f"{field} must be a non-empty relative path"]

    issues: list[str] = []
    path = PurePosixPath(value)
    if value.startswith(("/", "\\")) or path.is_absolute():
        issues.append(f"{field} must be relative")
    if "\\" in value or any(part == ".." for part in path.parts):
        issues.append(f"{field} must not contain path traversal")
    if directory_only and path.name != value:
        issues.append(f"{field} must be a single directory name")
    if not directory_only and path.name != value:
        issues.append(f"{field} must be a single filename")
    if markdown and not value.endswith(".md"):
        issues.append(f"{field} must end with .md")
    return issues


__all__ = [
    "ChapterRef",
    "DEFAULT_MANUSCRIPT",
    "UnitIntroRef",
    "declared_chapter_paths",
    "declared_unit_intro_paths",
    "iter_chapters",
    "iter_unit_intros",
    "load_config",
    "unit_blocks",
    "validate_config",
]
