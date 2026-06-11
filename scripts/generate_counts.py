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

    uv run python scripts/generate_counts.py --write   # apply
    uv run python scripts/generate_counts.py --check    # CI, no write

Exit codes:
    0: write succeeded (``--write``) or doc in sync (``--check``).
    1: drift detected (``--check``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.documentation.counts_doc import (  # noqa: E402
    check_counts_doc,
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
    args = parser.parse_args(argv)

    if args.check:
        in_sync, message = check_counts_doc(REPO_ROOT)
        print(message)
        return 0 if in_sync else 1

    written = write_counts_doc(REPO_ROOT)
    print(str(written.relative_to(REPO_ROOT)) if written.is_relative_to(REPO_ROOT) else str(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
