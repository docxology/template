#!/usr/bin/env python3
"""Refresh rendered provenance receipts for already-green project outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES  # noqa: E402
from infrastructure.validation.publication.rendered_refresh import run  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--project",
        action="append",
        dest="projects",
        metavar="QUALIFIED_NAME",
        help="Project to refresh; repeat for multiple projects.",
    )
    selection.add_argument("--all-public", action="store_true", help="Refresh every canonical public exemplar.")
    parser.add_argument(
        "--repo-root", type=Path, default=repo_root, help="Repository root (default: parent of scripts/)."
    )
    parser.add_argument(
        "--rebind",
        action="store_true",
        help="Revalidate unchanged rendered bytes and rewrite their receipts without "
        "re-rendering. Refused for any project whose tracked output tree is dirty.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Projects refreshed concurrently (default: 1; each worker owns its project tree).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    names = list(PUBLIC_PROJECT_NAMES if args.all_public else args.projects)
    results = run(args.repo_root.resolve(), names, jobs=args.jobs, rebind=args.rebind)
    failed = False
    for name, passed, message in sorted(results):
        if passed:
            print(f"PASS {name}: {message}")
        else:
            failed = True
            print(f"FAIL {name}: {message}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
