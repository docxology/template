"""Install-and-verify helpers for post-upload smoke testing.

Creates an isolated venv, installs the published package from the configured
index URL, and optionally runs an entry-point to confirm the wheel is
importable and functional.

No mocks required in tests: callers can pass a ``config`` that points at
a local devpi / puffin index, or skip verification entirely in dry-run mode.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .models import PyPIConfig

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _venv_bin(venv: Path, name: str) -> Path:
    """Resolve the OS-appropriate binary path inside *venv*.

    On POSIX the binary lives under ``bin/``; on Windows under ``Scripts/``.
    """
    unix = venv / "bin" / name
    if unix.exists():
        return unix
    # Windows fallback
    win = venv / "Scripts" / f"{name}.exe"
    if win.exists():
        return win
    # Return unix path regardless — subprocess will surface a useful error.
    return unix


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_install(
    package_name: str,
    config: PyPIConfig,
    *,
    version: str | None = None,
    entry_point: str | None = None,
    extra_pip_args: list[str] | None = None,
) -> bool:
    """Smoke-test that *package_name* can be installed from *config.index_url*.

    Procedure
    ---------
    1. Create a temporary virtual environment.
    2. ``pip install [--index-url <url>] <package_name>[==<version>]``
    3. If *entry_point* is given, run ``<entry_point> --help`` and check that
       it exits 0.

    Parameters
    ----------
    package_name:
        PyPI package name, e.g. ``"my-package"``.
    config:
        Determines which index URL to install from.
    version:
        Optional version pin.  When supplied the install target becomes
        ``package_name==version``.
    entry_point:
        Name of the console-script entry point to smoke-test.  Skipped when
        ``None``.
    extra_pip_args:
        Additional arguments forwarded verbatim to the ``pip install`` call
        (e.g. ``["--no-deps"]``).

    Returns
    -------
    bool
        ``True`` when installation (and optional entry-point check) succeeded,
        ``False`` on any failure.
    """
    install_target = package_name if version is None else f"{package_name}=={version}"

    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp) / "venv"

        # Create venv
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Failed to create venv: %s", exc.stderr)
            return False

        pip = _venv_bin(venv, "pip")

        # Install from the configured index
        pip_cmd: list[str] = [
            str(pip),
            "install",
            "--index-url",
            config.index_url,
            install_target,
        ]
        if extra_pip_args:
            pip_cmd.extend(extra_pip_args)

        try:
            subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            logger.error(
                "pip install of %s from %s failed: %s",
                install_target,
                config.index_url,
                exc.stderr.strip() or exc.stdout.strip(),
            )
            return False

        # Optional entry-point smoke test
        if entry_point is not None:
            ep = _venv_bin(venv, entry_point)
            result = subprocess.run(
                [str(ep), "--help"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.warning(
                    "Entry point '%s --help' returned exit code %d: %s",
                    entry_point,
                    result.returncode,
                    result.stderr.strip() or result.stdout.strip(),
                )
                return False

        logger.info(
            "Install verification passed: %s from %s",
            install_target,
            config.index_url,
        )
        return True
