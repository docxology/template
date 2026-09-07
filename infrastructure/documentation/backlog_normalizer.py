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

_BLOCKED_EXTERNAL_IDS = frozenset(
    {
        "DATA-PUBLICATION-1",
        "DATA-MEDIA-1",
        "LIT-ENGINE-POLITENESS-1",
        "REGISTERED-PUBLICATION-1",
        "POOLS-FOURTH-FOND-1",
        "SIA-APPROVAL-FORK-1",
        "ARL-CROSS-PHASE-1",
        "ARL-PHASE-PROVENANCE-1",
    }
)
_BLOCKED_TOOL_IDS = frozenset({"AUTOPOIESIS-SPEC-1", "FORMAL-SPEC-1", "PROSE-LLM-REVIEW-1", "REDACTED-VISUAL-1"})
_PARTIAL_IDS: frozenset[str] = frozenset()
_OPEN_IDS: frozenset[str] = frozenset()


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
        if len(cells) not in {6, 8} or cells[0].casefold() == "id" or set(cells[0]) <= {"-", "—"}:
            continue
        if _ID.fullmatch(cells[0]) and cells[0] not in seen:
            seen.add(cells[0])
            rows.append(cells)
    return rows


def _is_backlog_table_line(line: str) -> bool:
    if not line.startswith("|"):
        return False
    cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
    if len(cells) not in {6, 8}:
        return False
    if cells[0].casefold() == "id" or set(cells[0]) <= {"-", "—"}:
        return True
    return bool(_ID.fullmatch(cells[0]))


def _table(rows: list[tuple[str, ...]]) -> list[str]:
    output = [
        "| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | "
        "Acceptance command | Negative control |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    output.extend("| " + " | ".join(row) + " |" for row in rows)
    return output


def _status_for(identifier: str) -> str:
    if identifier in _BLOCKED_EXTERNAL_IDS:
        return "blocked-external"
    if identifier in _BLOCKED_TOOL_IDS:
        return "blocked-tool"
    if identifier in _PARTIAL_IDS:
        return "partial"
    if identifier in _OPEN_IDS:
        return "open"
    return "open"


def _canonical_acceptance_command(command: str, project_slug: str) -> str:
    """Keep the planned acceptance field executable even when legacy prose was supplied."""
    # A TODO lives inside its exemplar.  Keep its acceptance command runnable
    # from that project root so project-local documentation contracts do not
    # mistake a root-checkout path for a reproducible local command.  The
    # public matrix supplies the checkout-level wrapper when it needs to run
    # every exemplar.
    if re.search(
        rf"(?:uv\s+run\s+pytest|python\s+-m\s+pytest)\s+projects/templates/{re.escape(project_slug)}(?:/|\b)",
        command,
        re.IGNORECASE,
    ):
        return "`uv run pytest tests -q --no-cov --timeout=120`"
    if re.search(
        r"(?:`[^`]+`|\b(?:uv\s+run|pytest|python(?:3)?|ruff|mypy|bandit|bash|sh|make|git\s+|"
        r"scripts/|check_[A-Za-z0-9_./-]+|--check\b))",
        command,
        re.IGNORECASE,
    ):
        return command
    return "`uv run pytest tests -q --no-cov --timeout=120`"


def _normalize_row(row: tuple[str, ...], *, project_slug: str) -> tuple[str, ...]:
    """Migrate a legacy six-field row or validate the shape of a new row."""
    if len(row) == 6:
        identifier, size, dependency, artifact, command, negative = row
        # Active planning is intentionally decomposed into Minor/Medium
        # slices.  Preserve the stable ID while converting legacy release-
        # scale rows into a bounded Medium unblock condition.
        if size.strip().casefold() == "major":
            size = "Medium"
        status = _status_for(identifier.strip("`"))
        action_prefix = {
            "open": "Implement the scoped change",
            "partial": "Complete the remaining scoped work",
            "blocked-external": "Obtain the required owner or external receipt to unblock",
            "blocked-tool": "Install or pin the required tool, or record its unavailable status to unblock",
        }[status]
        acceptance = _canonical_acceptance_command(command, project_slug)
        next_action = f"{action_prefix}; run {acceptance} and attach {artifact}."
        return (identifier, status, size, dependency, next_action, artifact, acceptance, negative)
    if len(row) == 8:
        identifier, status, size, dependency, next_action, artifact, command, negative = row
        if size.strip().casefold() == "major":
            size = "Medium"
        acceptance = _canonical_acceptance_command(command, project_slug)
        if acceptance == command:
            return (identifier, status, size, dependency, next_action, artifact, command, negative)
        return (identifier, status, size, dependency, next_action, artifact, acceptance, negative)
    raise ValueError(f"backlog row must have six legacy or eight current fields: {row!r}")


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


def normalize_backlog(
    path: Path,
    *,
    close_ids: frozenset[str] = frozenset(),
    closure_evidence: str | None = None,
) -> tuple[str, str]:
    """Return a normalized future-only backlog and archived history text."""
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    title = lines[0] if lines and lines[0].startswith("#") else f"# {path.parent.name} TODO"
    sections = _sections(lines)
    rows = [_normalize_row(row, project_slug=path.parent.name) for row in _table_rows(lines)]
    closed_rows = [row for row in rows if row[0].strip("`") in close_ids]
    rows = [row for row in rows if row[0].strip("`") not in close_ids]
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
        "next action, proving artifact, acceptance command, and negative control; absence of an owner or "
        "external receipt",
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
        grouped.setdefault(row[2].strip().title(), []).append(row)
    for size in ("Minor", "Medium", "Major"):
        out.extend([f"## {size} upcoming", ""])
        scoped = grouped.get(size, [])
        # Keep an empty machine-readable scope explicit.  A future-only
        # backlog with no rows is still a valid contract and must not fall
        # back to prose that hides whether the table was accidentally lost.
        out.extend(_table(scoped))
        if not scoped:
            out.append("No active rows are currently scoped at this size.")
        out.append("")
    out.extend(
        [
            "## Backlog status",
            "",
            "Rows remain active until the acceptance command and negative control pass in the same source revision.",
            "A blocked row is a deliberate boundary, not a skipped success.",
            "",
        ]
    )
    normalized = "\n".join(out).rstrip() + "\n"
    archived_parts: list[str] = []
    if removed:
        archived_parts.extend(removed)
    if closed_rows:
        archived_parts.extend(
            [
                f"## Closed active rows {ARCHIVE_DATE}",
                "",
                "The following rows were removed after the same-revision acceptance and negative-control pass.",
                "Closure evidence: "
                + (closure_evidence or "same-revision acceptance receipt recorded by the release workflow."),
                "",
                *_table(closed_rows),
                "",
            ]
        )
    archived = "\n".join(archived_parts).rstrip() + "\n" if archived_parts else ""
    return normalized, archived


def normalize_public_backlogs(
    repo_root: Path | str,
    *,
    write: bool = False,
    close_ids: frozenset[str] = frozenset(),
    closure_evidence: str | None = None,
) -> tuple[int, int]:
    """Normalize all present public exemplar TODOs and optionally archive history."""
    root = Path(repo_root).resolve()
    archive: list[str] = []
    changed = 0
    for name in PUBLIC_PROJECT_NAMES:
        path = root / "projects" / name / "TODO.md"
        if not path.is_file():
            continue
        normalized, removed = normalize_backlog(
            path,
            close_ids=close_ids,
            closure_evidence=closure_evidence,
        )
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
