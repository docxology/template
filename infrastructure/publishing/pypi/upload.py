"""Twine-based upload and pre-upload check helpers for PyPI / TestPyPI.

Design constraints:
- ``dry_run=True`` is the safe default throughout; callers opt into real
  network operations explicitly.
- No subprocess call in the unit-testable ``_infer_*`` helpers.
- Token is never logged.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .models import PyPIConfig, PyPIResult

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _infer_package_name(files: list[Path]) -> str:
    """Best-effort package name from wheel / sdist filenames.

    Wheel filename format: ``{name}-{version}-...whl``
    Sdist filename format: ``{name}-{version}.tar.gz``
    """
    for f in files:
        # Strip .tar.gz or .whl suffix, then split on first '-'
        stem = f.stem
        if f.suffix == ".gz" and stem.endswith(".tar"):
            stem = stem[: -len(".tar")]
        parts = stem.split("-")
        if parts:
            return parts[0].replace("_", "-")
    return "unknown"


def _infer_version(files: list[Path]) -> str | None:
    """Best-effort version string from wheel / sdist filenames."""
    for f in files:
        stem = f.stem
        if f.suffix == ".gz" and stem.endswith(".tar"):
            stem = stem[: -len(".tar")]
        parts = stem.split("-")
        if len(parts) >= 2:
            return parts[1]
    return None


def _twine_env(token: str) -> dict[str, str]:
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    return env


def _redact_token(text: str, token: str) -> str:
    if not token:
        return text
    return text.replace(token, "<redacted>")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_dist(dist_dir: Path) -> list[str]:
    """Run ``twine check`` on all distribution files in *dist_dir*.

    Returns a (possibly empty) list of FAILED / ERROR strings.  An empty list
    means twine found no problems.  The function never raises on twine failure
    — it surfaces issues as strings so callers can decide how to handle them.

    Parameters
    ----------
    dist_dir:
        Directory containing ``.whl`` and/or ``.tar.gz`` files.
    """
    files = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
    if not files:
        return ["No distribution files found in dist_dir"]

    result = subprocess.run(
        [sys.executable, "-m", "twine", "check"] + [str(f) for f in sorted(files)],
        capture_output=True,
        text=True,
    )
    issues = [ln.strip() for ln in (result.stdout + result.stderr).splitlines() if "FAILED" in ln or "ERROR" in ln]
    return issues


def upload_dist(
    dist_dir: Path,
    config: PyPIConfig,
    *,
    dry_run: bool = True,
) -> PyPIResult:
    """Upload wheel + sdist artefacts to PyPI or TestPyPI via twine.

    Parameters
    ----------
    dist_dir:
        Directory that holds the ``.whl`` / ``.tar.gz`` artefacts.
    config:
        Target registry configuration including credentials.
    dry_run:
        When ``True`` (default) no network call is made; a ``"dry-run"``
        result is returned describing what *would* happen.

    Returns
    -------
    PyPIResult
        Structured result — never raises on upload failure.
    """
    from .build import list_dist_files

    wheels, sdists = list_dist_files(dist_dir)
    all_files = wheels + sdists
    package_name = _infer_package_name(all_files)
    version = _infer_version(all_files)

    if dry_run:
        logger.info(
            "dry-run: would upload %d file(s) to %s",
            len(all_files),
            config.upload_repository,
        )
        return PyPIResult(
            status="dry-run",
            package_name=package_name,
            version=version,
            url=None,
            wheel_files=tuple(f.name for f in wheels),
            sdist_files=tuple(f.name for f in sdists),
            timestamp_utc=_now_utc(),
        )

    if not config.token:
        return PyPIResult(
            status="error",
            package_name=package_name,
            version=version,
            error=(
                "Missing PyPI token. Set PYPI_TOKEN (production) or "
                "TESTPYPI_TOKEN (test) environment variable, or pass "
                "config.token explicitly."
            ),
            timestamp_utc=_now_utc(),
        )

    if not all_files:
        return PyPIResult(
            status="skipped",
            package_name=package_name,
            version=version,
            error="No distribution files found to upload in dist_dir",
            timestamp_utc=_now_utc(),
        )

    cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--repository",
        config.upload_repository,
        "--non-interactive",
    ] + [str(f) for f in sorted(all_files)]

    result = subprocess.run(cmd, capture_output=True, env=_twine_env(config.token), text=True)
    if result.returncode != 0:
        output = result.stderr.strip() or result.stdout.strip()
        return PyPIResult(
            status="error",
            package_name=package_name,
            version=version,
            error=f"twine upload failed: {_redact_token(output, config.token)}",
            timestamp_utc=_now_utc(),
        )

    pkg_url = f"{config.index_url}{package_name}/"
    logger.info(
        "Uploaded %s==%s to %s",
        package_name,
        version,
        config.upload_repository,
    )
    return PyPIResult(
        status="ok",
        package_name=package_name,
        version=version,
        url=pkg_url,
        wheel_files=tuple(f.name for f in wheels),
        sdist_files=tuple(f.name for f in sdists),
        timestamp_utc=_now_utc(),
    )
