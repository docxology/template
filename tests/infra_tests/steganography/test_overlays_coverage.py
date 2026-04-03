"""Tests for infrastructure.steganography.overlays — additional coverage."""

import pytest

from tests.infra_tests.steganography.conftest import has_reportlab

from infrastructure.steganography.overlays import FooterConfig


class TestFooterConfig:
    def test_defaults(self):
        cfg = FooterConfig()
        assert cfg.document_id == ""
        assert cfg.page_number == 1
        assert cfg.total_pages == 1
        assert cfg.hash_short == ""
        assert cfg.title == ""
        assert cfg.authors == ""
        assert cfg.source_filename == ""
        assert cfg.source_file_size == 0
        assert cfg.font_size == 5

    def test_custom_values(self):
        cfg = FooterConfig(
            document_id="abc123",
            page_number=3,
            total_pages=10,
            hash_short="deadbeef",
            title="My Paper",
            authors="Alice, Bob",
            source_filename="paper.pdf",
            source_file_size=1024 * 1024,
            font_size=6,
        )
        assert cfg.title == "My Paper"
        assert cfg.source_file_size == 1024 * 1024


@pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
class TestCreateWatermarkOverlay:
    def test_basic(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_custom_text(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792, text="DRAFT")
        assert len(pdf_bytes) > 0

    def test_custom_opacity_and_color(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(
            612, 792, opacity=0.15, color_rgb=(255, 0, 0), font_size=80
        )
        assert len(pdf_bytes) > 0

    def test_single_repeat(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792, repeat_count=1)
        assert len(pdf_bytes) > 0

    def test_many_repeats(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792, repeat_count=10)
        assert len(pdf_bytes) > 0

    def test_small_page(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(100, 100)
        assert len(pdf_bytes) > 0


@pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
class TestCreateFooterOverlay:
    def test_with_config(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        cfg = FooterConfig(
            document_id="test123",
            page_number=2,
            total_pages=5,
            hash_short="abcdef12",
            title="Test Paper Title",
            authors="Alice, Bob",
            source_filename="paper.pdf",
            source_file_size=512 * 1024,
        )
        pdf_bytes = create_footer_overlay(612, 792, cfg)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_with_kwargs(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612,
            792,
            document_id="kw_test",
            page_number=1,
            total_pages=3,
            hash_short="hash",
            title="KW Paper",
            authors="Charlie",
        )
        assert len(pdf_bytes) > 0

    def test_long_title_truncated(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612, 792, title="A" * 100, authors="Test"
        )
        assert len(pdf_bytes) > 0

    def test_large_file_size_mb(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612, 792, source_file_size=5 * 1024 * 1024  # 5 MB
        )
        assert len(pdf_bytes) > 0

    def test_small_file_size_kb(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612, 792, source_file_size=500  # 500 bytes
        )
        assert len(pdf_bytes) > 0

    def test_long_document_id(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612, 792, document_id="a" * 50
        )
        assert len(pdf_bytes) > 0

    def test_long_source_filename(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(
            612, 792, source_filename="very_long_filename_that_exceeds_twenty_chars.pdf"
        )
        assert len(pdf_bytes) > 0

    def test_no_optional_fields(self):
        from infrastructure.steganography.overlays import create_footer_overlay

        pdf_bytes = create_footer_overlay(612, 792)
        assert len(pdf_bytes) > 0


@pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
class TestCreateInvisibleTextOverlay:
    def test_basic(self):
        from infrastructure.steganography.overlays import create_invisible_text_overlay

        pdf_bytes = create_invisible_text_overlay(612, 792, "hidden data")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_long_hidden_text(self):
        from infrastructure.steganography.overlays import create_invisible_text_overlay

        pdf_bytes = create_invisible_text_overlay(612, 792, "x" * 10000)
        assert len(pdf_bytes) > 0

    def test_unicode_hidden_text(self):
        from infrastructure.steganography.overlays import create_invisible_text_overlay

        pdf_bytes = create_invisible_text_overlay(612, 792, "metadata: test-id-123")
        assert len(pdf_bytes) > 0
