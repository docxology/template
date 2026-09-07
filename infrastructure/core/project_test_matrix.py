"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.project_test_matrix``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.project_test_matrix`` directly.
"""

from infrastructure.core.testing.project_test_matrix import (  # noqa: F401
    ProjectTestResult,
    ProjectTestTask,
    run_project_test_matrix,
)

__all__ = [
    "ProjectTestResult",
    "ProjectTestTask",
    "run_project_test_matrix",
]
