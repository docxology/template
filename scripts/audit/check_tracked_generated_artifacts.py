#!/usr/bin/env python3
"""Generated-artifact guard — thin CLI over infrastructure.project.git_guards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import tracked_generated_artifacts  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    offenders = tracked_generated_artifacts(args.repo_root.resolve())
    if not offenders:
        print("No prohibited tracked generated artifacts found; canonical public exemplar outputs are allowed.")
        return 0

    print(
        "Tracked generated/local artifacts or oversized public template outputs found; "
        "untrack them with `git rm --cached`:"
    )
    for path in offenders:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
