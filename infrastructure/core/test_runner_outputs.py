"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.test_runner_outputs``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.test_runner_outputs`` directly.
"""

from infrastructure.core.testing.test_runner_outputs import (  # noqa: F401
    declared_output_relpaths,
    output_tree_digest,
)

__all__ = [
    "declared_output_relpaths",
    "output_tree_digest",
]
