#!/usr/bin/env python3
"""Validate the committed measured CI module-duration manifest.

Every key must name a real module of the current functional roster and every
value must be a finite positive number of seconds; a stale or invented entry
would silently mis-weight functional shards.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.testing.ci_contracts import CONTRACT_MODULES  # noqa: E402
from infrastructure.core.testing.ci_infra import infrastructure_files  # noqa: E402
from infrastructure.core.testing.ci_module_durations import (  # noqa: E402
    MANIFEST_RELATIVE_PATH,
    load_module_durations,
    validate_module_durations,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        durations = load_module_durations(args.repo_root)
        # The functional roster is the routine selection plus the declared deep
        # contract modules; a measurement must name one of those real modules.
        roster = frozenset(infrastructure_files(args.repo_root)) | CONTRACT_MODULES
        validate_module_durations(durations, roster)
    except (OSError, ValueError) as error:
        print(f"FAIL module duration manifest: {error}", file=sys.stderr)
        return 1
    print(
        f"Measured module durations: {len(durations)} of {len(roster)} roster modules "
        f"({MANIFEST_RELATIVE_PATH.as_posix()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
