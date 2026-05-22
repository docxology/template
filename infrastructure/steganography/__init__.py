"""Steganography module — Optional secure PDF post-processing.

This module provides configurable steganographic PDF augmentation that
produces a second ``*_steganography.pdf`` alongside the normal PDF output.

Techniques include:
- Diagonal watermark text overlays
- QR code and Code128 barcode strips
- PDF metadata and XMP injection
- Cryptographic hash embedding
- AES-GCM encrypted payload helpers
- Optional PDF password protection

The module is fully optional — all dependencies are lazily imported and
the module does nothing unless explicitly enabled through secure-run
defaults, project config, or API configuration.

Usage::

    from infrastructure.steganography import embed_steganography, SteganographyConfig
    from pathlib import Path

    # Quick — all techniques enabled
    embed_steganography(Path("paper.pdf"))

    # Configurable
    config = SteganographyConfig(enabled=True, encryption_enabled=False)
    embed_steganography(Path("paper.pdf"), config=config, title="My Paper")
"""

from infrastructure.steganography.config import (
    SteganographyConfig,
    resolve_build_timestamp,
)
from infrastructure.steganography.core import (
    SteganographyProcessor,
    embed_steganography,
    process_pdf,
)

__all__ = [
    "SteganographyConfig",
    "SteganographyProcessor",
    "embed_steganography",
    "process_pdf",
    "resolve_build_timestamp",
]
