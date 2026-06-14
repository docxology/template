#!/usr/bin/env python3
"""Advisory module line-count gate for Layer 1 and project script sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.line_count import (  # noqa: E402
    scan_infrastructure_and_scripts,
    scan_project_scripts,
    scan_project_src,
    scan_repository_tests,
)

# Split complete — allowlist removed after sheaf_tracks/semantic decomposition.
LINE_COUNT_ALLOWLIST: frozenset[str] = frozenset()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Emit advisory WARN lines for test modules >=800 lines (never fails the gate)",
    )
    args = parser.parse_args(argv)

    warnings: list[tuple[str, int]] = []
    failures: list[tuple[str, int]] = []

    infra_warn, infra_fail = scan_infrastructure_and_scripts(args.repo_root, allowlist=LINE_COUNT_ALLOWLIST)
    warnings.extend(infra_warn)
    failures.extend(infra_fail)

    proj_warn, proj_fail = scan_project_scripts(args.repo_root, allowlist=LINE_COUNT_ALLOWLIST)
    warnings.extend(proj_warn)
    failures.extend(proj_fail)

    src_warn, src_fail = scan_project_src(args.repo_root, allowlist=LINE_COUNT_ALLOWLIST)
    warnings.extend(src_warn)
    failures.extend(src_fail)

    if args.include_tests:
        test_warn, _ = scan_repository_tests(args.repo_root, allowlist=LINE_COUNT_ALLOWLIST)
        for rel, count in sorted(test_warn):
            print(f"WARN [test] {rel}: {count} lines")

    for rel, count in sorted(warnings):
        print(f"WARN {rel}: {count} lines")
    for rel, count in sorted(failures):
        print(f"FAIL {rel}: {count} lines")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
