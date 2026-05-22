"""Tests for steganography barcodes module."""

from __future__ import annotations


class TestBarcodes:
    def test_generate_qr_code(self):
        from infrastructure.steganography.barcodes import generate_qr_code

        png_bytes = generate_qr_code("test payload data")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 100

    def test_build_barcode_payload(self):
        from infrastructure.steganography.barcodes import build_barcode_payload

        payload = build_barcode_payload(title="Test Paper", hashes={"sha256": "a" * 64}, document_id="doc123")
        assert "T:Test Paper" in payload
        assert "ID:doc123" in payload
        assert "SHA256" in payload.upper()

    def test_build_barcode_payload_minimal(self):
        from infrastructure.steganography.barcodes import build_barcode_payload

        payload = build_barcode_payload()
        assert "T:" in payload
        assert "TS:" in payload

    def test_create_barcode_strip_overlay(self):
        from infrastructure.steganography.barcodes import create_barcode_strip_overlay

        pdf_bytes = create_barcode_strip_overlay(612, 792, qr_data="test qr data", code128_data="ID:test|P:1")
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
