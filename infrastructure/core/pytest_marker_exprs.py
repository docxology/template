"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.pytest_marker_exprs``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.pytest_marker_exprs`` directly.
"""

from infrastructure.core.testing.pytest_marker_exprs import (  # noqa: F401
    build_pytest_marker_expression,
)

__all__ = [
    "build_pytest_marker_expression",
]
