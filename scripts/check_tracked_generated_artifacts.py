#!/usr/bin/env python3
"""Fail when disposable generated artifacts are tracked by git.

The template keeps outputs, coverage files, OS metadata, and packaging metadata
regeneratable. They may exist locally, but they should not live in the git index.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    ".coverage",
    ".coverage.*",
    ".DS_Store",
    "*/.DS_Store",
    "*.egg-info/*",
    "*/.egg-info/*",
    "coverage.json",
    "coverage*.xml",
    "coverage_project.json",
    "htmlcov/*",
    "output/*",
    "projects/*/output/*",
    "projects/*/*/output/*",
)


def is_generated_artifact_path(path: str) -> bool:
    """Return True when *path* is a disposable artifact that should be untracked."""
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in GENERATED_ARTIFACT_PATTERNS)


def tracked_generated_artifacts(repo_root: Path) -> list[str]:
    """Return tracked generated-artifact paths under *repo_root*."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    return sorted(path for path in paths if is_generated_artifact_path(path))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to inspect (defaults to this script's parent repo).",
    )
    args = parser.parse_args(argv)

    offenders = tracked_generated_artifacts(args.repo_root.resolve())
    if not offenders:
        print("No tracked generated artifacts found.")
        return 0

    print("Tracked generated artifacts found; untrack them with `git rm --cached`:")
    for path in offenders:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
