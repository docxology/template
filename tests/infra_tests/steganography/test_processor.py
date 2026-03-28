"""Tests for SteganographyProcessor pipeline and process_pdf convenience function."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.infra_tests.steganography.conftest import has_pypdf, has_qrcode, has_reportlab


class TestSteganographyProcessor:
    def test_process_disabled_returns_input(self, tmp_pdf: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        processor = SteganographyProcessor(SteganographyConfig(enabled=False))
        assert processor.process(tmp_pdf) == tmp_pdf

    def test_process_file_not_found(self, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        processor = SteganographyProcessor(SteganographyConfig(enabled=True))
        with pytest.raises(FileNotFoundError):
            processor.process(tmp_path / "nonexistent.pdf")

    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
    def test_process_full_pipeline(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(enabled=True, overlays_enabled=True, barcodes_enabled=has_qrcode(), metadata_enabled=True, hashing_enabled=True, encryption_enabled=False)
        output = tmp_path / "output_steganography.pdf"
        result = SteganographyProcessor(config).process(tmp_pdf, output_pdf=output, title="Test Paper", authors=["Author One"], keywords=["test"])
        assert result.exists()
        assert result.stat().st_size > 0
        assert result == output

    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
    def test_process_auto_output_name(self, tmp_pdf: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(enabled=True, overlays_enabled=False, barcodes_enabled=False, metadata_enabled=True, hashing_enabled=True, encryption_enabled=False)
        result = SteganographyProcessor(config).process(tmp_pdf, title="Auto Test")
        assert result.name == tmp_pdf.stem + "_steganography.pdf"
        assert result.exists()
        result.unlink(missing_ok=True)

    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
    def test_process_preserves_page_count(self, tmp_pdf: Path, tmp_path: Path):
        from pypdf import PdfReader
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        original_pages = len(PdfReader(str(tmp_pdf)).pages)
        config = SteganographyConfig(enabled=True, overlays_enabled=True, barcodes_enabled=False, metadata_enabled=True, hashing_enabled=True, encryption_enabled=False)
        output = tmp_path / "page_count_test.pdf"
        result = SteganographyProcessor(config).process(tmp_pdf, output_pdf=output)
        assert len(PdfReader(str(result)).pages) == original_pages

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_process_hashing_manifest_created(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(enabled=True, overlays_enabled=False, barcodes_enabled=False, metadata_enabled=True, hashing_enabled=True, encryption_enabled=False, manifest_enabled=True)
        output = tmp_path / "manifest_test.pdf"
        SteganographyProcessor(config).process(tmp_pdf, output_pdf=output, title="Manifest Test")
        manifest = tmp_pdf.with_suffix(".hashes.json")
        assert manifest.exists()
        assert "sha256" in json.loads(manifest.read_text())["hashes"]


class TestProcessPdfConvenience:
    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
    def test_process_pdf(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import process_pdf

        config = SteganographyConfig(enabled=True, overlays_enabled=False, barcodes_enabled=False, metadata_enabled=True, hashing_enabled=True, encryption_enabled=False)
        output = tmp_path / "convenience_test.pdf"
        assert process_pdf(tmp_pdf, output_pdf=output, config=config).exists()
