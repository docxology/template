"""Tests for steganography overlays module."""

from __future__ import annotations

import pytest

from tests.infra_tests.steganography.conftest import has_reportlab


class TestOverlays:
    @pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
    def test_create_watermark_overlay(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792, text="SECRET")
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
    def test_create_footer_overlay(self):
        from infrastructure.steganography.overlays import create_footer_overlay, FooterConfig

        cfg = FooterConfig(document_id="abc123", page_number=1, total_pages=5, hash_short="deadbeef")
        pdf_bytes = create_footer_overlay(612, 792, cfg)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
    def test_create_invisible_text_overlay(self):
        from infrastructure.steganography.overlays import create_invisible_text_overlay

        pdf_bytes = create_invisible_text_overlay(612, 792, "hidden metadata")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
    def test_watermark_custom_params(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(800, 600, text="DRAFT", opacity=0.2, color_rgb=(255, 0, 0), font_size=80, repeat_count=3)
        assert len(pdf_bytes) > 0
