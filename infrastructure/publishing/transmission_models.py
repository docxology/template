"""Backwards-compat shim: the module moved to ``infrastructure.transmission.transmission_models``.

Old import paths keep resolving (``RENDERING-LAYERING-1``); new code imports
from ``infrastructure.transmission.transmission_models`` directly.
"""

from infrastructure.transmission.transmission_models import (  # noqa: F401
    TransmissionContext,
)

__all__ = [
    "TransmissionContext",
]
