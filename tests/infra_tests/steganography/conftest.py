"""Shared fixtures for steganography tests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest


@pytest.fixture
def tmp_pdf(tmp_path: Path) -> Path:
    """Create a minimal valid PDF file for testing.

    Uses reportlab to generate a real single-page PDF rather than a stub.
    Falls back to a raw PDF bytestream if reportlab is not available.
    """
    pdf_path = tmp_path / "test_document.pdf"

    try:
        from reportlab.pdfgen import canvas as rl_canvas  # type: ignore

        c = rl_canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 12)
        c.drawString(72, 700, "Test document for steganography module testing.")
        c.drawString(72, 680, "This is page 1.")
        c.showPage()
        c.drawString(72, 700, "This is page 2.")
        c.showPage()
        c.save()
    except ImportError:
        # Fallback: write a minimal valid PDF manually
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000114 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\n"
            b"startxref\n183\n%%EOF"
        )
        pdf_path.write_bytes(pdf_bytes)

    return pdf_path


@pytest.fixture
def steg_config():
    """Return a SteganographyConfig with all techniques enabled."""
    from infrastructure.steganography.config import SteganographyConfig

    return SteganographyConfig.all_enabled()


@pytest.fixture
def steg_config_minimal():
    """Return a minimal config with only metadata enabled."""
    from infrastructure.steganography.config import SteganographyConfig

    return SteganographyConfig(
        enabled=True,
        overlays_enabled=False,
        barcodes_enabled=False,
        metadata_enabled=True,
        hashing_enabled=True,
        encryption_enabled=False,
    )
