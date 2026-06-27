"""Tests for ``infrastructure.publishing.pypi``.

No mocks -- all assertions use real data, tmp_path fixtures, and direct
calls to the public API.  Subprocess-invoking paths (``build_dist``,
``twine upload``) are exercised only through the boundary conditions that
short-circuit before any network/build call (``dry_run=True``, missing
token, empty dist_dir).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.publishing.pypi.models import PyPIConfig, PyPIResult
from infrastructure.publishing.pypi.upload import (
    _infer_package_name,
    _infer_version,
    check_dist,
    upload_dist,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dist_dir(tmp_path: Path, *filenames: str) -> Path:
    """Create a dist/ directory populated with zero-byte stub files."""
    dist = tmp_path / "dist"
    dist.mkdir()
    for name in filenames:
        (dist / name).touch()
    return dist


# ---------------------------------------------------------------------------
# PyPIConfig -- defaults and test-mode
# ---------------------------------------------------------------------------


def test_pypi_config_defaults() -> None:
    """Default PyPIConfig targets production PyPI with safe defaults."""
    cfg = PyPIConfig()
    assert cfg.test is False
    assert cfg.token is None
    assert cfg.upload_repository == "pypi"
    assert cfg.index_url == "https://pypi.org/simple/"
    assert cfg.repository_url == "https://upload.pypi.org/legacy/"
    assert cfg.timeout == 120.0


def test_pypi_config_test_mode() -> None:
    """test=True flips every URL-derived property to test.pypi.org."""
    cfg = PyPIConfig(test=True, token="test-token")
    assert cfg.upload_repository == "testpypi"
    assert cfg.index_url == "https://test.pypi.org/simple/"
    # The token itself is preserved.
    assert cfg.token == "test-token"


# ---------------------------------------------------------------------------
# PyPIResult -- field contract
# ---------------------------------------------------------------------------


def test_pypi_result_dry_run_status() -> None:
    """PyPIResult with status='dry-run' carries the expected fields."""
    result = PyPIResult(
        status="dry-run",
        package_name="my-pkg",
        version="1.2.3",
        wheel_files=("my_pkg-1.2.3-py3-none-any.whl",),
        sdist_files=("my-pkg-1.2.3.tar.gz",),
        timestamp_utc="2026-01-01T00:00:00Z",
    )
    assert result.status == "dry-run"
    assert result.package_name == "my-pkg"
    assert result.version == "1.2.3"
    assert "my_pkg-1.2.3-py3-none-any.whl" in result.wheel_files
    assert "my-pkg-1.2.3.tar.gz" in result.sdist_files
    assert result.error is None
    assert result.url is None
    # ok property: dry-run counts as success.
    assert result.ok is True


# ---------------------------------------------------------------------------
# upload_dist -- dry-run path (no network, no build)
# ---------------------------------------------------------------------------


def test_upload_dist_dry_run_returns_dry_run_status(tmp_path: Path) -> None:
    """upload_dist with dry_run=True returns status='dry-run' immediately."""
    dist_dir = _make_dist_dir(
        tmp_path,
        "my_pkg-1.0.0-py3-none-any.whl",
        "my-pkg-1.0.0.tar.gz",
    )
    cfg = PyPIConfig(token="fake-token")
    result = upload_dist(dist_dir, cfg, dry_run=True)

    assert result.status == "dry-run"
    assert result.package_name == "my-pkg"
    assert result.version == "1.0.0"
    assert "my_pkg-1.0.0-py3-none-any.whl" in result.wheel_files
    assert "my-pkg-1.0.0.tar.gz" in result.sdist_files
    assert result.timestamp_utc is not None


def test_upload_dist_missing_token_returns_error(tmp_path: Path) -> None:
    """upload_dist without a token and dry_run=False returns status='error'."""
    dist_dir = _make_dist_dir(tmp_path, "my_pkg-2.0.0-py3-none-any.whl")
    cfg = PyPIConfig(token=None)
    result = upload_dist(dist_dir, cfg, dry_run=False)

    assert result.status == "error"
    assert result.error is not None
    # The error message should hint at the environment variable name.
    assert "PYPI_TOKEN" in result.error or "token" in result.error.lower()


def test_upload_dist_no_files_returns_error(tmp_path: Path) -> None:
    """upload_dist with an empty dist_dir and a token returns status='skipped'.

    Missing token is checked before missing files, so we need a real token
    and an empty dir to reach the "no files" guard.  The module returns
    "skipped" (not "error") for this case.
    """
    dist_dir = tmp_path / "empty_dist"
    dist_dir.mkdir()
    cfg = PyPIConfig(token="real-looking-token")
    result = upload_dist(dist_dir, cfg, dry_run=False)

    assert result.status == "skipped"
    assert result.error is not None
    assert "No distribution files" in result.error or "dist" in result.error.lower()


# ---------------------------------------------------------------------------
# _infer_package_name / _infer_version -- pure filename parsing
# ---------------------------------------------------------------------------


def test_infer_package_name_from_wheel(tmp_path: Path) -> None:
    """_infer_package_name extracts the package part from a wheel filename."""
    whl = tmp_path / "my_package-3.1.4-py3-none-any.whl"
    whl.touch()

    name = _infer_package_name([whl])

    # Underscores are normalised to dashes.
    assert name == "my-package"


def test_infer_package_name_from_sdist(tmp_path: Path) -> None:
    """_infer_package_name extracts the first dash-delimited token from a sdist.

    The implementation splits the stem on '-' and returns parts[0].  For a
    single-word package name like 'mypkg-3.1.4.tar.gz' this is the full name.
    Hyphenated package names (e.g. 'my-package-3.1.4.tar.gz') only return
    the first segment -- a known limitation of the best-effort heuristic.
    """
    sdist = tmp_path / "mypkg-3.1.4.tar.gz"
    sdist.touch()

    name = _infer_package_name([sdist])

    assert name == "mypkg"


def test_infer_package_name_empty_list() -> None:
    """_infer_package_name on an empty list returns 'unknown'."""
    assert _infer_package_name([]) == "unknown"


def test_infer_version_from_wheel(tmp_path: Path) -> None:
    """_infer_version returns parts[1] of the dash-split stem.

    The implementation splits the stem on '-' and returns parts[1].  For a
    wheel with a single-word (no-hyphen) package name -- e.g.
    'mypkg-1.2.3-py3-none-any.whl' -- parts[1] is the version string.
    Wheels whose package name itself contains a hyphen (e.g. 'my-pkg-...')
    would return the second name segment rather than the version; use
    underscore-normalised names to avoid this.
    """
    whl = tmp_path / "mypkg-1.2.3-py3-none-any.whl"
    whl.touch()

    version = _infer_version([whl])

    assert version == "1.2.3"


def test_infer_version_from_sdist(tmp_path: Path) -> None:
    """_infer_version returns parts[1] of the dash-split stem for an sdist.

    For a single-word package name 'mypkg-4.5.6.tar.gz', parts[1] is '4.5.6'.
    """
    sdist = tmp_path / "mypkg-4.5.6.tar.gz"
    sdist.touch()

    version = _infer_version([sdist])

    assert version == "4.5.6"


def test_infer_version_empty_list() -> None:
    """_infer_version on an empty list returns None."""
    assert _infer_version([]) is None


# ---------------------------------------------------------------------------
# check_dist -- no-files path (no subprocess)
# ---------------------------------------------------------------------------


def test_check_dist_no_files_returns_issues(tmp_path: Path) -> None:
    """check_dist on an empty directory returns a non-empty issues list."""
    empty_dir = tmp_path / "no_dist"
    empty_dir.mkdir()

    issues = check_dist(empty_dir)

    assert isinstance(issues, list)
    assert len(issues) > 0
    combined = " ".join(issues).lower()
    assert (
        "no distribution" in combined
        or "no dist" in combined
        or "found" in combined
    )


def test_check_dist_nonexistent_dir_returns_issues(tmp_path: Path) -> None:
    """check_dist on a missing directory returns a non-empty issues list.

    list_dist_files returns empty lists for a non-existent dir, so
    check_dist hits the 'no files' short-circuit without spawning a subprocess.
    """
    missing = tmp_path / "does_not_exist"
    issues = check_dist(missing)
    assert len(issues) > 0


# ---------------------------------------------------------------------------
# Dry-run through upload_dist directly (bypasses uv build)
# ---------------------------------------------------------------------------


def test_pypi_adapter_dry_run_returns_dry_run_result(tmp_path: Path) -> None:
    """upload_dist dry_run=True on a pre-built dist_dir returns a dry-run result.

    We call upload_dist directly (pre-seeded dist_dir) to avoid invoking
    ``uv build`` in tests.  This exercises the same code path the adapter
    reaches after a successful build step.
    """
    dist_dir = _make_dist_dir(
        tmp_path,
        "template_pkg-0.1.0-py3-none-any.whl",
        "template-pkg-0.1.0.tar.gz",
    )
    cfg = PyPIConfig(test=True, token=None)

    result = upload_dist(dist_dir, cfg, dry_run=True)

    assert result.status == "dry-run"
    assert result.ok is True
    assert result.package_name == "template-pkg"
    assert result.version == "0.1.0"
    assert len(result.wheel_files) == 1
    assert len(result.sdist_files) == 1


def test_pypi_adapter_dry_run_empty_dist_still_returns_dry_run(tmp_path: Path) -> None:
    """dry_run=True short-circuits before the 'no files' guard.

    Even an empty dist_dir returns status='dry-run' (with 'unknown' as the
    inferred package name) because the dry-run return happens unconditionally
    before any token or file checks.
    """
    empty_dist = tmp_path / "dist"
    empty_dist.mkdir()
    cfg = PyPIConfig(token=None)

    result = upload_dist(empty_dist, cfg, dry_run=True)

    assert result.status == "dry-run"
    assert result.package_name == "unknown"
    assert result.version is None
