"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.public_matrix_receipt``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.public_matrix_receipt`` directly.
"""

from infrastructure.core.testing.public_matrix_receipt import (  # noqa: F401
    PublicMatrixLaneResult,
    PublicMatrixReceipt,
    build_public_matrix_cache_key,
    build_public_matrix_receipt,
    determine_worker_info,
    write_public_matrix_receipt,
)

__all__ = [
    "PublicMatrixLaneResult",
    "PublicMatrixReceipt",
    "build_public_matrix_cache_key",
    "build_public_matrix_receipt",
    "determine_worker_info",
    "write_public_matrix_receipt",
]
