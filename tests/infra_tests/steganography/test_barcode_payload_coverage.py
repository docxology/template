"""Tests for infrastructure.steganography.barcode_payload — comprehensive coverage."""

from infrastructure.steganography.barcode_payload import (
    build_barcode_payload,
    build_metadata_qr_text,
    build_citation_qr_text,
    build_mailto_qr_text,
    build_integrity_qr_text,
)


class TestBuildBarcodePayload:
    def test_basic(self):
        result = build_barcode_payload(title="My Paper")
        assert "T:My Paper" in result
        assert "TS:" in result

    def test_with_document_id(self):
        result = build_barcode_payload(title="Paper", document_id="doc-123")
        assert "ID:doc-123" in result

    def test_with_hashes(self):
        result = build_barcode_payload(
            title="Paper",
            hashes={"sha256": "abcdef1234567890abcdef1234567890"},
        )
        assert "SHA256:" in result
        # Only first 16 chars of digest
        assert "abcdef1234567890" in result

    def test_with_extra(self):
        result = build_barcode_payload(
            title="Paper",
            extra={"version": "1.0", "format": "pdf"},
        )
        assert "version:1.0" in result
        assert "format:pdf" in result

    def test_title_truncation(self):
        long_title = "A" * 100
        result = build_barcode_payload(title=long_title)
        # Title truncated to 60 chars
        assert f"T:{'A' * 60}" in result

    def test_empty(self):
        result = build_barcode_payload()
        assert "T:" in result
        assert "TS:" in result

    def test_pipe_delimited(self):
        result = build_barcode_payload(title="Test", document_id="123")
        assert "|" in result


class TestBuildMetadataQrText:
    def test_basic(self):
        result = build_metadata_qr_text(title="My Paper", document_id="doc-1")
        assert "My Paper" in result
        assert "Doc-ID" in result

    def test_no_title(self):
        result = build_metadata_qr_text(document_id="doc-1")
        assert "Doc-ID" in result

    def test_no_document_id(self):
        result = build_metadata_qr_text(title="Paper")
        assert "Paper" in result
        assert "Doc-ID" not in result

    def test_title_truncation(self):
        result = build_metadata_qr_text(title="A" * 100)
        # Title truncated to 40 chars
        assert len(result.split(" | ")[0]) <= 40

    def test_contains_date(self):
        result = build_metadata_qr_text(title="Test")
        # Should contain a date like 2026-04-02
        assert "-" in result


class TestBuildCitationQrText:
    def test_with_authors(self):
        result = build_citation_qr_text(title="My Paper", authors=["Smith", "Jones"])
        assert "Smith" in result
        assert "My Paper" in result

    def test_no_authors(self):
        result = build_citation_qr_text(title="Paper")
        assert "Unknown" in result

    def test_length_limit(self):
        result = build_citation_qr_text(title="A" * 200, authors=["Author"])
        assert len(result) <= 100


class TestBuildMailtoQrText:
    def test_with_email(self):
        result = build_mailto_qr_text(
            title="Paper",
            authors=["Smith"],
            author_emails=["smith@example.com"],
        )
        assert result.startswith("mailto:smith@example.com")
        assert "subject=" in result

    def test_no_email(self):
        result = build_mailto_qr_text(title="Paper", authors=["Smith"])
        assert "Contact Smith" in result

    def test_no_email_no_authors(self):
        result = build_mailto_qr_text(title="Paper")
        assert "Contact Author" in result

    def test_empty_email_list(self):
        result = build_mailto_qr_text(title="Paper", author_emails=[])
        # Empty list is falsy
        assert "Contact" in result


class TestBuildIntegrityQrText:
    def test_with_hash(self):
        result = build_integrity_qr_text(
            document_id="doc-1",
            hashes={"sha256": "abcdef1234567890abcdef1234567890"},
        )
        assert "SHA-256" in result
        assert "ID doc-1" in result

    def test_no_hash(self):
        result = build_integrity_qr_text(document_id="doc-1")
        assert "ID doc-1" in result
        assert "SHA" not in result

    def test_no_data(self):
        result = build_integrity_qr_text()
        assert result == ""

    def test_wrong_hash_algo(self):
        result = build_integrity_qr_text(hashes={"md5": "abc123"})
        # md5 not sha256, so no SHA-256 entry
        assert "SHA-256" not in result
