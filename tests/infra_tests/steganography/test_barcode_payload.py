"""Tests for infrastructure.steganography.barcode_payload module.

Tests barcode payload building and QR text generation functions.
"""

from __future__ import annotations

from datetime import datetime

from infrastructure.steganography.barcode_payload import (
    build_barcode_payload,
    build_citation_qr_text,
    build_integrity_qr_text,
    build_mailto_qr_text,
    build_metadata_qr_text,
)


class TestBuildBarcodePayload:
    """Tests for build_barcode_payload."""

    def test_basic_payload(self):
        payload = build_barcode_payload(title="Test Paper")
        assert "T:Test Paper" in payload
        assert "TS:" in payload

    def test_title_truncated_to_60(self):
        long_title = "A" * 100
        payload = build_barcode_payload(title=long_title)
        # Title should be truncated to 60 chars
        assert f"T:{'A' * 60}" in payload
        assert f"T:{'A' * 61}" not in payload

    def test_with_document_id(self):
        payload = build_barcode_payload(title="Test", document_id="DOC-123")
        assert "ID:DOC-123" in payload

    def test_with_hashes(self):
        hashes = {"sha256": "abcdef1234567890abcdef1234567890"}
        payload = build_barcode_payload(title="Test", hashes=hashes)
        # Hash algo truncated to 6, digest to 16
        assert "SHA256:abcdef1234567890" in payload

    def test_hash_digest_truncated_to_16(self):
        hashes = {"sha256": "a" * 64}
        payload = build_barcode_payload(hashes=hashes)
        assert f"SHA256:{'a' * 16}" in payload

    def test_hash_algo_truncated_to_6(self):
        hashes = {"longalgoname": "abc123"}
        payload = build_barcode_payload(hashes=hashes)
        assert "LONGAL:abc123" in payload

    def test_with_extra_fields(self):
        extra = {"version": "1.0", "license": "MIT"}
        payload = build_barcode_payload(title="Test", extra=extra)
        assert "version:1.0" in payload
        assert "license:MIT" in payload

    def test_pipe_delimited(self):
        payload = build_barcode_payload(title="Test", document_id="DOC-1")
        parts = payload.split("|")
        assert len(parts) >= 3  # title, timestamp, doc_id

    def test_timestamp_format(self):
        payload = build_barcode_payload()
        # Should contain UTC timestamp in compact format
        parts = payload.split("|")
        ts_part = [p for p in parts if p.startswith("TS:")]
        assert len(ts_part) == 1
        # Format: YYYYMMDDTHHMMSSZ
        ts = ts_part[0].replace("TS:", "")
        assert ts.endswith("Z")
        assert "T" in ts

    def test_empty_defaults(self):
        payload = build_barcode_payload()
        assert "T:" in payload
        assert "TS:" in payload


class TestBuildMetadataQrText:
    """Tests for build_metadata_qr_text."""

    def test_basic_metadata(self):
        text = build_metadata_qr_text(title="My Paper", document_id="DOC-1")
        assert "My Paper" in text
        assert "DOC-1" in text

    def test_title_truncated(self):
        text = build_metadata_qr_text(title="A" * 100)
        # Title truncated to 40
        assert len([p for p in text.split(" | ") if "A" in p][0]) <= 40

    def test_document_id_truncated(self):
        text = build_metadata_qr_text(document_id="X" * 50)
        # Doc ID truncated to 16
        assert "X" * 17 not in text

    def test_includes_date(self):
        text = build_metadata_qr_text()
        year = datetime.now().strftime("%Y")
        assert year in text

    def test_empty_inputs(self):
        text = build_metadata_qr_text()
        # Should at least have date
        assert len(text) > 0

    def test_uses_hyphen_not_colon_for_doc_id(self):
        text = build_metadata_qr_text(document_id="ABC")
        assert "Doc-ID" in text


class TestBuildCitationQrText:
    """Tests for build_citation_qr_text."""

    def test_basic_citation(self):
        text = build_citation_qr_text(title="Test Paper", authors=["Smith, J."])
        assert "Smith, J." in text
        year = datetime.now().strftime("%Y")
        assert year in text
        assert "Test Paper" in text

    def test_no_authors_fallback(self):
        text = build_citation_qr_text(title="Paper")
        assert "Unknown" in text

    def test_output_max_100_chars(self):
        text = build_citation_qr_text(
            title="A Very Long Title That Goes On And On And On For Testing Purposes",
            authors=["A Very Long Author Name Indeed"],
        )
        assert len(text) <= 100

    def test_title_truncated_to_50(self):
        text = build_citation_qr_text(title="B" * 100, authors=["X"])
        # Title portion should be truncated
        assert "B" * 51 not in text


class TestBuildMailtoQrText:
    """Tests for build_mailto_qr_text."""

    def test_with_email(self):
        text = build_mailto_qr_text(
            title="Paper",
            authors=["Smith"],
            author_emails=["smith@example.com"],
        )
        assert text.startswith("mailto:smith@example.com")
        assert "subject=" in text

    def test_url_encoded_subject(self):
        text = build_mailto_qr_text(
            title="My Paper Title",
            author_emails=["a@b.com"],
        )
        assert "mailto:a@b.com" in text
        # Subject should be URL-encoded
        assert "subject=" in text

    def test_no_email_fallback(self):
        text = build_mailto_qr_text(authors=["Smith"])
        assert "Contact Smith" in text

    def test_no_email_no_author(self):
        text = build_mailto_qr_text()
        assert "Contact" in text
        assert "Author" in text

    def test_none_emails_list(self):
        text = build_mailto_qr_text(author_emails=None, authors=["Doe"])
        assert "Contact Doe" in text

    def test_empty_emails_list(self):
        text = build_mailto_qr_text(author_emails=[], authors=["Doe"])
        assert "Contact Doe" in text


class TestBuildIntegrityQrText:
    """Tests for build_integrity_qr_text."""

    def test_with_sha256(self):
        hashes = {"sha256": "abcdef1234567890abcdef1234567890"}
        text = build_integrity_qr_text(hashes=hashes)
        assert "SHA-256" in text
        assert "abcdef1234567890abcdef12" in text  # 24 chars

    def test_with_document_id(self):
        text = build_integrity_qr_text(document_id="DOC-123")
        assert "ID DOC-123" in text

    def test_both_hash_and_id(self):
        hashes = {"sha256": "abc123"}
        text = build_integrity_qr_text(document_id="DOC-1", hashes=hashes)
        assert "SHA-256" in text
        assert "ID DOC-1" in text
        assert " | " in text

    def test_no_sha256_in_hashes(self):
        hashes = {"md5": "abc123"}
        text = build_integrity_qr_text(hashes=hashes)
        assert "SHA-256" not in text

    def test_empty_inputs(self):
        text = build_integrity_qr_text()
        assert text == ""

    def test_document_id_truncated(self):
        text = build_integrity_qr_text(document_id="X" * 50)
        assert "X" * 13 not in text  # truncated to 12
