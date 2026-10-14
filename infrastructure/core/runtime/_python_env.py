"""Python interpreter and subprocess environment utilities.

Validates Python version, virtual environment interpreter, uv availability,
and provides subprocess environment configuration.
"""

import os
import platform
import subprocess  # nosec B404
import sys
from pathlib import Path
from collections.abc import Mapping

from infrastructure.core.secrets import strip_secret_env
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.runtime.python_binding import select_analysis_python
from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)

# Public environment-variable name, never a credential value.
_ANALYSIS_SECRET_OPT_IN = "ANALYSIS_ALLOW_SECRETS"  # nosec B105


def validate_analysis_script_path(script_path: Path, project_root: Path) -> Path:
    """Return a runnable project script only when it stays under ``scripts/``.

    Stage 02 normally receives paths from :func:`script_discovery`, but this
    low-level helper is also public and can be called directly. A bounded held
    regular-file read rejects lexical traversal and symlinked ancestors or
    leaves before execution.
    """
    scripts_root = (project_root / "scripts").absolute()
    candidate = Path(script_path).absolute()
    if ".." in candidate.parts:
        raise ValueError("analysis script path cannot contain parent traversal")
    try:
        candidate.relative_to(scripts_root)
    except ValueError as exc:
        raise ValueError(f"analysis script must remain under {scripts_root}: {script_path}") from exc
    if candidate.suffix != ".py":
        raise ValueError(f"analysis script is missing or not a Python file: {script_path}")
    try:
        read_bytes_confined(project_root, candidate, max_bytes=8 * 1024 * 1024)
    except OSError as exc:
        raise ValueError("analysis script must be an existing regular no-follow source file") from exc
    return candidate


def _python_version_supported(version: tuple[int, int]) -> bool:
    """Apply the platform's Python 3.12 floor to an explicit version pair."""
    return version >= (3, 12)


def check_python_version() -> bool:
    """Verify Python 3.12+ is available (matches ``requires-python`` in pyproject.toml)."""
    version_str = platform.python_version()

    if not _python_version_supported((sys.version_info.major, sys.version_info.minor)):
        logger.error(f"Python 3.12+ required, found {version_str}")
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


def get_subprocess_env(
    base_env: dict[str, str] | None = None,
    *,
    redact_secrets: bool = False,
) -> dict[str, str]:
    """Return env dict with VIRTUAL_ENV stripped when uv is active (avoids warnings).

    Args:
        base_env: Base environment dictionary (defaults to os.environ if None)
        redact_secrets: Remove credential-like variable names before returning.

    Returns:
        Environment dictionary suitable for subprocess.run(env=...)
    """
    env = dict(os.environ if base_env is None else base_env)
    if redact_secrets:
        env = strip_secret_env(env)
    # Unset VIRTUAL_ENV when using uv to avoid warnings about absolute paths
    if check_uv_available() and "VIRTUAL_ENV" in env:
        env.pop("VIRTUAL_ENV", None)
    return env


def build_analysis_script_cmd_and_env(
    script_path: Path,
    project_root: Path,
    repo_root: Path,
    *,
    allow_secret_env: bool | None = None,
    base_env: Mapping[str, str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Build the subprocess command and environment for running an analysis script.

    Encapsulates venv detection, PYTHONPATH construction, and matplotlib env
    setup that were previously inline in the analysis orchestrator script.

    Args:
        script_path: Path to the analysis script to execute.
        project_root: Absolute path to the project directory (projects/{name}/).
        repo_root: Absolute path to the repository root.
        allow_secret_env: Explicitly permit credential-like environment
            variables. When omitted, only ``ANALYSIS_ALLOW_SECRETS=1`` (or
            another strict true value) opts in; the default is fail-closed.
        base_env: An already-admitted local environment. Copy it before
            construction so a sequence can freeze mode/epoch without changing
            the process's global environment.

    Returns:
        A (cmd, env) tuple ready for ``subprocess.run(cmd, env=env, ...)``.
    """
    import tempfile

    script_path = validate_analysis_script_path(script_path, project_root)
    source_env = dict(os.environ if base_env is None else base_env)
    if allow_secret_env is None:
        allow_secret_env = source_env.get(_ANALYSIS_SECRET_OPT_IN, "").strip().lower() in {
            "1",
            "true",
            "yes",
        }

    cmd = [str(select_analysis_python(project_root)), str(script_path)]
    env = dict(source_env) if allow_secret_env else strip_secret_env(source_env)
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    env["PYTHONPATH"] = os.pathsep.join(
        [
            # Project root first so scripts can ``from src.<pkg> import ...``
            # (``src`` resolved as a package); ``project_root/src`` keeps the
            # bare ``from <pkg> import`` form working too. Without the root,
            # scripts that do not self-bootstrap sys.path fail with
            # ``No module named 'src'``.
            str(project_root),
            str(project_root / "src"),
            str(repo_root),
            str(repo_root / "infrastructure"),
        ]
    )
    env["PROJECT_DIR"] = str(project_root)
    env.pop("VIRTUAL_ENV", None)

    from infrastructure.core.execution_policy import apply_execution_policy

    return cmd, apply_execution_policy(env, repo_root)
