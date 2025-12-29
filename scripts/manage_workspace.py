#!/usr/bin/env python3
"""Workspace management script for uv multi-project support.

This script provides utilities for managing uv workspaces in the multi-project template:

- sync: Sync all workspace dependencies
- add <package> --project <name>: Add dependency to specific project
- update: Update all workspace dependencies
- tree: Show workspace dependency tree
- status: Show workspace status

Usage:
    uv run python scripts/manage_workspace.py sync
    uv run python scripts/manage_workspace.py add numpy --project project
    uv run python scripts/manage_workspace.py update
    uv run python scripts/manage_workspace.py tree
    uv run python scripts/manage_workspace.py status
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header

logger = get_logger(__name__)


def run_uv_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a uv command and return exit code."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            capture_output=False,
            check=False
        )
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run uv command: {e}")
        return 1


def sync_workspace() -> int:
    """Sync all workspace dependencies."""
    log_header("SYNCING WORKSPACE DEPENDENCIES", logger)
    logger.info("Running 'uv sync' for entire workspace...")

    exit_code = run_uv_command(['uv', 'sync'])
    if exit_code == 0:
        log_success("Workspace dependencies synced successfully", logger)
    else:
        logger.error("Failed to sync workspace dependencies")

    return exit_code


def add_dependency(package: str, project_name: str) -> int:
    """Add a dependency to a specific project."""
    log_header(f"ADDING DEPENDENCY TO PROJECT: {project_name}", logger)
    logger.info(f"Adding '{package}' to project '{project_name}'...")

    # Change to project directory
    project_dir = Path("projects") / project_name
    if not project_dir.exists():
        logger.error(f"Project directory not found: {project_dir}")
        return 1

    # Use uv add to add to the specific project's pyproject.toml
    exit_code = run_uv_command(['uv', 'add', package], cwd=project_dir)
    if exit_code == 0:
        log_success(f"Added '{package}' to project '{project_name}'", logger)
        logger.info("Run 'uv sync' to install the new dependency")
    else:
        logger.error(f"Failed to add '{package}' to project '{project_name}'")

    return exit_code


def update_workspace() -> int:
    """Update all workspace dependencies."""
    log_header("UPDATING WORKSPACE DEPENDENCIES", logger)
    logger.info("Running 'uv sync --upgrade' for entire workspace...")

    exit_code = run_uv_command(['uv', 'sync', '--upgrade'])
    if exit_code == 0:
        log_success("Workspace dependencies updated successfully", logger)
    else:
        logger.error("Failed to update workspace dependencies")

    return exit_code


def show_workspace_tree() -> int:
    """Show workspace dependency tree."""
    log_header("WORKSPACE DEPENDENCY TREE", logger)
    logger.info("Showing workspace dependency tree...")

    exit_code = run_uv_command(['uv', 'tree'])
    if exit_code != 0:
        logger.error("Failed to show workspace dependency tree")

    return exit_code


def show_workspace_status() -> int:
    """Show workspace status."""
    log_header("WORKSPACE STATUS", logger)

    # Check if we're in a workspace
    workspace_file = Path("pyproject.toml")
    if not workspace_file.exists():
        logger.error("No pyproject.toml found in current directory")
        return 1

    # Check workspace configuration
    try:
        import tomllib
        with open(workspace_file, 'rb') as f:
            config = tomllib.load(f)

        workspace_config = config.get('tool', {}).get('uv', {}).get('workspace', {})
        if workspace_config:
            members = workspace_config.get('members', [])
            exclude = workspace_config.get('exclude', [])

            logger.info(f"Workspace members: {len(members)}")
            for member in members:
                logger.info(f"  - {member}")

            if exclude:
                logger.info(f"Excluded patterns: {len(exclude)}")
                for pattern in exclude:
                    logger.info(f"  - {pattern}")

            # Check if lock file exists
            lock_file = Path("uv.lock")
            if lock_file.exists():
                logger.info("Lock file: present (uv.lock)")
            else:
                logger.warning("Lock file: missing (run 'uv sync' to create)")

            log_success("Workspace configuration is valid", logger)
            return 0
        else:
            logger.error("No workspace configuration found in pyproject.toml")
            return 1

    except Exception as e:
        logger.error(f"Failed to read workspace configuration: {e}")
        return 1


def main() -> int:
    """Main entry point for workspace management."""
    parser = argparse.ArgumentParser(
        description="Manage uv workspace for multi-project template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/manage_workspace.py sync
  uv run python scripts/manage_workspace.py add numpy --project project
  uv run python scripts/manage_workspace.py update
  uv run python scripts/manage_workspace.py tree
  uv run python scripts/manage_workspace.py status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # sync command
    subparsers.add_parser('sync', help='Sync all workspace dependencies')

    # add command
    add_parser = subparsers.add_parser('add', help='Add dependency to specific project')
    add_parser.add_argument('package', help='Package name to add')
    add_parser.add_argument('--project', required=True, help='Project name to add dependency to')

    # update command
    subparsers.add_parser('update', help='Update all workspace dependencies')

    # tree command
    subparsers.add_parser('tree', help='Show workspace dependency tree')

    # status command
    subparsers.add_parser('status', help='Show workspace status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute the requested command
    if args.command == 'sync':
        return sync_workspace()
    elif args.command == 'add':
        return add_dependency(args.package, args.project)
    elif args.command == 'update':
        return update_workspace()
    elif args.command == 'tree':
        return show_workspace_tree()
    elif args.command == 'status':
        return show_workspace_status()
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    exit(main())