"""Backwards-compat shim: the module moved to ``infrastructure.transmission.transmission_page_check``.

Old import paths keep resolving (``RENDERING-LAYERING-1``); new code imports
from ``infrastructure.transmission.transmission_page_check`` directly.
"""

from infrastructure.transmission.transmission_page_check import (  # noqa: F401
    TransmissionPageCheckResult,
    check_transmission_bookend_pages,
    main,
    validate_transmission_bookend_pages,
)

__all__ = [
    "TransmissionPageCheckResult",
    "check_transmission_bookend_pages",
    "main",
    "validate_transmission_bookend_pages",
]
