"""Package installation and environment variable configuration.

Handles installing missing packages via uv, setting pipeline environment
variables, and validating uv sync results.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.runtime._python_env import check_uv_available, get_subprocess_env

logger = get_logger(__name__)


def install_missing_packages(packages: list[str], cwd: Path | None = None) -> bool:
    """Install packages with ``uv pip install`` when uv is available.

    Args:
        packages: Package names/specifiers for pip.
        cwd: Working directory for the subprocess (optional).

    Returns:
        True on success, False if uv is missing or the install command fails.
    """
    if not packages:
        return True
    if not check_uv_available():
        logger.warning("install_missing_packages: uv not on PATH")
        return False
    cmd = ["uv", "pip", "install", *packages]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
            env=get_subprocess_env(),
        )
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.error(f"install_missing_packages failed: {e}", exc_info=True)
        return False
    if result.returncode != 0:
        logger.error(
            "install_missing_packages: uv pip install failed: %s",
            (result.stderr or result.stdout or "").strip() or "(no output)",
        )
        return False
    log_success(f"Installed packages: {', '.join(packages)}", logger)
    return True


def set_environment_variables(repo_root: Path) -> bool:
    """Configure environment variables for pipeline.

    Sets MPLBACKEND=Agg (headless matplotlib), PYTHONIOENCODING=utf-8,
    and PROJECT_ROOT for the pipeline scripts.

    Args:
        repo_root: Repository root directory

    Returns:
        True if environment variables set successfully, False otherwise
    """
    # Set matplotlib backend for headless operation
    os.environ["MPLBACKEND"] = "Agg"

    # Ensure UTF-8 encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # Set project root in environment
    os.environ["PROJECT_ROOT"] = str(repo_root)

    log_success(
        "Environment variables configured (MPLBACKEND, PYTHONIOENCODING, PROJECT_ROOT)", logger
    )
    return True


def validate_uv_sync_result(repo_root: Path) -> tuple[bool, str]:
    """Check for .venv/ and uv.lock after uv sync; returns (success, message)."""
    # Check for .venv directory
    venv_path = repo_root / ".venv"
    if not venv_path.exists():
        return False, "Virtual environment not created"

    # Check for uv.lock file
    lock_file = repo_root / "uv.lock"
    if not lock_file.exists():
        return False, "Lock file not generated"

    return True, "uv sync completed successfully"


def check_build_tools(tools: dict[str, str]) -> bool:
    """Return True if every named executable is on PATH.

    Args:
        tools: Map of executable name to short human-readable purpose (for logging).

    Returns:
        True when all tools are found, False if any are missing.
    """
    import shutil

    all_ok = True
    for name, purpose in tools.items():
        if shutil.which(name):
            logger.debug(f"Build tool OK: {name} ({purpose})")
        else:
            logger.warning(f"Build tool missing: {name} ({purpose})")
            all_ok = False
    return all_ok
