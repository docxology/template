"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.test_runner_cache``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.test_runner_cache`` directly.
"""

from infrastructure.core.testing.test_runner_cache import (  # noqa: F401
    _cache_identity_inputs,
    _resolve_roster_revision,
)

__all__ = [
    "_cache_identity_inputs",
    "_resolve_roster_revision",
]
