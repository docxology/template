#!/usr/bin/env python3
"""Generate (or check) ``docs/_generated/COUNTS.md``.

Thin orchestrator: all logic lives in ``infrastructure.documentation.counts_doc``.

``COUNTS.md`` (formerly the hand-maintained ``COUNTS.md``) is the
canonical factsheet pinning volatile repo literals — the tracked
``infrastructure/`` Python-file count, the project-scope/publishing test
collection totals, the public exemplar roster, and the importable module list.
This generator re-derives those from the live tree so ``--check`` fails the
moment the committed doc drifts.

Usage::

    uv run python scripts/docgen/counts.py --write   # apply
    uv run python scripts/docgen/counts.py --check    # CI, no write
    uv run python scripts/docgen/counts.py --verify-coverage --write \
        --coverage-snapshot-output /owned/retained/counts_coverage.snapshot.data

Exit codes:
    0: write succeeded (``--write``) or doc in sync (``--check``).
    1: drift detected or a coverage measurement failed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.documentation.counts_doc import (  # noqa: E402
    check_counts_doc,
    write_coverage_provenance,
    verify_exemplar_coverage_result,
    write_counts_doc,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="render and write the doc")
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify the doc is in sync with the live tree without writing",
    )
    parser.add_argument(
        "--refresh-coverage-provenance",
        action="store_true",
        help="record source hashes after rerunning every changed coverage gate",
    )
    parser.add_argument(
        "--verify-coverage",
        action="store_true",
        help=(
            "re-measure every exemplar's standalone release-profile coverage and "
            "compare against the recorded percentage (slow — runs every release "
            "profile suite); combine with --write and --coverage-snapshot-output "
            "to write a retained DATA copy only after every measurement succeeds"
        ),
    )
    parser.add_argument(
        "--coverage-snapshot-output",
        type=Path,
        help="existing independent exact copy of selected counts_coverage.py outside the repo and SDK",
    )
    parser.add_argument(
        "--project-workers",
        default="auto",
        help="bounded public-exemplar collection concurrency (default: auto); use 'serial' or a positive integer",
    )
    args = parser.parse_args(argv)

    if args.coverage_snapshot_output is not None and not (args.verify_coverage and args.write):
        parser.error("--coverage-snapshot-output requires --verify-coverage --write")
    if args.verify_coverage and args.write and args.coverage_snapshot_output is None:
        parser.error("--verify-coverage --write requires --coverage-snapshot-output with a retained DATA copy")

    if args.verify_coverage:
        try:
            result = verify_exemplar_coverage_result(
                REPO_ROOT, rewrite=args.write, snapshot_output=args.coverage_snapshot_output
            )
        except (ValueError, OSError, UnicodeError) as exc:
            parser.error(str(exc))
        print(result.report)
        if not result.measurement_complete:
            print("\ncoverage snapshot not refreshed — resolve every measurement failure and rerun")
            return 1
        if args.write and result.drifted_count:
            # The retained DATA copy holds measured literals; executable Source
            # remains unchanged until the owner reviews a new Source epoch.
            print("\nDATA prepared — review/apply after terminal closure, then rebuild and refresh provenance")
            return 0
        return 0 if result.all_match else 1

    if args.check:
        in_sync, message = check_counts_doc(REPO_ROOT, project_workers=args.project_workers)
        print(message)
        return 0 if in_sync else 1

    if args.refresh_coverage_provenance:
        provenance = write_coverage_provenance(REPO_ROOT)
        print(str(provenance.relative_to(REPO_ROOT)))
    written = write_counts_doc(REPO_ROOT, project_workers=args.project_workers)
    print(str(written.relative_to(REPO_ROOT)) if written.is_relative_to(REPO_ROOT) else str(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
