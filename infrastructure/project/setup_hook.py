"""Optional per-project ``setup_hook`` runner.

A project may ship a one-time environment-bootstrap script alongside its
analysis scripts:

* ``projects/<name>/scripts/setup_hook.py`` — preferred (cross-platform).
* ``projects/<name>/scripts/setup_hook.sh`` — POSIX-only fallback.

The hook is discovered by :func:`find_setup_hook` and invoked by
:func:`run_project_setup_hook` from the Stage 0 / Stage 1 setup script
(``scripts/00_setup_environment.py``). On Windows, only the ``.py`` form is
honoured; ``.sh`` hooks are skipped with a warning because POSIX shells are
not guaranteed to be available.

The hook may declare a small YAML manifest at
``projects/<name>/scripts/setup_hook.yaml`` to advertise prerequisites:

.. code-block:: yaml

    description: "Free-text purpose"
    required_tools: ["elan", "lake", "gauss"]   # binaries that must be on PATH
    required_env: ["HF_TOKEN"]                   # required env vars (presence only)
    timeout_sec: 1800                            # overrides PROJECT_SETUP_HOOK_TIMEOUT_SEC
    skip_if_env: ["CI_NO_HOOKS"]                 # truthy env vars that disable the hook

All manifest fields are optional. A project without ``setup_hook.yaml``
behaves as it always has — the hook simply runs to completion (or times out).

Environment knobs:

* ``PROJECT_SETUP_HOOK_TIMEOUT_SEC`` — global default timeout (3600 s).
* ``PROJECT_SETUP_HOOK_DRY_RUN`` — truthy values cause :func:`run_project_setup_hook`
  to perform the preflight, log what *would* run, and return ``True`` without
  invoking the hook.

The module follows the No-Mocks policy: tests exercise real ``tmp_path`` projects
and real subprocesses.
"""

import os
import platform
import shutil

# Required to invoke the project-supplied setup hook.
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover — pyyaml is a hard project dep
    _yaml = None  # type: ignore[assignment]

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SEC: int = 3600
"""Fallback timeout when neither manifest nor env var is set."""

_TRUTHY = {"1", "true", "yes", "on"}


def _is_truthy(val: str | None) -> bool:
    """Return ``True`` for typical truthy env-var values."""
    return val is not None and val.strip().lower() in _TRUTHY


def _is_windows() -> bool:
    """Return ``True`` on Windows hosts (used to gate ``.sh`` hooks)."""
    return platform.system() == "Windows"


def find_setup_hook(project_dir: Path) -> Path | None:
    """Locate the project's setup hook script, if any.

    Args:
        project_dir: Path to the project directory (``projects/<name>``).

    Returns:
        The hook ``Path`` if found, else ``None``.

    Resolution order:
        1. ``scripts/setup_hook.py``
        2. ``scripts/setup_hook.sh`` (skipped on Windows)
    """
    scripts = project_dir / "scripts"
    py_hook = scripts / "setup_hook.py"
    if py_hook.is_file():
        return py_hook
    sh_hook = scripts / "setup_hook.sh"
    if sh_hook.is_file():
        if _is_windows():
            logger.warning(
                "Found %s but POSIX shell hooks are not supported on Windows; provide a setup_hook.py instead.",
                sh_hook,
            )
            return None
        return sh_hook
    return None


def _manifest_path(hook: Path) -> Path:
    """Return the manifest path that lives alongside ``hook``."""
    return hook.parent / "setup_hook.yaml"


