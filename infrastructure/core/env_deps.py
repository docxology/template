"""Dependency and build tool checking utilities.

Functions for verifying Python packages, build tools, and installing
missing dependencies. Split from environment.py to keep each module
under 300 LOC.
"""

from __future__ import annotations

import shutil
import subprocess

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def check_dependencies(
    required_packages: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """Verify required packages are installed.

    Args:
        required_packages: List of package names to check. If None, uses default list.

    Returns:
        Tuple of (all_present, missing_packages)
    """
    if required_packages is None:
        # Core required packages (must be present)
        required_packages = [
            "numpy",
            "matplotlib",
            "pytest",
        ]
        # No optional packages in default infrastructure check
        # (project-specific deps like scipy belong in projects/{name}/pyproject.toml)
        optional_packages: list[str] = []
    else:
        optional_packages = []

    missing_packages = []
    optional_missing = []

    for package in required_packages:
        try:
            __import__(package)
            logger.debug(f"Package '{package}' available")
        except ImportError:
            logger.error(f"Package '{package}' not found")
            missing_packages.append(package)

    # Check optional packages - warn but don't fail
    for package in optional_packages:
        try:
            __import__(package)
            logger.debug(f"Package '{package}' available")
        except ImportError:
            logger.warning(f"Package '{package}' not found (optional)")
            optional_missing.append(package)

    found_count = len(required_packages) - len(missing_packages)
    if not missing_packages:
        log_success(f"All {found_count} required packages found", logger)
    if optional_missing:
        logger.info(f"Optional packages missing: {', '.join(optional_missing)}")
        logger.info("These are not critical but recommended for full functionality")

    return len(missing_packages) == 0, missing_packages


def install_missing_packages(packages: list[str]) -> bool:
    """Install packages via uv add + uv sync; returns True on success."""
    logger.info(f"Installing {len(packages)} missing package(s) with uv...")

    # Check if uv is available
    if not shutil.which("uv"):
        logger.error("uv package manager not found - cannot auto-install dependencies")
        logger.error("Install uv with: pip install uv")
        logger.error("Or install packages manually: pip install " + " ".join(packages))
        return False

    try:
        # Use uv add to properly manage dependencies through pyproject.toml
        # First add to pyproject.toml, then sync
        for package in packages:
            add_cmd = ["uv", "add", package]
            logger.info(f"Adding to pyproject.toml: {' '.join(add_cmd)}")
            try:
                add_result = subprocess.run(
                    add_cmd, check=False, capture_output=True, text=True, timeout=30
                )
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout adding {package} to pyproject.toml (30s)")
                continue
            if add_result.returncode != 0:
                logger.warning(f"Failed to add {package} to pyproject.toml: {add_result.stderr}")

        # Then sync to install all dependencies
        cmd = ["uv", "sync"]
        logger.info(f"Syncing dependencies: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=False, timeout=120)
        except subprocess.TimeoutExpired:
            logger.error("uv sync timed out after 120s")
            return False

        if result.returncode == 0:
            # Verify installation
            logger.info("Verifying installation...")
            all_installed = True
            for package in packages:
                try:
                    __import__(package)
                    logger.debug(f"Package '{package}' installed successfully")
                except ImportError:
                    logger.error(f"Package '{package}' installation failed")
                    all_installed = False

            if all_installed:
                log_success(f"All {len(packages)} packages installed successfully", logger)
            return all_installed
        else:
            logger.error(f"uv installation failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        logger.error(f"Failed to install packages: {e}", exc_info=True)
        return False


def check_build_tools(required_tools: dict[str, str] | None = None) -> bool:
    """Verify build tools are available.

    Args:
        required_tools: Dictionary mapping tool names to descriptions.
                       If None, uses default tools.

    Returns:
        True if all tools are available, False otherwise
    """
    if required_tools is None:
        required_tools = {
            "pandoc": "Document conversion",
            "xelatex": "LaTeX compilation",
        }

    all_present = True
    for tool, purpose in required_tools.items():
        if shutil.which(tool):
            logger.debug(f"'{tool}' available ({purpose})")
        else:
            logger.error(f"'{tool}' not found ({purpose})")
            all_present = False

    if all_present:
        log_success(f"All {len(required_tools)} build tools available", logger)
    return all_present


from infrastructure.core.install_commands import build_install_commands  # noqa: E402, F401
