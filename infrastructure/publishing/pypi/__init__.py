"""PyPI / TestPyPI publishing adapter.

Public surface::

    from infrastructure.publishing.pypi import (
        PyPIAdapter,
        PyPIConfig,
        PyPIResult,
        build_dist,
        upload_dist,
        check_dist,
        run_pypi_release,
        verify_install,
    )

``dry_run=True`` is the default everywhere — no accidental uploads.
"""

from __future__ import annotations

from .adapter import PyPIAdapter, run_pypi_release
from .build import build_dist
from .models import PyPIConfig, PyPIResult
from .upload import check_dist, upload_dist
from .verify import verify_install

__all__ = [
    "PyPIAdapter",
    "PyPIConfig",
    "PyPIResult",
    "build_dist",
    "check_dist",
    "run_pypi_release",
    "upload_dist",
    "verify_install",
]
