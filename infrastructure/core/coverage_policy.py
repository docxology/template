"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.coverage_policy``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.coverage_policy`` directly.
"""

from infrastructure.core.testing.coverage_policy import (  # noqa: F401
    PYTEST_HELP_PROBE_TIMEOUT_SECONDS,
    check_cov_datafile_support,
)

__all__ = [
    "PYTEST_HELP_PROBE_TIMEOUT_SECONDS",
    "check_cov_datafile_support",
]
