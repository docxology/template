"""Manuscript structure audit — shared gate for CLI and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textbook import content
from textbook.config import (
    ChapterRef,
    UnitIntroRef,
    declared_chapter_paths,
    declared_unit_intro_paths,
    iter_chapters,
    iter_unit_intros,
    validate_config,
)


_SKIPPED_PART_DOCS = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


@dataclass(frozen=True)
class AuditReport:
    """Structured result of :func:`run_manuscript_audit`."""

    problems: tuple[str, ...]
    rows: tuple[str, ...]
    total_words: int
    total_stubs: int


def format_audit_table(rows: tuple[str, ...], total_words: int, total_stubs: int) -> str:
    """Return the human-readable audit summary block."""
    lines = ["Chapter audit:", *rows, "", f"Totals: {total_words} words, {total_stubs} stub markers remaining"]
    return "\n".join(lines)


def orphan_part_markdown_paths(manuscript_dir: Path, config: dict[str, Any]) -> list[Path]:
    """Return markdown files under ``part_*`` directories not declared in config."""
    declared = {path.resolve() for path in declared_chapter_paths(manuscript_dir, config)}
    declared |= {path.resolve() for path in declared_unit_intro_paths(manuscript_dir, config)}
    orphans: list[Path] = []
    for part_dir in sorted(manuscript_dir.glob("part_*")):
        if not part_dir.is_dir():
            continue
        for markdown in sorted(part_dir.glob("*.md")):
            if markdown.name in _SKIPPED_PART_DOCS:
                continue
            if markdown.resolve() not in declared:
                orphans.append(markdown)
    return orphans


def _record_problem(problems: list[str], message: str, *, require_present: bool) -> None:
    if require_present:
        problems.append(message)


def _audit_chapter(
    chapter: ChapterRef,
    manuscript_dir: Path,
    project_dir: Path,
    *,
    require_present: bool,
    problems: list[str],
) -> tuple[str, int, int]:
    chapter_path = chapter.path(manuscript_dir)
    lab_path = manuscript_dir / "labs" / chapter.part_id / f"lab_{chapter.stem}.md"
    question_path = manuscript_dir / "questions" / chapter.part_id / f"q_{chapter.stem}.md"

    if not chapter_path.exists():
        _record_problem(
            problems,
            f"missing chapter file: {chapter_path.relative_to(project_dir)}",
            require_present=require_present,
        )
        return f"  {chapter.part_id:>8} {chapter.stem:<26} MISSING", 0, 0

    text = chapter_path.read_text(encoding="utf-8")
    issues = content.validate_chapter(text)
    for issue in issues:
        problems.append(f"{chapter.part_id}/{chapter.file}: {issue}")

    stubs = content.count_stub_markers(text)
    words = content.count_words(text)

    for label, path in (("lab", lab_path), ("question", question_path)):
        if not path.exists():
            _record_problem(
                problems,
                f"missing {label} file: {path.relative_to(project_dir)}",
                require_present=require_present,
            )

    status = "OK" if not issues else "FAIL"
    row = f"  {chapter.part_id:>8} {chapter.stem:<26} words={words:>5} stubs={stubs:>3} {status}"
    return row, words, stubs


def _audit_unit_intro(
    intro: UnitIntroRef,
    manuscript_dir: Path,
    project_dir: Path,
    *,
    require_present: bool,
    problems: list[str],
) -> tuple[str, int, int]:
    intro_path = intro.path(manuscript_dir)
    if not intro_path.exists():
        _record_problem(
            problems,
            f"missing unit intro file: {intro_path.relative_to(project_dir)}",
            require_present=require_present,
        )
        return f"  {intro.part_id:>8} {'unit_intro':<26} MISSING", 0, 0

    text = intro_path.read_text(encoding="utf-8")
    issues = content.validate_unit_intro(text)
    for issue in issues:
        problems.append(f"{intro.part_id}/{intro.file}: {issue}")

    stubs = content.count_stub_markers(text)
    words = content.count_words(text)
    status = "OK" if not issues else "FAIL"
    row = f"  {intro.part_id:>8} {'unit_intro':<26} words={words:>5} stubs={stubs:>3} {status}"
    return row, words, stubs


def run_manuscript_audit(
    project_dir: Path,
    config: dict[str, Any],
    *,
    require_present: bool = True,
) -> AuditReport:
    """Validate declared manuscript files and return a structured audit report."""
    manuscript_dir = project_dir / "manuscript"
    problems: list[str] = list(validate_config(config))
    rows: list[str] = []
    total_words = 0
    total_stubs = 0

    for intro in iter_unit_intros(config):
        row, words, stubs = _audit_unit_intro(
            intro,
            manuscript_dir,
            project_dir,
            require_present=require_present,
            problems=problems,
        )
        rows.append(row)
        total_words += words
        total_stubs += stubs

    for chapter in iter_chapters(config):
        row, words, stubs = _audit_chapter(
            chapter,
            manuscript_dir,
            project_dir,
            require_present=require_present,
            problems=problems,
        )
        rows.append(row)
        total_words += words
        total_stubs += stubs

    for orphan in orphan_part_markdown_paths(manuscript_dir, config):
        problems.append(f"orphan markdown under part directory: {orphan.relative_to(project_dir)}")

    return AuditReport(
        problems=tuple(problems),
        rows=tuple(rows),
        total_words=total_words,
        total_stubs=total_stubs,
    )


__all__ = [
    "AuditReport",
    "format_audit_table",
    "orphan_part_markdown_paths",
    "run_manuscript_audit",
]
