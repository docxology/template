#!/usr/bin/env python3
"""Review, check, apply or roll back a coordinated metadata patch release.

Plan prints JSON to stdout without writing. Apply/rollback require its reviewed
canonical SHA256 and a retained private journal outside the checkout. No command
installs dependencies, commits, tags, publishes, or grants release acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.publishing.release_plan import build_release_plan, canonical, check_release_plan  # noqa: E402
from infrastructure.publishing.release_plan_transaction import apply_release_plan, rollback_release_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Print a deterministic dry-run plan")
    plan.add_argument("--from-version", required=True)
    plan.add_argument("--to-version", required=True)
    for name in ("check", "apply"):
        child = commands.add_parser(name)
        child.add_argument("--plan", type=Path, required=True)
        if name == "apply":
            child.add_argument("--reviewed-sha256", required=True)
            child.add_argument("--journal", type=Path, required=True)
    rollback = commands.add_parser("rollback")
    rollback.add_argument("--reviewed-sha256", required=True)
    rollback.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "plan":
        result = build_release_plan(args.repo_root, args.to_version, expected_current=args.from_version)
    elif args.command == "rollback":
        rollback_release_plan(args.repo_root, args.journal, reviewed_sha256=args.reviewed_sha256)
        result = {"status": "rolled-back", "role": "metadata-preparation-only"}
    else:
        reviewed = json.loads(args.plan.read_bytes())
        if args.command == "check":
            check_release_plan(args.repo_root, reviewed)
            result = {"status": "current", "role": "metadata-preparation-only"}
        else:
            result = apply_release_plan(
                args.repo_root, reviewed, reviewed_sha256=args.reviewed_sha256, journal=args.journal
            )
    sys.stdout.write(canonical(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
