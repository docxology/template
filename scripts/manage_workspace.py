#!/usr/bin/env python3
"""Workspace management script for uv multi-project support."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.workspace import (
    add_dependency,
    show_workspace_status,
    show_workspace_tree,
    sync_workspace,
    update_workspace,
)

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage uv workspace for multi-project template")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("sync", help="Sync all workspace dependencies")
    add_parser = subparsers.add_parser("add", help="Add dependency to specific project")
    add_parser.add_argument("package", help="Package name to add")
    add_parser.add_argument("--project", required=True, help="Project name to add dependency to")
    subparsers.add_parser("update", help="Update all workspace dependencies")
    subparsers.add_parser("tree", help="Show workspace dependency tree")
    subparsers.add_parser("status", help="Show workspace status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    if args.command == "sync":
        return sync_workspace()
    if args.command == "add":
        return add_dependency(args.package, args.project)
    if args.command == "update":
        return update_workspace()
    if args.command == "tree":
        return show_workspace_tree()
    if args.command == "status":
        return show_workspace_status()
    logger.error("Unknown command: %s", args.command)
    return 1


if __name__ == "__main__":
    sys.exit(main())
