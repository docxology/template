"""Backwards-compat shim: the module moved to ``infrastructure.transmission.transmission_figure``.

Old import paths keep resolving (``RENDERING-LAYERING-1``); new code imports
from ``infrastructure.transmission.transmission_figure`` directly.
"""

from infrastructure.transmission.transmission_figure import (  # noqa: F401
    write_transmission_diagram,
)

__all__ = [
    "write_transmission_diagram",
]
