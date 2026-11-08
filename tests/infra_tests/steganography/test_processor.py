"""Tests for SteganographyProcessor pipeline and embed_steganography convenience function."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.infra_tests.steganography.conftest import has_pypdf, has_qrcode, has_reportlab


def _plain_pdf(path: Path, *, width: int = 200) -> Path:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=width, height=300)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _metadata_processor():
    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor

    return SteganographyProcessor(
        SteganographyConfig(
            enabled=True,
            overlays_enabled=False,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
        )
    )


def test_reused_processor_does_not_embed_previous_document_hashes(tmp_path: Path):
    from pypdf import PdfReader

    first = _plain_pdf(tmp_path / "first.pdf")
    second = _plain_pdf(tmp_path / "second.pdf", width=400)
    processor = _metadata_processor()
    processor.process(first)
    processor.config.hashing_enabled = False
    output = processor.process(second)
    attachment = PdfReader(output).attachments["stego_manifest.json"][0]
    assert json.loads(attachment)["hashes"] == {}
    assert not second.with_suffix(".hashes.json").exists()


@pytest.mark.parametrize("alias", ["same-path", "hardlink", "symlink"])
def test_source_alias_refused_before_any_artifact_write(tmp_path: Path, alias: str):
    import os

    source = _plain_pdf(tmp_path / "source.pdf")
    original = source.read_bytes()
    output = source if alias == "same-path" else tmp_path / "alias.pdf"
    if alias == "hardlink":
        os.link(source, output)
    elif alias == "symlink":
        output.symlink_to(source)
    with pytest.raises(ValueError):
        _metadata_processor().process(source, output)
    assert source.read_bytes() == original
    assert not source.with_suffix(".hashes.json").exists()


def test_protected_custom_pdf_reruns_without_a_public_manifest(tmp_path: Path):
    from infrastructure.steganography.artifact_paths import custom_secure_sources, owned_secure_pdf_sha256

    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.output_suffix = "_private"
    processor.config.manifest_enabled = False
    processor.protect_output = True

    output = processor.process(source)
    assert not source.with_suffix(".hashes.json").exists()
    assert owned_secure_pdf_sha256(source, output) is not None
    assert custom_secure_sources([source, output], "_private") == [source]
    assert processor.process(source) == output


def test_public_manifest_does_not_classify_a_naturally_suffixed_pdf(tmp_path: Path):
    from infrastructure.steganography.artifact_paths import custom_secure_sources, secure_file_sha256

    source = tmp_path / "source.pdf"
    naturally_suffixed = _plain_pdf(tmp_path / "source_private.pdf")
    source.with_suffix(".hashes.json").write_text(
        json.dumps(
            {
                "source_file": source.name,
                "steganography_applied": "true",
                "secure_pdf": naturally_suffixed.name,
                "secure_pdf_sha256": secure_file_sha256(naturally_suffixed),
            }
        ),
        encoding="utf-8",
    )
    assert custom_secure_sources([naturally_suffixed], "_private") == [naturally_suffixed]
    _plain_pdf(source)
    with pytest.raises(ValueError, match="without matching source evidence"):
        custom_secure_sources([source, naturally_suffixed], "_private")


def test_unavailable_private_ownership_preserves_previous_custom_output(tmp_path: Path):
    from infrastructure.steganography.artifact_paths import owned_secure_pdf_sha256

    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.output_suffix = "_private"
    processor.protect_output = True
    output = processor.process(source)
    previous = output.read_bytes()
    state_directory = tmp_path / ".steganography-ownership"
    state_directory.chmod(0o750)
    try:
        assert owned_secure_pdf_sha256(source, output) is None
        with pytest.raises(ValueError, match="without matching source evidence"):
            processor.process(source)
        assert output.read_bytes() == previous
    finally:
        state_directory.chmod(0o700)


def test_missing_pdf_with_nonprivate_receipt_refuses_publication(tmp_path: Path):
    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.output_suffix = "_private"
    processor.protect_output = True
    output = processor.process(source)
    (receipt,) = (tmp_path / ".steganography-ownership").glob("*.json")
    original = receipt.read_bytes()
    output.unlink()
    receipt.chmod(0o644)

    with pytest.raises(ValueError, match="Existing ownership receipt is not a private regular file"):
        processor.process(source)
    assert not output.exists()
    assert receipt.read_bytes() == original

    receipt.chmod(0o600)
    assert processor.process(source) == output
    assert processor.process(source) == output


def test_private_receipt_publication_rolls_back_when_directory_is_substituted(tmp_path: Path, monkeypatch):
    import os

    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.output_suffix = "_private"
    processor.protect_output = True
    output = processor.process(source)
    owner = tmp_path / ".steganography-ownership"
    (receipt,) = owner.glob("*.json")
    manifest = source.with_suffix(".hashes.json")
    prior_pdf, prior_receipt, prior_manifest = output.read_bytes(), receipt.read_bytes(), manifest.read_bytes()
    _plain_pdf(source, width=400)
    moved = tmp_path / "detached-owner"
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    sentinel = replacement / receipt.name
    sentinel.write_bytes(b"unrelated existing receipt")
    original_replace = os.replace

    def substitute_directory(source, destination, **kwargs):
        if destination == receipt.name and not moved.exists():
            owner.rename(moved)
            owner.symlink_to(replacement, target_is_directory=True)
        return original_replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", substitute_directory)
    with pytest.raises(ValueError, match="Private ownership directory changed during publication"):
        processor.process(source)
    assert output.read_bytes() == prior_pdf
    assert (moved / receipt.name).read_bytes() == prior_receipt
    assert manifest.read_bytes() == prior_manifest
    assert not list(moved.glob("*.tmp"))
    assert sentinel.read_bytes() == b"unrelated existing receipt"


def test_missing_output_parent_preserves_previous_manifest(tmp_path: Path):
    source = _plain_pdf(tmp_path / "source.pdf")
    manifest = source.with_suffix(".hashes.json")
    manifest.write_bytes(b"previous manifest")
    with pytest.raises(FileNotFoundError):
        _metadata_processor().process(source, tmp_path / "missing" / "output.pdf")
    assert manifest.read_bytes() == b"previous manifest"


def test_required_missing_kmyth_preserves_all_published_artifacts(tmp_path: Path, monkeypatch):
    source = _plain_pdf(tmp_path / "source.pdf")
    output = _plain_pdf(tmp_path / "result.pdf", width=100)
    manifest = source.with_suffix(".hashes.json")
    manifest.write_bytes(b"previous manifest")
    pdf_sealed = output.with_name(output.name + ".ski")
    manifest_sealed = manifest.with_name(manifest.name + ".ski")
    pdf_sealed.write_bytes(b"previous PDF seal")
    manifest_sealed.write_bytes(b"previous manifest seal")
    before = {path: path.read_bytes() for path in [source, output, manifest, pdf_sealed, manifest_sealed]}
    processor = _metadata_processor()
    processor.config.kmyth_enabled = processor.config.kmyth_required = True
    processor.config.kmyth_binary_dir = str(tmp_path / "no-binaries")
    processor.config.kmyth_source_dir = str(tmp_path / "no-source")
    processor.config.kmyth_seal_artifacts = ["pdf", "hash_manifest"]
    monkeypatch.setenv("PATH", "")
    from infrastructure.steganography.kmyth_adapter import KmythUnavailableError

    with pytest.raises(KmythUnavailableError):
        processor.process(source, output)
    assert {path: path.read_bytes() for path in before} == before
    assert not list(tmp_path.glob(".steganography-*"))


def test_success_preserves_source_manifest_name_and_previous_destination_modes(tmp_path: Path):
    import hashlib
    import stat
    from pypdf import PdfReader

    source = _plain_pdf(tmp_path / "source.pdf")
    output = _plain_pdf(tmp_path / "result.pdf", width=100)
    manifest = source.with_suffix(".hashes.json")
    manifest.write_bytes(b"previous manifest")
    output.chmod(0o640)
    manifest.chmod(0o600)
    _metadata_processor().process(source, output)
    assert len(PdfReader(output).pages) == 1
    assert json.loads(manifest.read_text())["hashes"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert not output.with_suffix(".hashes.json").exists()
    assert stat.S_IMODE(output.stat().st_mode) == 0o640
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o600


def test_runtime_config_mutation_is_validated_before_processing(tmp_path: Path):
    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.enabled = "false"
    with pytest.raises(ValueError, match="enabled must be a boolean"):
        processor.process(source)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source.pdf"]


def test_encrypted_variant_keeps_embedded_provenance_attachment(tmp_path: Path):
    from pypdf import PdfReader

    source = _plain_pdf(tmp_path / "source.pdf")
    processor = _metadata_processor()
    processor.config.encryption_enabled = True
    processor.config.pdf_password = "component-password"
    result = processor.process(source)
    reader = PdfReader(result)
    assert reader.is_encrypted
    assert reader.decrypt("component-password")
    attachment = reader.attachments["stego_manifest.json"][0]
    assert json.loads(attachment)["hashes"]


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

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=has_qrcode(),
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        output = tmp_path / "output_steganography.pdf"
        result = SteganographyProcessor(config).process(
            tmp_pdf, output_pdf=output, title="Test Paper", authors=["Author One"], keywords=["test"]
        )
        assert result.exists()
        assert result.stat().st_size > 0
        assert result == output

    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
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
        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        output = tmp_path / "page_count_test.pdf"
        result = SteganographyProcessor(config).process(tmp_pdf, output_pdf=output)
        assert len(PdfReader(str(result)).pages) == original_pages

    @pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
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
        output = tmp_path / "manifest_test.pdf"
        SteganographyProcessor(config).process(tmp_pdf, output_pdf=output, title="Manifest Test")
        manifest = tmp_pdf.with_suffix(".hashes.json")
        assert manifest.exists()
        data = json.loads(manifest.read_text())
        assert "sha256" in data["hashes"]
        assert data["document_id"]
        assert data["source_size_bytes"] == tmp_pdf.stat().st_size
        assert "git_commit" in data
        assert isinstance(data["git_commit_available"], bool)


class TestProcessPdfConvenience:
    @pytest.mark.skipif(not (has_pypdf() and has_reportlab()), reason="pypdf and/or reportlab not installed")
    def test_embed_steganography(self, tmp_pdf: Path, tmp_path: Path):
        from infrastructure.steganography.config import SteganographyConfig
        from infrastructure.steganography.core import embed_steganography

        config = SteganographyConfig(
            enabled=True,
            overlays_enabled=False,
            barcodes_enabled=False,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=False,
        )
        output = tmp_path / "convenience_test.pdf"
        assert embed_steganography(tmp_pdf, output_pdf=output, config=config).exists()


def test_overlay_only_preserves_existing_document_catalog(tmp_path: Path):
    from pypdf import PdfReader, PdfWriter
    from infrastructure.steganography.config import DocumentMetadata, SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor
    from infrastructure.steganography.metadata import build_xmp_packet

    source = tmp_path / "catalog.pdf"
    xmp = build_xmp_packet(DocumentMetadata(title="Original catalog")).encode()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.add_metadata({"/Title": "Original catalog"})
    writer.xmp_metadata = xmp
    writer.add_attachment("original.txt", b"unrelated original attachment")
    writer.add_outline_item("Original section", 0)
    with source.open("wb") as stream:
        writer.write(stream)
    original = source.read_bytes()
    config = SteganographyConfig(
        enabled=True,
        overlays_enabled=True,
        barcodes_enabled=False,
        metadata_enabled=False,
        hashing_enabled=False,
        manifest_enabled=False,
    )
    output = SteganographyProcessor(config).process(source)
    assert source.read_bytes() == original
    reader = PdfReader(output)
    assert reader.attachments["original.txt"] == [b"unrelated original attachment"]
    assert reader.trailer["/Root"]["/Metadata"].get_data() == xmp
    assert reader.metadata.title == "Original catalog"
    assert reader.outline[0].title == "Original section"
