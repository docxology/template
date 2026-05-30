"""uv workspace management helpers."""

from __future__ import annotations

import subprocess

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_header, log_success

logger = get_logger(__name__)


def run_uv_command(cmd: list[str], cwd: Path | None = None) -> int:
    try:
        result = subprocess.run(cmd, cwd=cwd or Path.cwd(), capture_output=False, check=False, timeout=120)
        return result.returncode
    except OSError as exc:
        logger.error("Failed to run uv command: %s", exc)
        return 1


def sync_workspace() -> int:
    log_header("SYNCING WORKSPACE DEPENDENCIES", logger)
    logger.info("Running 'uv sync' for entire workspace...")
    exit_code = run_uv_command(["uv", "sync"])
    if exit_code == 0:
        log_success("Workspace dependencies synced successfully", logger)
    else:
        logger.error("Failed to sync workspace dependencies")
    return exit_code


def add_dependency(package: str, project_name: str) -> int:
    log_header(f"ADDING DEPENDENCY TO PROJECT: {project_name}", logger)
    project_dir = Path("projects") / project_name
    if not project_dir.exists():
        logger.error("Project directory not found: %s", project_dir)
        return 1
    exit_code = run_uv_command(["uv", "add", package], cwd=project_dir)
    if exit_code == 0:
        log_success(f"Added '{package}' to project '{project_name}'", logger)
        logger.info("Run 'uv sync' to install the new dependency")
    else:
        logger.error("Failed to add '%s' to project '%s'", package, project_name)
    return exit_code


def update_workspace() -> int:
    log_header("UPDATING WORKSPACE DEPENDENCIES", logger)
    exit_code = run_uv_command(["uv", "sync", "--upgrade"])
    if exit_code == 0:
        log_success("Workspace dependencies updated successfully", logger)
    else:
        logger.error("Failed to update workspace dependencies")
    return exit_code


def show_workspace_tree() -> int:
    log_header("WORKSPACE DEPENDENCY TREE", logger)
    exit_code = run_uv_command(["uv", "tree"])
    if exit_code != 0:
        logger.error("Failed to show workspace dependency tree")
    return exit_code


def show_workspace_status() -> int:
    log_header("WORKSPACE STATUS", logger)
    workspace_file = Path("pyproject.toml")
    if not workspace_file.exists():
        logger.error("No pyproject.toml found in current directory")
        return 1
    try:
        with workspace_file.open("rb") as handle:
            config = tomllib.load(handle)
        workspace_config = config.get("tool", {}).get("uv", {}).get("workspace", {})
        if not workspace_config:
            logger.error("No workspace configuration found in pyproject.toml")
            return 1
        for member in workspace_config.get("members", []):
            logger.info("  - %s", member)
        if Path("uv.lock").exists():
            logger.info("Lock file: present (uv.lock)")
        else:
            logger.warning("Lock file: missing (run 'uv sync' to create)")
        log_success("Workspace configuration is valid", logger)
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        logger.error("Failed to read workspace configuration: %s", exc)
        return 1
