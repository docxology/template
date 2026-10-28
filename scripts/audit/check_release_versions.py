#!/usr/bin/env python3
"""Check root and exemplar version identity across every release surface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.project.release_versions import (  # noqa: E402
    format_release_version_report,
    validate_release_versions,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--tag",
        help="Optional root Git tag to validate against the declared version (e.g. $GITHUB_REF_NAME).",
    )
    args = parser.parse_args(argv)
    report = validate_release_versions(args.repo_root, tag=args.tag)
    print(format_release_version_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
