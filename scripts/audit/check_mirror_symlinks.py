#!/usr/bin/env python3
"""Mirror-shape guard — thin CLI over infrastructure.project.linking.

The lifecycle directories under ``projects/`` are a generated mirror of the
private sidecar: every entry must be a managed symlink. ``link-projects`` only
prunes symlinks, so a real directory dropped into the mirror is invisible to it
— versioned by neither repo and one ``git add -f`` from publication. This guard
is what notices.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.linking import unmanaged_project_mirror_entries  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--private-root", type=Path, default=None)
    args = parser.parse_args(argv)

    offenders = unmanaged_project_mirror_entries(args.repo_root.resolve(), args.private_root)
    if not offenders:
        print("Mirror guard: every projects/<lifecycle>/ entry is a managed symlink.")
        return 0

    print(
        "MIRROR VIOLATION: unmanaged entries under projects/<lifecycle>/.\n"
        "This is a PUBLIC repo and these are not generated symlinks — move each\n"
        "one into the private sidecar and relink:\n"
        "  mv projects/<lifecycle>/<name> <private-root>/<lifecycle>/<name>\n"
        "  uv run python -m infrastructure.orchestration link-projects\n"
        "Offending entries:"
    )
    for offender in offenders:
        print(f"  {offender}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
