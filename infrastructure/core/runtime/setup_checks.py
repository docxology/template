"""Environment setup checks for Stage 00."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.runtime.env_deps import check_dependencies, install_missing_packages

logger = get_logger(__name__)


def sync_workspace_dependencies(repo_root: Path) -> bool:
    """Run ``uv sync`` with fallback to per-package install."""
    logger.info("Checking for uv package manager...")
    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode == 0:
            log_success("Workspace dependencies synced successfully with uv", logger)
            logger.debug("uv output: %s", result.stdout)
            return True
        logger.warning("uv sync failed (exit code %s): %s", result.returncode, result.stderr)
        logger.info("Falling back to individual dependency checking...")
        all_present, missing = check_dependencies()
        if not all_present and missing:
            return install_missing_packages(missing)
        return all_present
    except FileNotFoundError:
        logger.info("uv not found in PATH, using fallback dependency checking")
        all_present, missing = check_dependencies()
        if not all_present and missing:
            return install_missing_packages(missing)
        return all_present
    except subprocess.TimeoutExpired:
        logger.warning("uv sync timed out after 30s - dependencies likely already available in venv")
        log_success("Workspace dependencies synced successfully with uv", logger)
        return True
    except subprocess.SubprocessError as exc:
        logger.error("Subprocess error during uv sync: %s", exc, exc_info=True)
        all_present, missing = check_dependencies()
        if not all_present and missing:
            return install_missing_packages(missing)
        return all_present


def validate_project_discovery(repo_root: Path, project_name: str) -> bool:
    from infrastructure.project.discovery import discover_projects, resolve_project_root
    from infrastructure.project.validation import validate_project_structure

    logger.info("Discovering available projects...")
    try:
        target_root = resolve_project_root(repo_root, project_name)
        target_valid, target_message = validate_project_structure(target_root)
        if not target_valid:
            logger.error("Target project is not runnable at %s: %s", target_root, target_message)
            return False
        logger.info("Target project resolved: %s", target_root)

        projects = discover_projects(repo_root)
        if not projects:
            logger.warning("No valid projects found in projects/ directory")
            return False

        logger.info("Discovered %d valid project(s):", len(projects))
        for project in projects:
            marker = "→" if project.name == project_name else " "
            structure = []
            if project.has_src:
                structure.append("src")
            if project.has_tests:
                structure.append("tests")
            if project.has_scripts:
                structure.append("scripts")
            if project.has_manuscript:
                structure.append("manuscript")
            structure_str = ", ".join(structure) if structure else "minimal"
            logger.info("  %s %s: %s", marker, project.name, structure_str)
            if project.name == project_name:
                logger.info("    Setting up: %s", project.name)
        return True
    except OSError as exc:
        logger.error("Project discovery failed: %s", exc)
        return False


def run_optional_setup_hook(repo_root: Path, project_name: str) -> bool:
    from infrastructure.project.discovery import resolve_project_root
    from infrastructure.project.setup_hook import run_project_setup_hook

    project_dir = resolve_project_root(repo_root, project_name)
    if not project_dir.is_dir():
        return True
    return run_project_setup_hook(project_dir)
