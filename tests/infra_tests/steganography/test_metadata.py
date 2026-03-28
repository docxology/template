"""Tests for steganography metadata module."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.infra_tests.steganography.conftest import has_pypdf


class TestMetadata:
    def test_build_document_metadata(self):
        from infrastructure.steganography.config import DocumentMetadata
        from infrastructure.steganography.metadata import build_document_metadata

        doc = DocumentMetadata(title="Test Paper", authors=["Author One", "Author Two"], hashes={"sha256": "abcd" * 16}, document_id="doc-123", keywords=["test", "steganography"])
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

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_inject_pdf_metadata(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.metadata import inject_pdf_metadata

        output = tmp_path / "output_meta.pdf"
        inject_pdf_metadata(tmp_pdf, output, {"/Title": "Injected Title", "/CustomKey": "CustomValue"})
        assert output.exists()
        assert output.stat().st_size > 0

    def test_build_xmp_packet(self):
        from infrastructure.steganography.config import DocumentMetadata
        from infrastructure.steganography.metadata import build_xmp_packet

        doc = DocumentMetadata(title="Test", authors=["Author"], hashes={"sha256": "abc123"}, document_id="id-456")
        xmp = build_xmp_packet(doc)
        assert "<?xpacket" in xmp
        assert "Test" in xmp
        assert "Author" in xmp
        assert "abc123" in xmp
