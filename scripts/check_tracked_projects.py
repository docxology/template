#!/usr/bin/env python3
"""Fail when any project other than the two canonical templates is tracked.

CONFIDENTIALITY INVARIANT: this is a PUBLIC repository into which confidential
projects are routinely rotated under ``projects/``. Only the two canonical
template exemplars may ever be committed/pushed:

  * ``projects/template_code_project/``
  * ``projects/template_prose_project/``

Plus the repo-level documentation that lives directly in ``projects/``
(``projects/*.md`` — e.g. ``AGENTS.md``, ``README.md``, ``PAI.md``,
``PROJECTS_PARADIGM.md``). Anything else tracked under ``projects/`` is a
potential confidential-data leak (typically an accidental ``git add -f``)
and MUST block the push/CI until untracked with ``git rm -r --cached``.

This is defense-in-depth behind ``.gitignore`` (``projects/*`` ignored, with
repo-level Markdown docs and the two template directories negated): ignore
rules are bypassable with ``-f``; this guard is not.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404
import sys
from pathlib import Path

ALLOWED_PROJECT_DIRS: tuple[str, ...] = (
    "projects/template_code_project/",
    "projects/template_prose_project/",
)
# Repo-level docs that legitimately live directly under ``projects/``.
ALLOWED_PROJECTS_TOPLEVEL = re.compile(r"^projects/[^/]+\.md$")


def offending_tracked_projects(repo_root: Path) -> list[str]:
    """Return tracked ``projects/`` paths outside the allowed template set."""
    proc = subprocess.run(  # nosec B603 B607
        ["git", "ls-files", "-z", "projects/"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    offenders: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if ALLOWED_PROJECTS_TOPLEVEL.match(normalized):
            continue
        if any(normalized.startswith(prefix) for prefix in ALLOWED_PROJECT_DIRS):
            continue
        offenders.append(normalized)
    return sorted(offenders)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exit 0 when clean, 1 when a non-template project is tracked."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to inspect (defaults to this script's parent repo).",
    )
    args = parser.parse_args(argv)

    offenders = offending_tracked_projects(args.repo_root.resolve())
    if not offenders:
        print("Confidentiality guard: only the two canonical template projects are tracked.")
        return 0

    print(
        "CONFIDENTIALITY VIOLATION: non-template project paths are tracked by git.\n"
        "This is a PUBLIC repo — untrack them immediately with:\n"
        "  git rm -r --cached <path>\n"
        "Offending tracked paths:"
    )
    for path in offenders:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
