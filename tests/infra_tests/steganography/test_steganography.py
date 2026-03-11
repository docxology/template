"""Comprehensive tests for the steganography module.

Tests cover:
- Configuration loading and defaults
- Hash computation and manifest writing
- Overlay generation (watermark, footer, invisible text)
- Barcode generation (QR code, payload builder, barcode strip)
- PDF metadata injection
- Encryption utilities (HMAC fingerprint, document ID)
- Full SteganographyProcessor pipeline
- Disabled-feature passthrough
- XMP packet generation
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# Dependency Helpers (must be before decorators that use them)
# ═══════════════════════════════════════════════════════════════════════════


def _has_reportlab() -> bool:
    try:
        import reportlab  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def _has_pypdf() -> bool:
    try:
        import pypdf  # noqa: F401
        return True
    except ImportError:
        return False


def _has_qrcode() -> bool:
    try:
        import qrcode  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Configuration Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSteganographyConfig:
    """Tests for SteganographyConfig dataclass."""

    def test_default_config_disabled(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert config.enabled is False
        assert config.overlays_enabled is True
        assert config.barcodes_enabled is True
        assert config.metadata_enabled is True
        assert config.hashing_enabled is True
        assert config.encryption_enabled is False

    def test_all_enabled(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.all_enabled()
        assert config.enabled is True
        assert config.overlays_enabled is True
        assert config.encryption_enabled is True

    def test_from_dict_basic(self):
        from infrastructure.steganography.config import SteganographyConfig

        data = {"enabled": True, "overlays": False, "barcodes": True}
        config = SteganographyConfig.from_dict(data)
        assert config.enabled is True
        assert config.overlays_enabled is False
        assert config.barcodes_enabled is True

    def test_from_dict_empty(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.from_dict({})
        assert config.enabled is False  # default

    def test_from_dict_none(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.from_dict(None)
        assert config.enabled is False

    def test_from_dict_unknown_keys_ignored(self):
        from infrastructure.steganography.config import SteganographyConfig

        data = {"enabled": True, "unknown_key": "value", "another": 42}
        config = SteganographyConfig.from_dict(data)
        assert config.enabled is True

    def test_from_dict_canonical_names(self):
        from infrastructure.steganography.config import SteganographyConfig

        data = {"enabled": True, "overlays_enabled": False, "encryption_enabled": True}
        config = SteganographyConfig.from_dict(data)
        assert config.overlays_enabled is False
        assert config.encryption_enabled is True

    def test_default_hash_algorithms(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert "sha256" in config.hash_algorithms
        assert "sha512" in config.hash_algorithms

    def test_overlay_defaults(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert config.overlay_text == "CONFIDENTIAL"
        assert 0.0 < config.overlay_opacity < 1.0
        assert config.output_suffix == "_steganography"


# ═══════════════════════════════════════════════════════════════════════════
# Hashing Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestHashing:
    """Tests for hash computation and manifest writing."""

    def test_compute_file_hashes(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import compute_file_hashes

        hashes = compute_file_hashes(tmp_pdf)
        assert "sha256" in hashes
        assert "sha512" in hashes
        assert len(hashes["sha256"]) == 64  # SHA-256 hex digest length
        assert len(hashes["sha512"]) == 128  # SHA-512 hex digest length

    def test_compute_file_hashes_custom_algos(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import compute_file_hashes

        hashes = compute_file_hashes(tmp_pdf, algorithms=["md5", "sha256"])
        assert "md5" in hashes
        assert "sha256" in hashes

    def test_compute_file_hashes_unsupported_algo(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import compute_file_hashes

        hashes = compute_file_hashes(tmp_pdf, algorithms=["sha256", "nonexistent_algo"])
        assert "sha256" in hashes
        assert "nonexistent_algo" not in hashes

    def test_hash_determinism(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import compute_file_hashes

        h1 = compute_file_hashes(tmp_pdf)
        h2 = compute_file_hashes(tmp_pdf)
        assert h1 == h2

    def test_write_hash_manifest(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.hashing import write_hash_manifest

        hashes = {"sha256": "abcd" * 16, "sha512": "ef01" * 32}
        manifest_path = write_hash_manifest(tmp_pdf, hashes)

        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["source_file"] == tmp_pdf.name
        assert data["hashes"]["sha256"] == "abcd" * 16
        assert "timestamp" in data

    def test_write_hash_manifest_with_extra(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import write_hash_manifest

        hashes = {"sha256": "a" * 64}
        manifest_path = write_hash_manifest(
            tmp_pdf, hashes, extra={"document_id": "test123"}
        )
        data = json.loads(manifest_path.read_text())
        assert data["document_id"] == "test123"

    def test_compute_content_hash(self):
        from infrastructure.steganography.hashing import compute_content_hash

        h = compute_content_hash(b"hello world")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256


# ═══════════════════════════════════════════════════════════════════════════
# Overlay Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOverlays:
    """Tests for overlay generation."""

    @pytest.mark.skipif(
        not _has_reportlab(), reason="reportlab not installed"
    )
    def test_create_watermark_overlay(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(612, 792, text="SECRET")
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(
        not _has_reportlab(), reason="reportlab not installed"
    )
    def test_create_footer_overlay(self):
        from infrastructure.steganography.overlays import create_footer_overlay, FooterConfig

        cfg = FooterConfig(
            document_id="abc123",
            page_number=1,
            total_pages=5,
            hash_short="deadbeef",
        )
        pdf_bytes = create_footer_overlay(612, 792, cfg)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(
        not _has_reportlab(), reason="reportlab not installed"
    )
    def test_create_invisible_text_overlay(self):
        from infrastructure.steganography.overlays import create_invisible_text_overlay

        pdf_bytes = create_invisible_text_overlay(612, 792, "hidden metadata")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.skipif(
        not _has_reportlab(), reason="reportlab not installed"
    )
    def test_watermark_custom_params(self):
        from infrastructure.steganography.overlays import create_watermark_overlay

        pdf_bytes = create_watermark_overlay(
            800, 600,
            text="DRAFT",
            opacity=0.2,
            color_rgb=(255, 0, 0),
            font_size=80,
            repeat_count=3,
        )
        assert len(pdf_bytes) > 0


# ═══════════════════════════════════════════════════════════════════════════
# Barcode Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestBarcodes:
    """Tests for barcode generation."""

    @pytest.mark.skipif(
        not _has_qrcode(), reason="qrcode not installed"
    )
    def test_generate_qr_code(self):
        from infrastructure.steganography.barcodes import generate_qr_code

        png_bytes = generate_qr_code("test payload data")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 100  # Non-trivial PNG

    def test_build_barcode_payload(self):
        from infrastructure.steganography.barcodes import build_barcode_payload

        payload = build_barcode_payload(
            title="Test Paper",
            hashes={"sha256": "a" * 64},
            document_id="doc123",
        )
        assert "T:Test Paper" in payload
        assert "ID:doc123" in payload
        assert "SHA256" in payload.upper()

    def test_build_barcode_payload_minimal(self):
        from infrastructure.steganography.barcodes import build_barcode_payload

        payload = build_barcode_payload()
        assert "T:" in payload
        assert "TS:" in payload

    @pytest.mark.skipif(
        not (_has_reportlab() and _has_qrcode()),
        reason="reportlab and/or qrcode not installed"
    )
    def test_create_barcode_strip_overlay(self):
        from infrastructure.steganography.barcodes import create_barcode_strip_overlay

        pdf_bytes = create_barcode_strip_overlay(
            612, 792, qr_data="test qr data", code128_data="ID:test|P:1"
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


# ═══════════════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMetadata:
    """Tests for PDF metadata injection."""

    def test_build_document_metadata(self):
        from infrastructure.steganography.config import DocumentMetadata
        from infrastructure.steganography.metadata import build_document_metadata

        doc = DocumentMetadata(
            title="Test Paper",
            authors=["Author One", "Author Two"],
            hashes={"sha256": "abcd" * 16},
            document_id="doc-123",
            keywords=["test", "steganography"],
        )
        meta = build_document_metadata(doc)
        assert meta["/Title"] == "Test Paper"
        assert "Author One" in meta["/Author"]
        assert "/Hash_SHA256" in meta
        assert "/DocumentID" in meta
        assert "/Keywords" in meta

    def test_build_document_metadata_minimal(self):
        from infrastructure.steganography.config import DocumentMetadata
        from infrastructure.steganography.metadata import build_document_metadata

        meta = build_document_metadata(DocumentMetadata())
        assert "/Creator" in meta
        assert "/SteganographyTimestamp" in meta

    @pytest.mark.skipif(
        not _has_pypdf(), reason="pypdf not installed"
    )
    def test_inject_pdf_metadata(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.metadata import inject_pdf_metadata

        output = tmp_path / "output_meta.pdf"
        inject_pdf_metadata(
            tmp_pdf, output, {"/Title": "Injected Title", "/CustomKey": "CustomValue"}
        )
        assert output.exists()
        assert output.stat().st_size > 0

    def test_build_xmp_packet(self):
        from infrastructure.steganography.config import DocumentMetadata
        from infrastructure.steganography.metadata import build_xmp_packet

        doc = DocumentMetadata(
            title="Test",
            authors=["Author"],
            hashes={"sha256": "abc123"},
            document_id="id-456",
        )
        xmp = build_xmp_packet(doc)
        assert "<?xpacket" in xmp
        assert "Test" in xmp
        assert "Author" in xmp
        assert "abc123" in xmp


# ═══════════════════════════════════════════════════════════════════════════
# Encryption Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestEncryption:
    """Tests for encryption utilities."""

    def test_generate_fingerprint(self):
        from infrastructure.steganography.encryption import generate_fingerprint

        result = generate_fingerprint(b"test content")
        assert "fingerprint" in result
        assert "secret" in result
        assert len(result["fingerprint"]) == 64  # HMAC-SHA256

    def test_generate_fingerprint_deterministic(self):
        from infrastructure.steganography.encryption import generate_fingerprint

        r1 = generate_fingerprint(b"data", secret="fixed_secret")
        r2 = generate_fingerprint(b"data", secret="fixed_secret")
        assert r1["fingerprint"] == r2["fingerprint"]

    def test_generate_document_id(self):
        from infrastructure.steganography.encryption import generate_document_id

        doc_id = generate_document_id()
        assert isinstance(doc_id, str)
        assert len(doc_id) == 32  # 16 bytes → 32 hex chars

    def test_generate_document_id_unique(self):
        from infrastructure.steganography.encryption import generate_document_id

        ids = {generate_document_id() for _ in range(100)}
        assert len(ids) == 100  # All unique

    @pytest.mark.skipif(
        not _has_pypdf(), reason="pypdf not installed"
    )
    def test_apply_pdf_password(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.encryption import apply_pdf_password

        output = tmp_path / "encrypted.pdf"
        result = apply_pdf_password(tmp_pdf, output, user_password="test123")
        assert result.exists()
        assert result.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════════
# Full Pipeline Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSteganographyProcessor:
    """Tests for the full SteganographyProcessor pipeline."""

    def test_process_disabled_returns_input(self, tmp_pdf: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(enabled=False)
        processor = SteganographyProcessor(config)
        result = processor.process(tmp_pdf)
        assert result == tmp_pdf  # No processing

    def test_process_file_not_found(self, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(enabled=True)
        processor = SteganographyProcessor(config)
        with pytest.raises(FileNotFoundError):
            processor.process(tmp_path / "nonexistent.pdf")

    @pytest.mark.skipif(
        not (_has_pypdf() and _has_reportlab()),
        reason="pypdf and/or reportlab not installed",
    )
    def test_process_full_pipeline(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=_has_qrcode(),
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        processor = SteganographyProcessor(config)
        output = tmp_path / "output_steganography.pdf"
        result = processor.process(
            tmp_pdf,
            output_pdf=output,
            title="Test Paper",
            authors=["Author One"],
            keywords=["test"],
        )
        assert result.exists()
        assert result.stat().st_size > 0
        assert result == output

    @pytest.mark.skipif(
        not (_has_pypdf() and _has_reportlab()),
        reason="pypdf and/or reportlab not installed",
    )
    def test_process_auto_output_name(self, tmp_pdf: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=False,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        processor = SteganographyProcessor(config)
        result = processor.process(tmp_pdf, title="Auto Test")

        expected_name = tmp_pdf.stem + "_steganography.pdf"
        assert result.name == expected_name
        assert result.exists()

        # Cleanup
        result.unlink(missing_ok=True)

    @pytest.mark.skipif(
        not (_has_pypdf() and _has_reportlab()),
        reason="pypdf and/or reportlab not installed",
    )
    def test_process_preserves_page_count(self, tmp_pdf: Path, tmp_path: Path):
        from pypdf import PdfReader

        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        original_pages = len(PdfReader(str(tmp_pdf)).pages)

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        processor = SteganographyProcessor(config)
        output = tmp_path / "page_count_test.pdf"
        result = processor.process(tmp_pdf, output_pdf=output)

        result_pages = len(PdfReader(str(result)).pages)
        assert result_pages == original_pages

    @pytest.mark.skipif(
        not _has_pypdf(), reason="pypdf not installed"
    )
    def test_process_hashing_manifest_created(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import SteganographyProcessor

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=False,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
            manifest_enabled=True,
        )
        processor = SteganographyProcessor(config)
        output = tmp_path / "manifest_test.pdf"
        processor.process(tmp_pdf, output_pdf=output, title="Manifest Test")

        manifest = tmp_pdf.with_suffix(".hashes.json")
        assert manifest.exists()
        data = json.loads(manifest.read_text())
        assert "sha256" in data["hashes"]


# ═══════════════════════════════════════════════════════════════════════════
# Convenience Function Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestProcessPdfConvenience:
    """Tests for the top-level process_pdf convenience function."""

    @pytest.mark.skipif(
        not (_has_pypdf() and _has_reportlab()),
        reason="pypdf and/or reportlab not installed",
    )
    def test_process_pdf(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.core import process_pdf
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=False,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        output = tmp_path / "convenience_test.pdf"
        result = process_pdf(tmp_pdf, output_pdf=output, config=config)
        assert result.exists()

