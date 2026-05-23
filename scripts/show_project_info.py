#!/usr/bin/env python3
"""Display detailed project information — thin wrapper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.project.info import collect_project_info, display_project_info  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Display project information")
    parser.add_argument("--project", default="project", help="Project name")
    args = parser.parse_args()
    try:
        info = collect_project_info(args.project, repo_root)
        display_project_info(info, logger=logger)
        return 0
    except Exception as exc:
        logger.error("Failed to get project info: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
