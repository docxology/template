#!/usr/bin/env python3
"""Report every mainline commit whose receipts do not describe their own tree.

Every gate in this repository inspects *the current checkout*. None inspects
*the history*, so a commit that claimed verified receipts and was not could be
pushed, merged, and tagged without any check ever looking at it.

A commit is ``STALE`` when the digest stored in its committed receipt differs
from the digest its own tree produces. There is no expected-value table to keep
current, because the expected value is computed from the artifact.

The sampling, materialization, comparison and exit-code decision live in
:mod:`infrastructure.reporting.receipt_currency`. This script parses arguments
and prints.

Usage
-----
    python scripts/audit/receipt_currency.py                  # mainline since last tag
    python scripts/audit/receipt_currency.py --since v5.0.0
    python scripts/audit/receipt_currency.py --limit 40 --json
    python scripts/audit/receipt_currency.py --require-current   # exit 1 on any STALE

Exit codes: 0 clean (or report-only), 1 stale with ``--require-current``,
2 the environment could not answer (never reported as clean).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.reporting.receipt_currency import (  # noqa: E402
    DEFAULT_PROJECT,
    CommitRangeError,
    collect,
    last_tag,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", default=None, help="Revision to sample from (default: the newest v* tag).")
    parser.add_argument("--limit", type=int, default=40, help="Maximum number of first-parent commits.")
    parser.add_argument(
        "--ref",
        default="origin/main",
        help="Revision to sample (default: origin/main). Never HEAD by default: a canonical checkout "
        "may sit on a stale branch, which would silently sample the wrong history.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument(
        "--require-current",
        action="store_true",
        help="Exit non-zero when any sampled commit carries a stale receipt.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Sample the selected history and report every receipt that does not describe its tree."""
    args = _parse_args(argv)
    since = args.since or last_tag(REPO_ROOT)
    try:
        report = collect(REPO_ROOT, since=since, limit=args.limit, ref=args.ref, project=DEFAULT_PROJECT)
    except CommitRangeError as exc:
        raise SystemExit(str(exc)) from exc
    if not report.rows:
        raise SystemExit("no commits to sample; refusing to report a clean result")

    print(report.to_json() if args.json else report.format_table())
    warning = report.unavailable_warning()
    if warning is not None:
        print(warning, file=sys.stderr)
    return report.exit_code(require_current=args.require_current)


if __name__ == "__main__":
    raise SystemExit(main())
