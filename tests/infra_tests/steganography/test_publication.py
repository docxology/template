"""Real-file controls for the PDF artifact publication boundary."""

from pathlib import Path

import pytest

from infrastructure.steganography.publication import publish_artifacts, validate_destinations, validate_pdf


def test_artifact_preflight_keeps_existing_destinations_on_missing_stage(tmp_path: Path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"original source")
    output = tmp_path / "result.pdf"
    manifest = tmp_path / "source.hashes.json"
    output.write_bytes(b"previous PDF")
    manifest.write_bytes(b"previous manifest")
    staged = tmp_path / "new.pdf"
    staged.write_bytes(b"replacement")
    before = {path: path.read_bytes() for path in [source, output, manifest]}
    with pytest.raises(ValueError, match="Staged artifact must be a regular file"):
        publish_artifacts({output: staged, manifest: tmp_path / "missing.json"}, source=source)
    assert {path: path.read_bytes() for path in before} == before
    assert not list(tmp_path.glob(".*.steg-*"))


def test_artifact_targets_cannot_alias_each_other(tmp_path: Path):
    import os

    source = tmp_path / "source.pdf"
    output = tmp_path / "result.pdf"
    alias = tmp_path / "manifest.json"
    source.write_bytes(b"source")
    output.write_bytes(b"previous")
    os.link(output, alias)
    with pytest.raises(ValueError, match="share an inode"):
        validate_destinations(source, [output, alias])
    assert output.read_bytes() == alias.read_bytes() == b"previous"


def test_artifact_no_overwrite_is_preserved_before_other_replacements(tmp_path: Path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "result.pdf"
    sealed = tmp_path / "result.pdf.ski"
    staged = tmp_path / "stage"
    for path, value in [(source, b"source"), (output, b"previous PDF"), (sealed, b"previous seal"), (staged, b"new")]:
        path.write_bytes(value)
    with pytest.raises(FileExistsError):
        publish_artifacts({output: staged, sealed: staged}, source=source, no_overwrite={sealed})
    assert output.read_bytes() == b"previous PDF"
    assert sealed.read_bytes() == b"previous seal"


def test_invalid_pdf_is_rejected_by_actual_parser(tmp_path: Path):
    from pypdf.errors import PdfReadError

    staged = tmp_path / "invalid.pdf"
    staged.write_bytes(b"not a PDF")
    with pytest.raises(PdfReadError):
        validate_pdf(staged)


def test_encrypted_pdf_validation_uses_actual_password(tmp_path: Path):
    from pypdf import PdfWriter

    staged = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=300)
    writer.encrypt("component-password", algorithm="AES-256")
    with staged.open("wb") as stream:
        writer.write(stream)
    with pytest.raises(ValueError, match="Cannot validate"):
        validate_pdf(staged, password="wrong")
    validate_pdf(staged, password="component-password")
