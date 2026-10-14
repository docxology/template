#!/usr/bin/env python3
"""Generate deep-review report for template_search_project (second-to-last in the project-analysis stage).

All inventory scanning, documentation/bibliography/infrastructure audits,
review-summary subprocess invocation, and markdown assembly live in
``template_search_project.analysis.review_report`` — this script only resolves
project paths and calls into it, per the thin-orchestrator pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
# Select the declared SDK before exposing domain source; no ancestor imports.
_original_import_paths = sys.path[:]
try:
    sys.path.insert(0, str(_project_root / "scripts"))
    from _search_sdk_bootstrap import select_platform_sdk

    select_platform_sdk(_project_root)
finally:
    sys.path[:] = _original_import_paths
sys.path.insert(0, str(_project_root / "src"))

from template_search_project.analysis.review_report import generate_review_report, project_paths  # noqa: E402


def main() -> int:
    """CLI entry point."""
    project_root, review_dir = project_paths(_project_root)
    return generate_review_report(project_root, review_dir)


if __name__ == "__main__":
    sys.exit(main())
