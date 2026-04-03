"""Tests for infrastructure.steganography.encryption — additional coverage."""

import base64

from infrastructure.steganography.encryption import (
    encrypt_payload,
    decrypt_payload,
    generate_fingerprint,
    generate_document_id,
    _CRYPTOGRAPHY_AVAILABLE,
)

import pytest


class TestEncryptDecryptRoundtrip:
    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip(self):
        plaintext = "Hello, World! This is secret data."
        encrypted = encrypt_payload(plaintext)
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted
        assert "key" in encrypted

        decrypted = decrypt_payload(
            encrypted["ciphertext"], encrypted["nonce"], encrypted["key"]
        )
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_unicode(self):
        plaintext = "Unicode: 你好世界 こんにちは مرحبا"
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(
            encrypted["ciphertext"], encrypted["nonce"], encrypted["key"]
        )
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_empty(self):
        plaintext = ""
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(
            encrypted["ciphertext"], encrypted["nonce"], encrypted["key"]
        )
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_roundtrip_long_text(self):
        plaintext = "A" * 100_000
        encrypted = encrypt_payload(plaintext)
        decrypted = decrypt_payload(
            encrypted["ciphertext"], encrypted["nonce"], encrypted["key"]
        )
        assert decrypted == plaintext

    @pytest.mark.skipif(not _CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_custom_key(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = AESGCM.generate_key(bit_length=256)
        plaintext = "Custom key test"
        encrypted = encrypt_payload(plaintext, key=key)
        assert base64.b64decode(encrypted["key"]) == key
        decrypted = decrypt_payload(
            encrypted["ciphertext"], encrypted["nonce"], encrypted["key"]
        )
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

    def test_uniqueness(self):
        ids = {generate_document_id() for _ in range(50)}
        assert len(ids) == 50
