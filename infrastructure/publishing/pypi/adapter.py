"""High-level PyPIAdapter — thin orchestrator following the ArchivalProvider-style pattern.

Usage (production upload)::

    from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

    adapter = PyPIAdapter(PyPIConfig(test=True))   # reads TESTPYPI_TOKEN from env
    result = adapter.publish(Path("."), dry_run=False)
    print(result.url)

Usage (dry-run, always safe)::

    result = adapter.publish(Path("."), dry_run=True)
    assert result.status == "dry-run"

The adapter never raises on upload failure — callers inspect ``PyPIResult.status``
and ``PyPIResult.error``.
"""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .build import build_dist
from .models import PyPIConfig, PyPIResult
from .upload import check_dist, upload_dist

logger = get_logger(__name__)


def run_pypi_release(
    project_root: Path,
    *,
    token: str | None = None,
    test: bool = True,
    dry_run: bool = True,
    package_name: str | None = None,
    entry_point: str | None = None,
    verify: bool = False,
) -> PyPIResult:
    """Convenience one-liner: build → check → upload → (optionally) verify.

    Equivalent to constructing a :class:`PyPIAdapter` and calling
    :meth:`~PyPIAdapter.publish`, with an optional post-upload install
    verification step.

    Parameters
    ----------
    project_root:
        Root of the Python project (contains ``pyproject.toml``).
    token:
        PyPI / TestPyPI API token.  When ``None`` the token is read from the
        environment (``TESTPYPI_TOKEN`` when *test* is True, else
        ``PYPI_TOKEN``).
    test:
        Target TestPyPI (``test.pypi.org``) when True.
    dry_run:
        Skip real uploads when True (default).
    package_name:
        Required when *verify* is True so the install step knows what to
        ``pip install``.
    entry_point:
        Console-script name to smoke-test after installation.
    verify:
        Run :func:`.verify.verify_install` after a successful upload.

    Returns
    -------
    PyPIResult
        Result of the upload step (not the verify step).  Verify failures are
        logged as warnings.
    """
    config = PyPIConfig(token=token, test=test)
    adapter = PyPIAdapter(config)
    result = adapter.publish(project_root, dry_run=dry_run)

    if verify and result.ok and not dry_run:
        from .verify import verify_install

        name = package_name or result.package_name
        ok = verify_install(
            name,
            config,
            version=result.version,
            entry_point=entry_point,
        )
        if not ok:
            logger.warning(
                "Post-upload install verification FAILED for %s==%s",
                name,
                result.version,
            )

    return result


class PyPIAdapter:
    """Build → check → upload orchestrator for PyPI / TestPyPI.

    Follows the same structural contract as the ``ArchivalProvider`` protocol
    in ``infrastructure.publishing.archival``:

    - ``name`` class attribute identifies the adapter.
    - ``dry_run=True`` is the default at every layer.
    - Credentials are resolved from the environment when not provided at
      construction time.
    - The adapter never raises on upload failure; callers inspect
      :class:`PyPIResult`.

    Parameters
    ----------
    config:
        Upload target configuration.  When ``None`` a default
        :class:`PyPIConfig` targeting production PyPI is constructed.
    env:
        Environment mapping used to resolve missing tokens.  Defaults to
        ``os.environ``.  Passing a custom dict makes the adapter fully
        testable without real env variables.
    """

    name: str = "pypi"

    def __init__(
        self,
        config: PyPIConfig | None = None,
        *,
        env: dict[str, str] | None = None,
    ) -> None:
        source = env if env is not None else dict(os.environ)

        if config is None:
            config = PyPIConfig(
                token=source.get("PYPI_TOKEN"),
                test=False,
            )
        elif config.token is None:
            # Fill in the token from the environment using the correct key.
            env_key = "TESTPYPI_TOKEN" if config.test else "PYPI_TOKEN"
            config = PyPIConfig(
                token=source.get(env_key),
                repository_url=config.repository_url,
                test=config.test,
                timeout=config.timeout,
            )

        self.config = config

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def publish(
        self,
        project_root: Path,
        *,
        dry_run: bool = True,
        run_check: bool = True,
        dist_dir: Path | None = None,
    ) -> PyPIResult:
        """Build, optionally check, and upload the package.

        Steps
        -----
        1. ``uv build`` — creates wheel + sdist in *dist_dir* (default:
           ``project_root/dist``).
        2. ``twine check`` — validates the artefacts (skipped when
           ``run_check=False``).
        3. ``twine upload`` — skipped in dry-run mode.

        Parameters
        ----------
        project_root:
            Directory containing ``pyproject.toml``.
        dry_run:
            When ``True`` (default) the upload step is skipped and a
            ``"dry-run"`` :class:`PyPIResult` is returned.
        run_check:
            Run ``twine check`` before uploading.  Failures produce an
            ``"error"`` result and abort the upload.
        dist_dir:
            Override the default ``project_root/dist`` build output directory.

        Returns
        -------
        PyPIResult
            Structured result; never raises.
        """
        # Step 1 — build
        try:
            dist = build_dist(project_root, dist_dir=dist_dir)
        except RuntimeError as exc:
            return PyPIResult(
                status="error",
                package_name="unknown",
                version=None,
                error=f"Build failed: {exc}",
            )

        # Step 2 — check
        if run_check:
            issues = check_dist(dist)
            if issues:
                return PyPIResult(
                    status="error",
                    package_name="unknown",
                    version=None,
                    error=f"twine check failed: {'; '.join(issues)}",
                )

        # Step 3 — upload (or dry-run)
        return upload_dist(dist, self.config, dry_run=dry_run)
