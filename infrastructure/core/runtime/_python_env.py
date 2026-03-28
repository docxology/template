"""Python interpreter and subprocess environment utilities.

Validates Python version, virtual environment interpreter, uv availability,
and provides subprocess environment configuration.
"""

from __future__ import annotations

import os
import platform
import subprocess  # nosec B404
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


def check_python_version() -> bool:
    """Verify Python 3.10+ is available (matches ``requires-python`` in pyproject.toml)."""
    version_str = platform.python_version()

    if sys.version_info < (3, 10):
        logger.error(f"Python 3.10+ required, found {version_str}")
        return False

    log_success(f"Python {version_str} available", logger)
    return True


def check_uv_available() -> bool:
    """Check if uv package manager is available and working."""
    try:
        result = subprocess.run(  # nosec B603 B607
            ["uv", "--version"], capture_output=True, text=True, check=False, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def get_python_command() -> list[str]:
    """Get sys.executable for subprocess calls."""
    return [sys.executable]


def validate_interpreter() -> bool:
    """Validate that sys.executable is inside the expected virtual environment.

    Checks that the Python interpreter being used is the one managed by
    uv inside the project's .venv directory. This prevents "environment escape"
    where a system Python accidentally intercepts pipeline execution.

    Returns:
        True if interpreter is inside the venv (or no venv is expected), False otherwise.

    Note:
        Logs a warning if the interpreter is outside the venv but does not
        raise an exception, since CI environments and direct invocations
        may have valid reasons for running outside a venv.
    """
    interpreter = Path(sys.executable).resolve()

    # Check if VIRTUAL_ENV is set and matches
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        venv_resolved = Path(venv_path).resolve()
        try:
            interpreter.relative_to(venv_resolved)
            logger.debug(f"Interpreter validated: {interpreter} is inside {venv_resolved}")
            return True
        except ValueError:
            logger.warning(
                f"⚠️  Interpreter escape detected: sys.executable={interpreter} "
                f"is NOT inside VIRTUAL_ENV={venv_resolved}"
            )
            return False

    # Check for .venv in common ancestor directories
    for parent in interpreter.parents:
        if parent.name == ".venv":
            logger.debug(f"Interpreter validated: {interpreter} is inside a .venv")
            return True

    # No venv detected — might be CI or system Python, just note it
    logger.debug(f"No virtual environment detected for interpreter: {interpreter}")
    return True


def get_subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return env dict with VIRTUAL_ENV stripped when uv is active (avoids warnings).

    Args:
        base_env: Base environment dictionary (defaults to os.environ if None)

    Returns:
        Environment dictionary suitable for subprocess.run(env=...)
    """
    env = dict(base_env or os.environ)
    # Unset VIRTUAL_ENV when using uv to avoid warnings about absolute paths
    if check_uv_available() and "VIRTUAL_ENV" in env:
        env.pop("VIRTUAL_ENV", None)
    return env


def build_analysis_script_cmd_and_env(
    script_path: Path, project_root: Path, repo_root: Path
) -> tuple[list[str], dict[str, str]]:
    """Build the subprocess command and environment for running an analysis script.

    Encapsulates venv detection, PYTHONPATH construction, and matplotlib env
    setup that were previously inline in the analysis orchestrator script.

    Args:
        script_path: Path to the analysis script to execute.
        project_root: Absolute path to the project directory (projects/{name}/).
        repo_root: Absolute path to the repository root.

    Returns:
        A (cmd, env) tuple ready for ``subprocess.run(cmd, env=env, ...)``.
    """
    import shutil
    import tempfile

    # Detect project-local venv: if the project has its own .venv with optional
    # dependencies (e.g. discopy), use uv run from the project directory.
    project_venv = project_root / ".venv"
    if project_venv.is_dir():
        uv_path = shutil.which("uv")
        if uv_path:
            cmd: list[str] = [uv_path, "run", "--directory", str(project_root), "python", str(script_path)]
        else:
            cmd = get_python_command() + [str(script_path)]
    else:
        cmd = get_python_command() + [str(script_path)]

    env = get_subprocess_env()
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    env["PYTHONPATH"] = os.pathsep.join([
        str(repo_root),
        str(repo_root / "infrastructure"),
        str(project_root / "src"),
    ])
    env["PROJECT_DIR"] = str(project_root)
    env.pop("VIRTUAL_ENV", None)

    return cmd, env
