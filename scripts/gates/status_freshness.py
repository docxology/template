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
_LEDGER_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|")
_LAST_UPDATED = re.compile(r"^\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)


@dataclass(frozen=True)
class StatusRow:
    """One parsed subsystem verification row."""

    subsystem: str
    verified_on: date
    line_number: int


def parse_status_rows(text: str) -> list[StatusRow]:
    """Parse dated rows from the verification ledger table."""
    rows: list[StatusRow] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _LEDGER_ROW.match(line)
        if match is None or match.group(1).strip().lower() == "subsystem":
            continue
        try:
            verified_on = date.fromisoformat(match.group(2))
        except ValueError:
            continue
        rows.append(StatusRow(match.group(1).strip(), verified_on, line_number))
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
