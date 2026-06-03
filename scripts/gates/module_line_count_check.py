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
)

# Documented, time-boxed exceptions to the module line-count gate. These are
# dense active-inference sheaf domain modules introduced by the sheaf-hardening
# work; they exceed the 950-line fail threshold but are cohesive function
# collections, not god-classes. Allowlisted to unblock the v3.1.0 release.
# TODO(sheaf): split these into sibling modules (e.g. extract the artifact-
# provenance / replay-matrix builders from sheaf_tracks.py and the
# *_restrictions helpers from semantic.py) and remove these entries.
LINE_COUNT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "projects/templates/template_active_inference/src/roadmap_tracks/sheaf_tracks.py",
        "projects/templates/template_active_inference/src/manuscript/sheaf/semantic.py",
    }
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
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

    for rel, count in sorted(warnings):
        print(f"WARN {rel}: {count} lines")
    for rel, count in sorted(failures):
        print(f"FAIL {rel}: {count} lines")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
