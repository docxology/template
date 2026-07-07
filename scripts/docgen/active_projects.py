#!/usr/bin/env python3
"""Write docs/_generated/active_projects.md for the public template scope."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.documentation.active_projects_doc import write_active_projects_doc  # noqa: E402
from infrastructure.project.public_scope import public_project_names  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Regenerate the public active-projects document."""
    log_header("Generate Active Projects Documentation", logger)
    out_path = write_active_projects_doc(REPO_ROOT)
    log_success(f"Wrote {out_path} ({len(public_project_names(REPO_ROOT))} project(s))", logger)


if __name__ == "__main__":
    main()
