#!/usr/bin/env python3
"""Plan or explicitly execute two deterministic fresh-checkout rehearsals.

The default is a dry-run that prints the planned commands. No clone, network
access, dependency installation, or output mutation occurs unless ``--execute``
is supplied.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.publishing.rehearsal import (  # noqa: E402
    build_clean_checkout_plan,
    run_clean_checkout_rehearsal,
)
from infrastructure.publishing.release_receipts import write_receipt  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Print a dry-run plan or execute the explicitly requested rehearsal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--execute", action="store_true", help="Create two local clones and run the plan.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly select the default no-side-effect planning mode.",
    )
    parser.add_argument("--receipt", type=Path, help="Optional path for the JSON receipt.")
    args = parser.parse_args(argv)
    if args.execute and args.dry_run:
        parser.error("--execute and --dry-run are mutually exclusive")

    plan = build_clean_checkout_plan(REPO_ROOT, revision=args.revision)
    if not args.execute:
        payload = {"schema_version": "template-release-rehearsal-plan/v1", **plan.to_dict()}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    receipt = run_clean_checkout_rehearsal(REPO_ROOT, plan, platform_name=platform.system().lower())
    if args.receipt:
        write_receipt(args.receipt, receipt)
    print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
    return 0 if receipt.validate() == [] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
