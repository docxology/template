#!/usr/bin/env python3
"""Plan, execute, shard, or consolidate deterministic fresh-checkout rehearsals.

The default is a dry-run that prints the planned commands. No clone, network
access, dependency installation, or output mutation occurs unless ``--execute``
is supplied. ``--execute --shard-index N`` runs exactly one fresh-checkout run
for a matrix cell; ``--consolidate`` rebuilds the two-run determinism receipt
from the shard receipts.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
from infrastructure.publishing.rehearsal import (  # noqa: E402
    _rehearsal_exit_code,
    build_clean_checkout_plan,
    consolidate_rehearsal_shards,
    run_clean_checkout_rehearsal,
    run_clean_checkout_shard,
)
from infrastructure.publishing.release.release_receipts import (  # noqa: E402
    ReleaseReceiptError,
    rehearsal_shard_from_payload,
    write_receipt,
)


def main(argv: list[str] | None = None) -> int:
    """Print a dry-run plan, execute the rehearsal, run one shard, or consolidate shards."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--execute", action="store_true", help="Create two local clones and run the plan.")
    parser.add_argument(
        "--shard-index",
        type=int,
        metavar="N",
        help=(
            "With --execute: run exactly the Nth fresh-checkout run (1-based, of "
            "plan.runs) and emit a shard receipt instead of the consolidated "
            "two-run receipt. A separate --consolidate pass rebuilds the "
            "determinism judgment from the shard receipts."
        ),
    )
    parser.add_argument(
        "--consolidate",
        nargs="+",
        type=Path,
        metavar="SHARD_JSON",
        help="Rebuild the consolidated receipt from two or more shard receipts.",
    )
    parser.add_argument("--receipt", type=Path, help="Optional path for the JSON receipt.")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional directory for per-run diagnostic artifacts (matrix receipts, failed-command logs).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly select the default no-side-effect planning mode.",
    )
    args = parser.parse_args(argv)
    if args.execute and args.dry_run:
        parser.error("--execute and --dry-run are mutually exclusive")
    if args.consolidate and (args.execute or args.shard_index is not None):
        parser.error("--consolidate cannot be combined with --execute/--shard-index")
    if args.shard_index is not None and not args.execute:
        parser.error("--shard-index requires --execute")

    plan = build_clean_checkout_plan(REPO_ROOT, revision=args.revision)

    if args.consolidate:
        if args.receipt is None:
            parser.error("--consolidate requires --receipt for the consolidated receipt")
        try:
            shards = [
                rehearsal_shard_from_payload(json.loads(path.read_text(encoding="utf-8"))) for path in args.consolidate
            ]
        except (OSError, json.JSONDecodeError, ReleaseReceiptError) as exc:
            print(f"ERROR: failed to load rehearsal shard receipt: {exc}", file=sys.stderr)
            return 1
        receipt = consolidate_rehearsal_shards(shards, platform_name=platform.system().lower())
        write_receipt(args.receipt, receipt)
        print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
        return _rehearsal_exit_code(receipt)

    if args.shard_index is not None:
        if args.receipt is None:
            parser.error("--shard-index requires --receipt for the shard receipt")
        shard = run_clean_checkout_shard(
            REPO_ROOT,
            plan,
            run_index=args.shard_index,
            platform_name=platform.system().lower(),
            artifact_dir=args.artifact_dir,
        )
        write_receipt(args.receipt, shard)
        print(json.dumps(shard.to_dict(), indent=2, sort_keys=True))
        return _rehearsal_exit_code(shard)

    if not args.execute:
        payload = {"schema_version": "template-release-rehearsal-plan/v1", **plan.to_dict()}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    receipt = run_clean_checkout_rehearsal(
        REPO_ROOT, plan, platform_name=platform.system().lower(), artifact_dir=args.artifact_dir
    )
    if args.receipt:
        write_receipt(args.receipt, receipt)
    print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
    return _rehearsal_exit_code(receipt)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
