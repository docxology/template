"""Backwards-compat shim: the module moved to ``infrastructure.transmission.transmission_bookends``.

Old import paths keep resolving (``RENDERING-LAYERING-1``); new code imports
from ``infrastructure.transmission.transmission_bookends`` directly.
"""

from infrastructure.transmission.transmission_bookends import (  # noqa: F401
    TransmissionBookendSettings,
    TransmissionContext,
    build_transmission_context,
    compact_manifest_json,
    is_transmission_bookend,
    render_transmission_markdown,
    transmission_bookends_enabled,
    write_transmission_barcode_strip,
    write_transmission_bookends,
    write_transmission_diagram,
    write_transmission_manifest,
)

__all__ = [
    "TransmissionBookendSettings",
    "TransmissionContext",
    "build_transmission_context",
    "compact_manifest_json",
    "is_transmission_bookend",
    "render_transmission_markdown",
    "transmission_bookends_enabled",
    "write_transmission_barcode_strip",
    "write_transmission_bookends",
    "write_transmission_diagram",
    "write_transmission_manifest",
]
