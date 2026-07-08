#!/usr/bin/env python3
"""Generate deep-review report for template_search_project (runs last in the project-analysis stage).

All inventory scanning, documentation/bibliography/infrastructure audits,
review-summary subprocess invocation, and markdown assembly live in
``src.review_report`` — this script only resolves project paths and calls
into it, per the thin-orchestrator pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_repo_root = _project_root.parents[2]
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_repo_root))

from src.review_report import generate_review_report, project_paths  # noqa: E402


def main() -> int:
    """CLI entry point."""
    project_root, template_root, review_dir = project_paths()
    return generate_review_report(project_root, template_root, review_dir)


if __name__ == "__main__":
    sys.exit(main())
