"""Tests for steganography metadata module."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.steganography.config import DocumentMetadata
from infrastructure.steganography.metadata import (
    build_document_metadata,
    build_xmp_packet,
    classify_publication_metadata,
)
from tests.infra_tests.steganography.conftest import has_pypdf


class TestMetadata:
    def test_publication_metadata_classifier_allows_public_fields(self):
        result = classify_publication_metadata({"/Title": "Public paper", "/Author": "Author"})
        assert result == {
            "status": "pass",
            "keys": ["/Author", "/Title"],
            "issues": [],
        }

    def test_publication_metadata_classifier_rejects_recipient_and_secret_values(self):
        result = classify_publication_metadata(
            {
                "/RecipientID": "reviewer-1",
                "/Title": "token=must-not-leak",
            }
        )
        assert result["status"] == "fail"
        assert any("unexpected metadata key" in issue for issue in result["issues"])
        assert any("credential-like value" in issue for issue in result["issues"])

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


class TestBuildDocumentMetadata:
    def test_full_metadata(self):
        doc = DocumentMetadata(
            title="Test Paper",
            authors=["Alice", "Bob"],
            keywords=["test", "paper"],
            document_id="doc-123",
            hashes={"sha256": "abc123", "md5": "def456"},
        )
        meta = build_document_metadata(doc)
        assert meta["/Title"] == "Test Paper"
        assert "Alice" in meta["/Author"]
        assert "Bob" in meta["/Author"]
        assert "test" in meta["/Keywords"]
        assert meta["/DocumentID"] == "doc-123"
        assert meta["/Hash_SHA256"] == "abc123"
        assert meta["/Hash_MD5"] == "def456"

    def test_minimal_metadata(self):
        doc = DocumentMetadata()
        meta = build_document_metadata(doc)
        assert "/Creator" in meta
        assert "/Producer" in meta
        assert "/SteganographyTimestamp" in meta
        assert "/Title" not in meta
        assert "/Author" not in meta

    def test_extra_fields(self):
        doc = DocumentMetadata(
            title="T",
            extra={"CustomField": "value1", "/SlashField": "value2"},
        )
        meta = build_document_metadata(doc)
        assert meta["/CustomField"] == "value1"
        assert meta["/SlashField"] == "value2"

    def test_subject_includes_document_id(self):
        doc = DocumentMetadata(document_id="id-999")
        meta = build_document_metadata(doc)
        assert "id-999" in meta["/Subject"]


class TestBuildXmpPacket:
    def test_full_xmp(self):
        doc = DocumentMetadata(
            title="XMP Test",
            authors=["Author1", "Author2"],
            keywords=["kw1", "kw2"],
            document_id="xmp-id",
            hashes={"sha256": "hash123"},
        )
        xmp = build_xmp_packet(doc)
        assert "<?xpacket" in xmp
        assert "XMP Test" in xmp
        assert "Author1" in xmp
        assert "Author2" in xmp
        assert "kw1" in xmp
        assert "kw2" in xmp
        assert "xmp-id" in xmp
        assert "hash123" in xmp
        assert "steg:hash_sha256" in xmp

    def test_minimal_xmp(self):
        doc = DocumentMetadata(title="Minimal", document_id="min-id")
        xmp = build_xmp_packet(doc)
        assert "<?xpacket" in xmp
        assert "Minimal" in xmp
        assert "dc:creator" not in xmp  # No authors
        assert "dc:subject" not in xmp  # No keywords

    def test_xmp_with_authors_no_keywords(self):
        doc = DocumentMetadata(title="T", authors=["Alice"], document_id="id")
        xmp = build_xmp_packet(doc)
        assert "dc:creator" in xmp
        assert "Alice" in xmp
        assert "dc:subject" not in xmp

    def test_xmp_with_keywords_no_authors(self):
        doc = DocumentMetadata(title="T", keywords=["k1"], document_id="id")
        xmp = build_xmp_packet(doc)
        assert "dc:subject" in xmp
        assert "k1" in xmp
        assert "dc:creator" not in xmp


class TestInjectPdfMetadata:
    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_inject_basic(self, tmp_path):
        from infrastructure.steganography.metadata import inject_pdf_metadata

        # Create a minimal PDF using pypdf
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_path = tmp_path / "input.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        output = tmp_path / "output.pdf"
        result = inject_pdf_metadata(pdf_path, output, {"/Title": "Injected", "/Author": "Test"})
        assert result == output
        assert output.exists()

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_inject_with_xmp(self, tmp_path):
        from infrastructure.steganography.metadata import inject_pdf_metadata

        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_path = tmp_path / "input.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        output = tmp_path / "output_xmp.pdf"
        xmp = '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta/><?xpacket end="w"?>'
        result = inject_pdf_metadata(pdf_path, output, {"/Title": "T"}, xmp_string=xmp)
        assert result == output
        assert output.exists()

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_inject_with_attachments(self, tmp_path):
        from infrastructure.steganography.metadata import inject_pdf_metadata

        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_path = tmp_path / "input.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        output = tmp_path / "output_att.pdf"
        result = inject_pdf_metadata(
            pdf_path,
            output,
            {"/Title": "T"},
            attachments={"manifest.json": b'{"hash": "abc123"}'},
        )
        assert result == output
        assert output.exists()
