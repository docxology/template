"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.test_runner``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.test_runner`` directly.
"""

from infrastructure.core.testing.test_runner import (  # noqa: F401
    DEFAULT_COVERAGE_FILE,
    DEFAULT_FAIL_UNDER,
    DEFAULT_MARKER_EXPR,
    DEFAULT_PROJECT_FAIL_UNDER,
    DEFAULT_SKIP_PROJECTS,
    DEFAULT_SUBPROCESS_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT,
    _contains_tests,
    _output_tree_digest,
    discover_skip_combined_pytest_projects,
    run_per_project_pytest,
)

__all__ = [
    "DEFAULT_COVERAGE_FILE",
    "DEFAULT_FAIL_UNDER",
    "DEFAULT_MARKER_EXPR",
    "DEFAULT_PROJECT_FAIL_UNDER",
    "DEFAULT_SKIP_PROJECTS",
    "DEFAULT_SUBPROCESS_TIMEOUT_SECONDS",
    "DEFAULT_TIMEOUT",
    "_contains_tests",
    "_output_tree_digest",
    "discover_skip_combined_pytest_projects",
    "run_per_project_pytest",
]
