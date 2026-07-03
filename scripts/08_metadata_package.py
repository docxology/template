#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.publishing.metadata_stage import run_metadata_package  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate metadata package (ONIX, JSON, OPF)")
    parser.add_argument(
        "--project",
        default="project",
        help="Project directory name or qualified path (e.g. templates/template_code_project); "
        "resolves projects/active/<name> first, else projects/working/<name>",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    return run_metadata_package(repo_root, args.project)


if __name__ == "__main__":
    sys.exit(main())
