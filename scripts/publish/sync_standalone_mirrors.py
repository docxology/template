#!/usr/bin/env python3
"""Sync public exemplars into their standalone publication repositories.

Thin orchestrator: all behaviour lives in
:mod:`infrastructure.publishing.standalone_mirror`, which documents the two
properties that matter (update-only, and symlink dereferencing) and why.

Dry-run by default — reviewing the per-repository delta before touching a public
repository is the point.

USAGE (from the repo root)::

    uv run python scripts/publish/sync_standalone_mirrors.py
    uv run python scripts/publish/sync_standalone_mirrors.py --project template_formal
    uv run python scripts/publish/sync_standalone_mirrors.py --commit
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.public_scope import public_project_names  # noqa: E402
from infrastructure.publishing.standalone_mirror import sync_exemplar  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Report or apply standalone-mirror syncs for the public exemplars."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit", action="store_true", help="perform real commits and pushes")
    parser.add_argument("--project", help="limit to a single exemplar name")
    args = parser.parse_args(argv)

    dirty = subprocess.run(  # noqa: S603 - fixed argv
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    if dirty:
        print("REFUSING: monorepo working tree is dirty — commit first so the mirror is reproducible.")
        return 1
    revision = subprocess.run(  # noqa: S603 - fixed argv
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()

    qualified = [name for name in public_project_names(REPO_ROOT) if name.startswith("templates/")]
    names = [args.project] if args.project else [name.split("/", 1)[1] for name in qualified]

    print(f"source: {revision} | exemplars: {len(names)} | mode: {'COMMIT' if args.commit else 'DRY-RUN'}\n")
    results = []
    for name in names:
        result = sync_exemplar(REPO_ROOT, name, commit=args.commit, source_revision=revision)
        results.append(result)
        delta = f" (+{result.added} ~{result.modified} -{result.deleted})" if result.changed else ""
        print(f"  {name:42} {result.status}{delta}")
        sys.stdout.flush()

    print()
    for status in ("SYNCED", "WOULD SYNC", "up to date"):
        count = sum(1 for result in results if result.status == status)
        if count:
            print(f"  {status}: {count}")
    problems = [r for r in results if r.status.startswith(("SKIP", "PUSH FAILED"))]
    for result in problems:
        print(f"  PROBLEM {result.exemplar}: {result.status}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
