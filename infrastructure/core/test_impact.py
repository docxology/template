"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.test_impact``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.test_impact`` directly.
"""

from infrastructure.core.testing.test_impact import (  # noqa: F401
    TestImpactPlan,
    classify_changed_paths,
)

__all__ = [
    "TestImpactPlan",
    "classify_changed_paths",
]
