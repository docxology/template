#!/usr/bin/env python3
"""Advisory module line-count gate for Layer 1 and project script sources."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.line_count import (  # noqa: E402
    LineCountRatchet,
    scan_infrastructure_and_scripts,
    scan_project_scripts,
    scan_project_src,
    scan_repository_tests,
)

# Temporary grandfathers for the 2026-07 exemplar merge — each entry is open
# refactoring debt, not an accepted end state (precedent: the sheaf_tracks
# allowlist, removed once that split landed). Remove the entry when the module
# is decomposed:
# - template_pools_rules_tools figures.py (1028): split per-figure builders out.
# - template_redacted_report visuals.py (1469): split redaction profiles /
#   PDF proof / steganography adapter into submodules.
LINE_COUNT_ALLOWLIST: dict[str, LineCountRatchet] = {
    "projects/templates/template_pools_rules_tools/src/figures.py": LineCountRatchet(
        max_lines=1028,
        expires_on=date(2026, 10, 1),
    ),
    "projects/templates/template_redacted_report/src/redacted_report/visuals.py": LineCountRatchet(
        max_lines=1469,
        expires_on=date(2026, 10, 1),
    ),
}


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
