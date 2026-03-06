"""Steganography configuration.

Defines SteganographyConfig — a dataclass controlling which steganographic
techniques are applied when producing the secure PDF variant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SteganographyConfig:
    """Configuration for steganographic PDF post-processing.

    Attributes:
        enabled: Master switch — when False no processing occurs.
        overlays_enabled: Diagonal watermark text overlays.
        barcodes_enabled: QR / Code128 / DataMatrix barcode strips.
        metadata_enabled: XMP and PDF Info dictionary injection.
        hashing_enabled: Hash computation and embedding.
        encryption_enabled: AES-256 payload encryption and PDF password.
        overlay_text: Watermark text rendered diagonally across pages.
        overlay_opacity: Opacity of the watermark overlay (0.0–1.0).
        overlay_color_rgb: RGB tuple for overlay text colour.
        barcode_content: Data to encode in barcodes (None → auto from title + hash).
        hash_algorithms: Hash algorithms to compute.
        pdf_password: Optional password for PDF-level encryption.
        output_suffix: Suffix appended to the output filename.
        manifest_enabled: Whether to write a JSON hash manifest sidecar.
    """

    enabled: bool = False
    overlays_enabled: bool = True
    barcodes_enabled: bool = True
    metadata_enabled: bool = True
    hashing_enabled: bool = True
    encryption_enabled: bool = False

    overlay_text: str = "CONFIDENTIAL"
    overlay_opacity: float = 0.08
    overlay_color_rgb: tuple = (128, 128, 128)

    barcode_content: Optional[str] = None

    hash_algorithms: List[str] = field(default_factory=lambda: ["sha256", "sha512"])

    pdf_password: Optional[str] = None
    output_suffix: str = "_steganography"
    manifest_enabled: bool = True

    # ── Factory ───────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SteganographyConfig":
        """Build config from a raw dictionary (e.g. parsed YAML section).

        Unknown keys are silently ignored so forward-compatible config files
        work without errors.
        """
        if not data:
            return cls()

        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Normalise shorthand booleans from YAML
        bool_aliases = {
            "overlays": "overlays_enabled",
            "barcodes": "barcodes_enabled",
            "metadata": "metadata_enabled",
            "hashing": "hashing_enabled",
            "encryption": "encryption_enabled",
        }
        for alias, canon in bool_aliases.items():
            if alias in data and canon not in filtered:
                filtered[canon] = bool(data[alias])

        return cls(**filtered)

    @classmethod
    def all_enabled(cls) -> "SteganographyConfig":
        """Return a config with every technique switched on."""
        return cls(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=True,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=True,
        )
