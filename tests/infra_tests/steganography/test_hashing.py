"""Tests for steganography hashing module."""

from __future__ import annotations

import json
from pathlib import Path


class TestHashing:
    def test_compute_file_hashes(self, tmp_pdf: Path):
        from infrastructure.steganography.hashing import compute_file_hashes

        hashes = compute_file_hashes(tmp_pdf)
        assert "sha256" in hashes
        assert "sha512" in hashes
        assert len(hashes["sha256"]) == 64
        assert len(hashes["sha512"]) == 128

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

        assert compute_file_hashes(tmp_pdf) == compute_file_hashes(tmp_pdf)

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

        manifest_path = write_hash_manifest(tmp_pdf, {"sha256": "a" * 64}, extra={"document_id": "test123"})
        data = json.loads(manifest_path.read_text())
        assert data["document_id"] == "test123"

    def test_compute_content_hash(self):
        from infrastructure.steganography.hashing import compute_content_hash

        h = compute_content_hash(b"hello world")
        assert isinstance(h, str)
        assert len(h) == 64
