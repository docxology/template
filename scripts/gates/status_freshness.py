#!/usr/bin/env python3
"""Fail when the subsystem verification ledger has gone stale."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_LEDGER_HEADER = (
    "id",
    "subsystem",
    "last verified",
    "verified by",
    "verification scope",
    "command",
    "receipt",
    "mode",
    "health",
)
_LAST_UPDATED = re.compile(r"^\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
_EXECUTABLE = re.compile(r"(?:`[^`]+`|\b(?:uv\s+run|pytest|python|ruff|mypy|bash|git\s+|scripts/))", re.I)
_VERIFICATION_MODES = {"automated", "manual", "external", "optional-tool"}


@dataclass(frozen=True)
class StatusRow:
    """One parsed subsystem verification row."""

    subsystem: str
    verified_on: date
    line_number: int
    identifier: str = ""
    verified_by: str = ""
    verification_scope: str = ""
    command: str = ""
    receipt: str = ""
    mode: str = ""
    health: str = ""


def parse_status_rows(text: str) -> list[StatusRow]:
    """Parse dated rows from the versioned verification ledger table."""
    rows: list[StatusRow] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if len(cells) != len(_LEDGER_HEADER) or tuple(cell.casefold() for cell in cells) == _LEDGER_HEADER:
            continue
        if all(set(cell) <= {"-", "—"} for cell in cells):
            continue
        try:
            verified_on = date.fromisoformat(cells[2])
        except ValueError:
            continue
        rows.append(
            StatusRow(
                subsystem=cells[1],
                verified_on=verified_on,
                line_number=line_number,
                identifier=cells[0],
                verified_by=cells[3],
                verification_scope=cells[4],
                command=cells[5],
                receipt=cells[6],
                mode=cells[7],
                health=cells[8],
            )
        )
    return rows


def freshness_findings(
    text: str,
    *,
    as_of: date | None = None,
    max_age_days: int = 183,
) -> list[str]:
    """Return fail-closed freshness findings for a status document."""
    if max_age_days < 1:
        raise ValueError("max_age_days must be positive")
    effective_date = as_of or date.today()
    rows = parse_status_rows(text)
    findings: list[str] = []
    if not rows:
        findings.append("STATUS.md has no dated subsystem verification rows")
        return findings

    header = next(
        (
            tuple(cell.strip().casefold() for cell in line.strip().strip("|").split("|"))
            for line in text.splitlines()
            if line.lstrip().startswith("|")
        ),
        (),
    )
    if header != _LEDGER_HEADER:
        findings.append("STATUS.md verification ledger must use the nine-field ID/command/receipt/mode schema")
    for row in rows:
        required = {
            "stable ID": row.identifier,
            "verified by": row.verified_by,
            "verification scope": row.verification_scope,
            "command": row.command,
            "receipt": row.receipt,
            "verification mode": row.mode,
            "health": row.health,
        }
        for label, value in required.items():
            if not value.strip():
                findings.append(f"{row.subsystem}: missing {label} (line {row.line_number})")
        if row.command.strip() and not _EXECUTABLE.search(row.command):
            findings.append(f"{row.subsystem}: command is not executable (line {row.line_number})")
        if row.mode.strip() and row.mode.casefold() not in _VERIFICATION_MODES:
            findings.append(f"{row.subsystem}: unsupported verification mode {row.mode!r} (line {row.line_number})")

    threshold = effective_date - timedelta(days=max_age_days)
    for row in rows:
        if row.verified_on > effective_date:
            findings.append(
                f"{row.subsystem}: verification date {row.verified_on.isoformat()} "
                f"is in the future (line {row.line_number})"
            )
        elif row.verified_on < threshold:
            age = (effective_date - row.verified_on).days
            findings.append(
                f"{row.subsystem}: last verified {row.verified_on.isoformat()} "
                f"({age} days old; maximum {max_age_days}, line {row.line_number})"
            )

    header_match = _LAST_UPDATED.search(text)
    if header_match is None:
        findings.append("STATUS.md is missing its **Last updated:** date")
    else:
        try:
            header_date = date.fromisoformat(header_match.group(1))
        except ValueError:
            findings.append("STATUS.md **Last updated:** date is invalid")
        else:
            if header_date > effective_date:
                findings.append("STATUS.md **Last updated:** date is in the future")
            elif header_date < threshold:
                age = (effective_date - header_date).days
                findings.append(f"STATUS.md **Last updated:** is {age} days old; refresh the ledger header")
    return findings


def validate_status_file(
    status_path: Path,
    *,
    as_of: date | None = None,
    max_age_days: int = 183,
) -> list[str]:
    """Validate one ``STATUS.md`` path and return human-readable findings."""
    try:
        text = status_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {status_path}: {exc}"]
    return freshness_findings(text, as_of=as_of, max_age_days=max_age_days)


def main(argv: list[str] | None = None) -> int:
    """Run the status freshness gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="Evaluation date in YYYY-MM-DD format (defaults to today).",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=183,
        help="Maximum permitted ledger age (default: 183 days / six months).",
    )
    args = parser.parse_args(argv)
    findings = validate_status_file(
        args.repo_root.resolve() / "STATUS.md",
        as_of=args.as_of,
        max_age_days=args.max_age_days,
    )
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print(f"STATUS.md freshness: OK (max age {args.max_age_days} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
