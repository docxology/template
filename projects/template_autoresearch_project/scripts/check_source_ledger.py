#!/usr/bin/env python3
"""Offline source-ledger audit CLI."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[1]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.source_ledger import load_source_ledger, source_tier_counts  # noqa: E402


def main() -> int:
    """Validate the manuscript source ledger and print tier counts."""
    entries = load_source_ledger(PROJECT_ROOT / "manuscript" / "source_ledger.yaml")
    print(f"source ledger entries: {len(entries)}")
    for tier, count in sorted(source_tier_counts(entries).items()):
        print(f"{tier}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
