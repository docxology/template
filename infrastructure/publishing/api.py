"""Backwards-compatible re-exports for Zenodo API types.

Prefer ``infrastructure.publishing.zenodo`` for new code.
"""

from infrastructure.publishing.http import REQUEST_TIMEOUT
from infrastructure.publishing.zenodo.client import ZenodoClient
from infrastructure.publishing.zenodo.config import ZenodoConfig
from infrastructure.publishing.zenodo.models import DepositionResult

__all__ = [
    "DepositionResult",
    "REQUEST_TIMEOUT",
    "ZenodoClient",
    "ZenodoConfig",
]
