#!/usr/bin/env python3
"""Validate structural and skip contracts for every canonical public exemplar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.public_capabilities import audit_public_capabilities  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the public capability contract gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = audit_public_capabilities(args.repo_root)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        for project in report.projects:
            status = "OK" if project.passed else "FAIL"
            print(
                f"{status} {project.project}: src={project.source_file_count} "
                f"tests={project.test_file_count} scripts={project.script_file_count} "
                f"skips={len(project.skip_contracts)}"
            )
            for issue in project.missing_paths:
                print(f"  missing: {issue}")
            for issue in project.issues:
                print(f"  issue: {issue}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
