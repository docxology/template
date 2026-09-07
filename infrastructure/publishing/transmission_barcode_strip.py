"""Backwards-compat shim: the module moved to ``infrastructure.transmission.transmission_barcode_strip``.

Old import paths keep resolving (``RENDERING-LAYERING-1``); new code imports
from ``infrastructure.transmission.transmission_barcode_strip`` directly.
"""

from infrastructure.transmission.transmission_barcode_strip import (  # noqa: F401
    TransmissionContext,
    build_transmission_manifest_payload,
    compact_manifest_json,
    write_transmission_barcode_strip,
    write_transmission_manifest,
)

__all__ = [
    "TransmissionContext",
    "build_transmission_manifest_payload",
    "compact_manifest_json",
    "write_transmission_barcode_strip",
    "write_transmission_manifest",
]
