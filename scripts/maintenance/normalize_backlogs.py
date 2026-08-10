#!/usr/bin/env python3
"""Normalize canonical exemplar TODO files into future-only grouped backlogs."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.documentation.backlog_normalizer import normalize_public_backlogs

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    """Run the repository-scoped backlog normalizer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write normalized TODOs and archive removed sections")
    parser.add_argument(
        "--close-id",
        action="append",
        default=[],
        metavar="ID",
        help="remove a verified completed row and archive it; repeat for multiple IDs",
    )
    parser.add_argument(
        "--closure-evidence",
        help="receipt path or same-revision result summary recorded with closed rows",
    )
    args = parser.parse_args()
    close_ids = frozenset(args.close_id)
    if close_ids and not args.write:
        parser.error("--close-id requires --write so completed evidence is archived")
    changed, archived = normalize_public_backlogs(
        REPO_ROOT,
        write=args.write,
        close_ids=close_ids,
        closure_evidence=args.closure_evidence,
    )
    print(f"canonical exemplar backlogs changed: {changed}")
    print(f"archived sections: {archived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
