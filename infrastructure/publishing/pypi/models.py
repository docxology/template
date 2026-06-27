"""Data models for PyPI/TestPyPI publishing."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PyPIConfig:
    """Configuration for a PyPI/TestPyPI upload target.

    ``test=True`` routes all operations to test.pypi.org.
    ``token`` may be left None at construction time; the adapter resolves it
    from the environment (``PYPI_TOKEN`` / ``TESTPYPI_TOKEN``) before upload.
    ``timeout`` is passed to twine-equivalent network operations.
    """

    token: str | None = None
    repository_url: str = "https://upload.pypi.org/legacy/"
    test: bool = False  # True => use test.pypi.org
    timeout: float = 120.0

    @property
    def upload_repository(self) -> str:
        """Repository name recognised by twine's ``--repository`` flag."""
        if self.test:
            return "testpypi"
        return "pypi"

    @property
    def index_url(self) -> str:
        """Simple index URL for ``pip install --index-url``."""
        if self.test:
            return "https://test.pypi.org/simple/"
        return "https://pypi.org/simple/"


@dataclass(frozen=True)
class PyPIResult:
    """Result of a single PyPI build/check/upload attempt.

    ``status`` values:

    - ``"ok"``      — upload completed successfully.
    - ``"error"``   — something failed; see ``error``.
    - ``"dry-run"`` — skipped intentionally; would have uploaded.
    - ``"skipped"`` — prerequisite missing (e.g. no dist files to upload).
    """

    status: str  # "ok" | "error" | "dry-run" | "skipped"
    package_name: str
    version: str | None
    url: str | None = None
    wheel_files: tuple[str, ...] = field(default_factory=tuple)
    sdist_files: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    timestamp_utc: str | None = None

    @property
    def ok(self) -> bool:
        """True if the result is considered successful (ok or dry-run)."""
        return self.status in {"ok", "dry-run"}