def _load_manifest(hook: Path) -> dict[str, Any]:
    """Load and lightly validate ``setup_hook.yaml`` (if present).

    Unknown keys are preserved but ignored. Type errors are reported and a
    safe empty manifest is returned, so a malformed YAML file degrades to
    "no manifest" rather than aborting setup.
    """
    manifest_file = _manifest_path(hook)
    if not manifest_file.is_file():
        return {}
    if _yaml is None:  # pragma: no cover — pyyaml is a hard dep
        logger.warning("PyYAML unavailable; ignoring %s", manifest_file)
        return {}
    try:
        with manifest_file.open("r", encoding="utf-8") as fh:
            data = _yaml.safe_load(fh)
    except (OSError, _yaml.YAMLError) as exc:
        logger.warning("Failed to parse %s: %s", manifest_file, exc)
        return {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.warning("%s must be a mapping at top level; ignoring", manifest_file)
        return {}
    return data


def _coerce_str_list(value: Any, field: str, manifest: Path) -> list[str]:
    """Coerce a manifest field to ``list[str]`` with a friendly warning."""
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return list(value)
    logger.warning("%s: %s must be a list of strings; got %r", manifest, field, value)
    return []


def preflight_setup_hook(project_dir: Path) -> tuple[bool, list[str]]:
    """Validate the project's setup-hook prerequisites.

    Reads ``setup_hook.yaml`` if present and verifies declared
    ``required_tools`` are on ``PATH`` and declared ``required_env`` vars
    are set. Honours ``skip_if_env`` — if any listed env var is truthy,
    the preflight returns ``(True, ["skipped: <var>"])`` so the caller can
    log the reason and short-circuit.

    Args:
        project_dir: Path to the project directory (``projects/<name>``).

    Returns:
        ``(ok, messages)`` — ``ok=True`` means the hook may run (or was
        intentionally skipped). ``messages`` is a list of human-readable
        notes: failure reasons when ``ok=False``, or ``"skipped: <var>"``
        entries when ``ok=True`` due to ``skip_if_env``. When there is no
        hook and no manifest, returns ``(True, [])``.
    """
    hook = find_setup_hook(project_dir)
    if hook is None:
        # No hook → trivially OK, even if a manifest is somehow present.
        return True, []

    manifest = _load_manifest(hook)
    manifest_path = _manifest_path(hook)

    # skip_if_env short-circuits everything else.
    skip_vars = _coerce_str_list(manifest.get("skip_if_env"), "skip_if_env", manifest_path)
    for var in skip_vars:
        if _is_truthy(os.environ.get(var)):
            return True, [f"skipped: {var}"]

    errors: list[str] = []

    required_tools = _coerce_str_list(manifest.get("required_tools"), "required_tools", manifest_path)
    missing_tools = [tool for tool in required_tools if shutil.which(tool) is None]
    if missing_tools:
        errors.append("Hook needs: " + ", ".join(f"{t} (not on PATH)" for t in missing_tools))

    required_env = _coerce_str_list(manifest.get("required_env"), "required_env", manifest_path)
    missing_env = [name for name in required_env if not os.environ.get(name)]
    if missing_env:
        errors.append("Hook needs env: " + ", ".join(missing_env))

    return (not errors), errors


def _resolved_timeout(hook: Path) -> int:
    """Return the timeout (seconds) for ``hook``.

    Precedence (highest first):
      1. ``timeout_sec`` in ``setup_hook.yaml`` (must be a positive int).
      2. ``PROJECT_SETUP_HOOK_TIMEOUT_SEC`` env var.
      3. :data:`DEFAULT_TIMEOUT_SEC`.
    """
    manifest = _load_manifest(hook)
    raw = manifest.get("timeout_sec")
    if isinstance(raw, int) and raw > 0:
        return raw
    if raw is not None:
        logger.warning(
            "%s: timeout_sec must be a positive int; got %r — falling back to env/default",
            _manifest_path(hook),
            raw,
        )
    env_raw = os.environ.get("PROJECT_SETUP_HOOK_TIMEOUT_SEC")
    if env_raw:
        try:
            parsed = int(env_raw)
            if parsed > 0:
                return parsed
        except ValueError:
            logger.warning(
                "PROJECT_SETUP_HOOK_TIMEOUT_SEC=%r is not an int; using default %d",
                env_raw,
                DEFAULT_TIMEOUT_SEC,
            )
    return DEFAULT_TIMEOUT_SEC


def _build_command(hook: Path) -> list[str]:
    """Build the argv to invoke ``hook`` (Python or POSIX shell)."""
    if hook.suffix == ".py":
        return [sys.executable, str(hook)]
    return ["bash", str(hook)]


def run_project_setup_hook(project_dir: Path) -> bool:
    """Run the project's setup hook, if present.

    The hook is a one-time bootstrap script (e.g. install a Lean toolchain,
    download a model). It is invoked synchronously with a timeout. Stdout
    and stderr are streamed to the parent process so progress is visible.

    Behaviour:

    * If no hook exists, returns ``True`` (no-op).
    * Runs preflight via :func:`preflight_setup_hook`. If preflight fails
      (e.g. a required tool is missing), logs a single actionable error
      and returns ``False`` *without* invoking the hook.
    * If preflight reports a ``skip_if_env`` skip, logs and returns ``True``.
    * If ``PROJECT_SETUP_HOOK_DRY_RUN`` is truthy, logs what would run and
      returns ``True`` without invoking the hook.
    * Otherwise invokes the hook with the resolved timeout. Non-zero exit
      codes and timeouts are reported and return ``False``.

    Args:
        project_dir: Path to the project directory (``projects/<name>``).

    Returns:
        ``True`` if the hook succeeded, was skipped, or was a dry-run;
        ``False`` if preflight failed or the hook errored/timed out.
    """
    hook = find_setup_hook(project_dir)
    if hook is None:
        logger.debug("No setup_hook for %s — skipping", project_dir.name)
        return True

    ok, messages = preflight_setup_hook(project_dir)
    if not ok:
        # messages is a non-empty list of actionable error strings.
        for msg in messages:
            logger.error("%s setup_hook preflight: %s", project_dir.name, msg)
        return False

    # skip_if_env path
    for msg in messages:
        if msg.startswith("skipped:"):
            logger.info("%s setup_hook %s", project_dir.name, msg)
            return True

    timeout = _resolved_timeout(hook)
    cmd = _build_command(hook)

    if _is_truthy(os.environ.get("PROJECT_SETUP_HOOK_DRY_RUN")):
        logger.info(
            "[dry-run] would run setup_hook for %s: %s (timeout=%ds)",
            project_dir.name,
            " ".join(cmd),
            timeout,
        )
        return True

    logger.info("Running setup_hook for %s: %s (timeout=%ds)", project_dir.name, hook, timeout)
    try:
        # argv is fixed by this module; the hook path is validated as repo-local.
        result = subprocess.run(  # nosec B603
            cmd,
            cwd=str(project_dir),
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error("setup_hook for %s timed out after %ds", project_dir.name, timeout)
        return False
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("setup_hook for %s failed to launch: %s", project_dir.name, exc)
        return False

    if result.returncode != 0:
        logger.error("setup_hook for %s exited with code %d", project_dir.name, result.returncode)
        return False

    logger.info("setup_hook for %s completed successfully", project_dir.name)
    return True


__all__ = [
    "DEFAULT_TIMEOUT_SEC",
    "find_setup_hook",
    "preflight_setup_hook",
    "run_project_setup_hook",
]
