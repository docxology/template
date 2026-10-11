"""Canonical platform package previews and exact TestPyPI sandbox transfers.

The TestPyPI result includes actual retrieval and installed smoke. Production
promotion requires a separately reviewed exact-revision release contract.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from .models import PyPIConfig, PyPIResult


def run_pypi_release(
    project_root: Path,
    *,
    token: str | None = None,
    test: bool = True,
    dry_run: bool = True,
) -> PyPIResult:
    """Run an exact sandbox transfer or local admission preview; never claim readiness."""
    return PyPIAdapter(PyPIConfig(token=token, test=test)).publish(project_root, dry_run=dry_run)


class PyPIAdapter:
    """Public operating adapter with bounded, source-bound platform admission."""

    name: str = "pypi"

    def __init__(self, config: PyPIConfig | None = None, *, env: dict[str, str] | None = None) -> None:
        source = env if env is not None else dict(os.environ)
        config = config or PyPIConfig()
        self.config = PyPIConfig(
            token=config.token
            or source.get("TEST_PYPI_API_TOKEN" if config.test else "PYPI_TOKEN")
            or source.get("TESTPYPI_TOKEN" if config.test else "PYPI_TOKEN"),
            repository_url=config.repository_url,
            test=config.test,
            timeout=config.timeout,
        )

    def publish(self, project_root: Path, *, dry_run: bool = True) -> PyPIResult:
        """Build an admitted local preview, or perform the canonical sandbox transfer.

        Every invocation uses fresh private output. Imports of the public
        adapter/model surface do not load build or acceptance implementations.
        """
        # Rendering imports the public publishing package while installed
        # artifact contracts are still initializing. Load executable acceptance
        # only when explicitly invoked, after package initialization completes.
        from infrastructure.publishing.pypi_release import (
            Deadline,
            TestPyPIError,
            _redact,
            build_package,
            freeze_build_source,
            run_test_pypi_release,
        )

        package, version = "unknown", None
        try:
            if not dry_run:
                if not self.config.test:
                    raise TestPyPIError(
                        "production promotion requires the separate reviewed release contract",
                        state="blocked",
                        exit_code=75,
                    )
                if self.config.repository_url not in {
                    "https://upload.pypi.org/legacy/",
                    "https://test.pypi.org/legacy/",
                }:
                    raise ValueError("canonical sandbox adapter refuses alternate repository authority")
                receipt = run_test_pypi_release(
                    self.config.token or "",
                    repo_root=project_root,
                    timeout_seconds=self.config.timeout,
                )
                artifacts = receipt["transfer"]["artifacts"]
                return PyPIResult(
                    "ok",
                    receipt["package"],
                    receipt["version"],
                    url=f"https://test.pypi.org/project/{receipt['package']}/{receipt['version']}/",
                    wheel_files=tuple(item["filename"] for item in artifacts if item["filename"].endswith(".whl")),
                    sdist_files=tuple(item["filename"] for item in artifacts if item["filename"].endswith(".tar.gz")),
                    receipt=receipt,
                )
            deadline = Deadline.start(self.config.timeout)
            uv = shutil.which("uv")
            if uv is None:
                raise TestPyPIError("prepared uv is unavailable", state="blocked", exit_code=75)
            with tempfile.TemporaryDirectory(prefix="template-pypi-preview-") as temporary:
                scratch = Path(temporary).resolve()
                source = freeze_build_source(project_root, scratch, deadline)
                package, version = source.requirement.package, source.requirement.version
                _, distributions = build_package(source, scratch, uv, deadline)
                return PyPIResult(
                    "dry-run",
                    package,
                    version,
                    wheel_files=tuple(item.path.name for item in distributions if item.kind == "wheel"),
                    sdist_files=tuple(item.path.name for item in distributions if item.kind == "sdist"),
                    receipt={
                        "assurance": "local build and exact source admission only",
                        "status": "dry-run",
                        "source_identity": source.requirement.source_identity,
                        "artifacts": {item.path.name: item.sha256 for item in distributions},
                        "publication": "not performed",
                        "installed_acceptance": "not performed",
                    },
                )
        except TestPyPIError as exc:
            return PyPIResult(exc.state, package, version, error=_redact(str(exc), (self.config.token or "",)))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return PyPIResult("error", package, version, error=_redact(str(exc), (self.config.token or "",)))
