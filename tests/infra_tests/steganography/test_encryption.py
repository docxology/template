"""Tests for steganography encryption module."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.infra_tests.steganography.conftest import has_pypdf


class TestEncryption:
    def test_generate_fingerprint(self):
        from infrastructure.steganography.encryption import generate_fingerprint

        result = generate_fingerprint(b"test content")
        assert "fingerprint" in result
        assert "secret" in result
        assert len(result["fingerprint"]) == 64

    def test_generate_fingerprint_deterministic(self):
        from infrastructure.steganography.encryption import generate_fingerprint

        r1 = generate_fingerprint(b"data", secret="fixed_secret")
        r2 = generate_fingerprint(b"data", secret="fixed_secret")
        assert r1["fingerprint"] == r2["fingerprint"]

    def test_generate_document_id(self):
        from infrastructure.steganography.encryption import generate_document_id

        doc_id = generate_document_id()
        assert isinstance(doc_id, str)
        assert len(doc_id) == 32

    def test_generate_document_id_unique(self, monkeypatch):
        # Uniqueness only holds in the random branch. Defensively ensure
        # the deterministic-mode env flag is not set — earlier tests in
        # the suite that set it via process-level os.environ (rather than
        # monkeypatch) can otherwise pollute this one.
        monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)
        from infrastructure.steganography.encryption import generate_document_id

        ids = {generate_document_id() for _ in range(100)}
        assert len(ids) == 100

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
    def test_apply_pdf_password(self, tmp_pdf: Path, tmp_path: Path):
        from pypdf import PdfReader

        from infrastructure.steganography.encryption import apply_pdf_password

        output = tmp_path / "encrypted.pdf"
        result = apply_pdf_password(tmp_pdf, output, user_password="test123")
        assert result.exists()
        assert result.stat().st_size > 0

        reader = PdfReader(str(result))
        assert reader.is_encrypted is True
        assert reader.decrypt("test123") > 0
        encrypt_dict = reader.trailer["/Encrypt"]
        assert encrypt_dict["/Length"] == 256
        assert encrypt_dict["/CF"]["/StdCF"]["/CFM"] == "/AESV3"
