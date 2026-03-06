"""Steganography module — Optional secure PDF post-processing.

This module provides configurable steganographic PDF augmentation that
produces a second ``*_steganography.pdf`` alongside the normal PDF output.

Techniques include:
- Diagonal watermark text overlays
- QR code and Code128 barcode strips
- PDF metadata and XMP injection
- Cryptographic hash embedding
- AES-256 encrypted payloads
- Optional PDF password protection

The module is fully optional — all dependencies are lazily imported and
the module does nothing unless explicitly enabled in ``config.yaml``.

Usage::

    from infrastructure.steganography import process_pdf, SteganographyConfig
    from pathlib import Path

    # Quick — all techniques enabled
    process_pdf(Path("paper.pdf"))

    # Configurable
    config = SteganographyConfig(enabled=True, encryption_enabled=False)
    process_pdf(Path("paper.pdf"), config=config, title="My Paper")
"""

from infrastructure.steganography.config import SteganographyConfig
from infrastructure.steganography.core import SteganographyProcessor, process_pdf

__all__ = [
    "SteganographyConfig",
    "SteganographyProcessor",
    "process_pdf",
]
