"""Tests for steganography encryption module."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from infrastructure.steganography.encryption import (
    _CRYPTOGRAPHY_AVAILABLE,
    decrypt_payload,
    encrypt_payload,
    generate_document_id,
    generate_fingerprint,
)
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


class TestEncryptDecryptRoundtrip:
    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip(self):
        plaintext = "Hello, World! This is secret data."
        encrypted = encrypt_payload(plaintext)
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted
        assert "key" in encrypted

        decrypted = decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], encrypted["key"])
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_unicode(self):
        plaintext = "Unicode: 你好世界 こんにちは مرحبا"
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], encrypted["key"])
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_empty(self):
        plaintext = ""
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], encrypted["key"])
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_long_text(self):
        plaintext = "A" * 100_000
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], encrypted["key"])
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_custom_key(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = AESGCM.generate_key(bit_length=256)
        plaintext = "Custom key test"
        encrypted = encrypt_payload(plaintext, key=key)
        assert base64.b64decode(encrypted["key"]) == key
        decrypted = decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], encrypted["key"])
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_different_keys_different_ciphertext(self):
        plaintext = "same data"
        enc1 = encrypt_payload(plaintext)
        enc2 = encrypt_payload(plaintext)
        # Different random keys should produce different ciphertext
        assert enc1["ciphertext"] != enc2["ciphertext"]

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_wrong_key_fails(self):
        plaintext = "secret"
        encrypted = encrypt_payload(plaintext)
        # Generate a different key
        enc2 = encrypt_payload("other")
        with pytest.raises(Exception):
            decrypt_payload(encrypted["ciphertext"], encrypted["nonce"], enc2["key"])


class TestGenerateFingerprint:
    def test_basic(self):
        result = generate_fingerprint(b"test content")
        assert "fingerprint" in result
        assert "secret" in result
        assert len(result["fingerprint"]) == 64

    def test_deterministic_with_same_secret(self):
        r1 = generate_fingerprint(b"data", secret="my_secret")
        r2 = generate_fingerprint(b"data", secret="my_secret")
        assert r1["fingerprint"] == r2["fingerprint"]
        assert r1["secret"] == r2["secret"]

    def test_different_content_different_fingerprint(self):
        r1 = generate_fingerprint(b"data1", secret="same")
        r2 = generate_fingerprint(b"data2", secret="same")
        assert r1["fingerprint"] != r2["fingerprint"]

    def test_different_secret_different_fingerprint(self):
        r1 = generate_fingerprint(b"data", secret="secret1")
        r2 = generate_fingerprint(b"data", secret="secret2")
        assert r1["fingerprint"] != r2["fingerprint"]

    def test_auto_generated_secret(self):
        r1 = generate_fingerprint(b"data")
        r2 = generate_fingerprint(b"data")
        assert r1["secret"] != r2["secret"]  # Random secrets

    def test_empty_content(self):
        result = generate_fingerprint(b"")
        assert len(result["fingerprint"]) == 64


class TestGenerateDocumentId:
    def test_length(self):
        doc_id = generate_document_id()
        assert len(doc_id) == 32

    def test_hex_chars(self):
        doc_id = generate_document_id()
        assert all(c in "0123456789abcdef" for c in doc_id)

    def test_uniqueness(self, monkeypatch):
        # Defensive: uniqueness only holds in the random branch, so
        # ensure deterministic-mode is off regardless of upstream
        # suite-level env state.
        monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)
        ids = {generate_document_id() for _ in range(50)}
        assert len(ids) == 50
