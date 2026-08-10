"""Normalize canonical exemplar backlogs into future-only scoped tables."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

ARCHIVE_DATE = "2026-08-09"
_ID = re.compile(r"^`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)`?$")
_REMOVED_HEADINGS = {
    "Current validation evidence",
    "Ordered improvement ladder",
    "Promotion Rule",
    "Promotion rule",
    "Active backlog index",
}
_GENERATED_HEADINGS = {
    "Backlog operating rules",
    "Backlog status",
    "Minor upcoming",
    "Medium upcoming",
    "Major upcoming",
}


def _sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                sections.append(current)
            current = (line[3:].strip(), [])
        elif current is not None:
            current[1].append(line)
    if current is not None:
        sections.append(current)
    return sections


def _table_rows(lines: list[str]) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    seen: set[str] = set()
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if len(cells) != 6 or cells[0].casefold() == "id" or set(cells[0]) <= {"-", "—"}:
            continue
        if _ID.fullmatch(cells[0]) and cells[0] not in seen:
            seen.add(cells[0])
            rows.append(cells)
    return rows


def _is_backlog_table_line(line: str) -> bool:
    if not line.startswith("|"):
        return False
    cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
    if len(cells) != 6:
        return False
    if cells[0].casefold() == "id" or set(cells[0]) <= {"-", "—"}:
        return True
    return bool(_ID.fullmatch(cells[0]))


def _table(rows: list[tuple[str, ...]]) -> list[str]:
    output = [
        "| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    output.extend("| " + " | ".join(row) + " |" for row in rows)
    return output


def _clean_body(lines: list[str]) -> list[str]:
    """Trim and collapse blank lines so normalization is idempotent."""
    cleaned: list[str] = []
    for line in lines:
        if not line.strip() and cleaned and not cleaned[-1].strip():
            continue
        cleaned.append(line)
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return cleaned


def normalize_backlog(path: Path) -> tuple[str, str]:
    """Return a normalized future-only backlog and archived history text."""
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    title = lines[0] if lines and lines[0].startswith("#") else f"# {path.parent.name} TODO"
    sections = _sections(lines)
    rows = _table_rows(lines)
    removed: list[str] = []
    retained: list[tuple[str, list[str]]] = []
    for heading, body in sections:
        if heading in _REMOVED_HEADINGS:
            removed.extend([f"## {heading}", *body, ""])
        elif heading in _GENERATED_HEADINGS:
            continue
        else:
            retained.append((heading, _clean_body([line for line in body if not _is_backlog_table_line(line)])))

    out: list[str] = [
        title,
        "",
        "This backlog is future-only. Completed validation and dated review evidence are preserved in",
        "[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)",
        "or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,",
        "proving artifact, acceptance command, and negative control; absence of an owner or external receipt",
        "keeps a capability blocked rather than silently promoting it.",
        "",
        "## Backlog operating rules",
        "",
        "- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.",
        "- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.",
        "- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips",
        "  or blockers.",
        "- Re-derive counts and receipts from live source data; never copy measurements into this planning file.",
        "",
    ]
    for heading, body in retained:
        out.extend([f"## {heading}", "", *body, ""])

    grouped: dict[str, list[tuple[str, ...]]] = {"Minor": [], "Medium": [], "Major": []}
    for row in rows:
        grouped.setdefault(row[1].strip().title(), []).append(row)
    for size in ("Minor", "Medium", "Major"):
        out.extend([f"## {size} upcoming", ""])
        scoped = grouped.get(size, [])
        out.extend(_table(scoped) if scoped else ["No active rows are currently scoped at this size."])
        out.append("")
    out.extend(
        [
            "## Backlog status",
            "",
            "Rows remain active until the acceptance command and negative control pass in the same source revision.",
            "A blocked major row is a deliberate boundary, not a skipped success.",
            "",
        ]
    )
    normalized = "\n".join(out).rstrip() + "\n"
    archived = "\n".join(removed).rstrip() + "\n" if removed else ""
    return normalized, archived


def normalize_public_backlogs(repo_root: Path | str, *, write: bool = False) -> tuple[int, int]:
    """Normalize all present public exemplar TODOs and optionally archive history."""
    root = Path(repo_root).resolve()
    archive: list[str] = []
    changed = 0
    for name in PUBLIC_PROJECT_NAMES:
        path = root / "projects" / name / "TODO.md"
        if not path.is_file():
            continue
        normalized, removed = normalize_backlog(path)
        if normalized != path.read_text(encoding="utf-8"):
            changed += 1
            if write:
                path.write_text(normalized, encoding="utf-8")
        if removed:
            archive.extend(
                [
                    f"### `{path.parent.name}`",
                    "",
                    f"The following pre-normalization sections were archived on {ARCHIVE_DATE}:",
                    "",
                    removed,
                    "",
                ]
            )
    if write and archive:
        history = root / "docs" / "maintenance" / "exemplar-backlog-history.md"
        with history.open("a", encoding="utf-8") as handle:
            handle.write(f"\n## Archived {ARCHIVE_DATE} future-only backlog migration\n\n")
            handle.write("\n".join(archive))
    return changed, len(archive) // 6


__all__ = ["normalize_backlog", "normalize_public_backlogs"]
