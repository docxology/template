#!/usr/bin/env python3
"""Offline source-ledger audit CLI."""

from __future__ import annotations

from pathlib import Path

from _bootstrap import ensure_project_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ensure_project_paths(PROJECT_ROOT)

from src.source_ledger import (  # noqa: E402
    load_source_ledger,
    source_age_summary,
    source_tier_counts,
    validate_source_ledger_contract,
)


def main() -> int:
    """Validate the manuscript source ledger and print tier counts."""
    entries = load_source_ledger(PROJECT_ROOT / "manuscript" / "source_ledger.yaml")
    print(f"source ledger entries: {len(entries)}")
    for tier, count in sorted(source_tier_counts(entries).items()):
        print(f"{tier}: {count}")
    for bucket, count in sorted(source_age_summary(entries).items()):
        print(f"checked_age_{bucket}: {count}")
    issues = validate_source_ledger_contract(PROJECT_ROOT)
    for issue in issues:
        print(f"source ledger issue: {issue}", file=__import__("sys").stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
