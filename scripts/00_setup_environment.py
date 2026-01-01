#!/usr/bin/env python3
"""Environment setup orchestrator script.

This thin orchestrator prepares the environment for the complete project pipeline:
1. Verifies Python version and dependencies
2. Sets up directory structure
3. Configures environment variables
4. Validates build tools availability

Stage 1 of the pipeline orchestration.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.core.environment import (
    check_python_version,
    check_dependencies,
    install_missing_packages,
    check_build_tools,
    setup_directories,
    verify_source_structure,
    set_environment_variables,
)
from infrastructure.core.file_operations import clean_coverage_files

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute environment setup orchestration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup environment")
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
    )
    args = parser.parse_args()
    
    log_header(f"STAGE 00: Environment Setup (Project: {args.project})", logger)
    
    repo_root = Path(__file__).parent.parent

    # Clean coverage files to ensure clean state for subsequent test runs
    clean_coverage_files(repo_root)

    def check_and_install_dependencies() -> bool:
        """Check dependencies and install missing ones using workspace sync."""
        logger.info("Checking for uv package manager...")

        try:
            result = subprocess.run(['uv', 'sync'], cwd=str(repo_root),
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                log_success("Workspace dependencies synced successfully with uv", logger)
                logger.debug(f"uv output: {result.stdout}")
                return True
            else:
                logger.warning(f"uv sync failed (exit code {result.returncode}): {result.stderr}")
                logger.info("Falling back to individual dependency checking...")
                # Fall back to checking individual dependencies
                all_present, missing = check_dependencies()
                if not all_present and missing:
                    return install_missing_packages(missing)
                return all_present
        except FileNotFoundError:
            logger.info("uv not found in PATH, using fallback dependency checking")
            logger.info("Install uv with: pip install uv (recommended for faster dependency management)")
            # Fall back to checking individual dependencies
            all_present, missing = check_dependencies()
            if not all_present and missing:
                return install_missing_packages(missing)
            return all_present
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error during uv sync: {e}", exc_info=True)
            logger.info("Falling back to individual dependency checking...")
            # Fall back to checking individual dependencies
            all_present, missing = check_dependencies()
            if not all_present and missing:
                return install_missing_packages(missing)
            return all_present

    def check_project_discovery() -> bool:
        """Discover and validate available projects."""
        from infrastructure.project.discovery import discover_projects

        logger.info("Discovering available projects...")
        try:
            projects = discover_projects(repo_root)

            if not projects:
                logger.warning("No valid projects found in projects/ directory")
                return False

            logger.info(f"Discovered {len(projects)} valid project(s):")
            for project in projects:
                marker = "→" if project.name == args.project else " "
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
                logger.info(f"  {marker} {project.name}: {structure_str}")

                if project.name == args.project:
                    logger.info(f"    Setting up: {project.name}")

            return True
        except Exception as e:
            logger.error(f"Project discovery failed: {e}")
            return False
    
    checks = [
        ("Python version", lambda: check_python_version()),
        ("Dependencies", check_and_install_dependencies),
        ("Build tools", lambda: check_build_tools()),
        ("Directory structure", lambda: setup_directories(repo_root, args.project)),
        ("Source structure", lambda: verify_source_structure(repo_root, args.project)),
        ("Project discovery", check_project_discovery),
        ("Environment variables", lambda: set_environment_variables(repo_root)),
    ]
    
    results = []
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    log_header("Setup Summary")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        log_success("\n✅ Environment setup complete - ready to proceed")
        return 0
    else:
        logger.error("\n❌ Environment setup failed - fix issues and try again")
        return 1


if __name__ == "__main__":
    exit(main())

