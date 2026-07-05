"""Table of contents: chapter numbering and lab/question title derivation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textbook.config import ChapterRef, iter_chapters


@dataclass(frozen=True)
class TocEntry:
    """A numbered table-of-contents entry for one chapter."""

    number: int
    part_label: str
    part_title: str
    title: str
    part_id: str
    file: str


def build_toc(config: dict[str, Any]) -> list[TocEntry]:
    """Return chapters numbered sequentially across the whole book (1..N)."""
    entries: list[TocEntry] = []
    for number, chapter in enumerate(iter_chapters(config), start=1):
        entries.append(
            TocEntry(
                number=number,
                part_label=chapter.part_label,
                part_title=chapter.part_title,
                title=chapter.title,
                part_id=chapter.part_id,
                file=chapter.file,
            )
        )
    return entries


def chapter_number(config: dict[str, Any], part_id: str, file: str) -> int:
    """Return the 1-based sequential number of a chapter, or raise if absent."""
    for entry in build_toc(config):
        if entry.part_id == part_id and entry.file == file:
            return entry.number
    raise KeyError(f"chapter not found: {part_id}/{file}")


def unit_intro_label(part_id: str) -> str:
    """Pandoc-crossref label for a unit introduction: ``sec:<part>_intro``."""
    return f"sec:{part_id}_intro"


def section_label(chapter: ChapterRef) -> str:
    """Pandoc-crossref label for a chapter heading: ``sec:<part>_<stem>``."""
    return f"sec:{chapter.part_id}_{chapter.stem}"


def lab_label(chapter: ChapterRef) -> str:
    """Pandoc-crossref label for a chapter's lab: ``sec:lab_<part>_<stem>``."""
    return f"sec:lab_{chapter.part_id}_{chapter.stem}"


def question_label(chapter: ChapterRef) -> str:
    """Pandoc-crossref label for a chapter's question bank: ``sec:q_<part>_<stem>``."""
    return f"sec:q_{chapter.part_id}_{chapter.stem}"


def lab_title(chapter_title: str) -> str:
    """Display title for a chapter's lab activity."""
    return f"Lab — {chapter_title}"


def question_bank_title(chapter_title: str) -> str:
    """Display title for a chapter's question bank."""
    return f"Question Bank — {chapter_title}"


__all__ = [
    "TocEntry",
    "build_toc",
    "chapter_number",
    "lab_label",
    "lab_title",
    "question_bank_title",
    "question_label",
    "section_label",
    "unit_intro_label",
]
