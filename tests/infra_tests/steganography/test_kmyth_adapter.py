"""Tests for optional Kmyth/TPM integration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _write_fake_kmyth_tools(bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    seal = bin_dir / "kmyth-seal"
    seal.write_text(
        "#!/bin/sh\n"
        'input=""\n'
        'output=""\n'
        'while [ "$#" -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --input|-i) shift; input="$1" ;;\n'
        '    --output|-o) shift; output="$1" ;;\n'
        "    --pcrs_list|-p|--cipher|-c) shift ;;\n"
        "  esac\n"
        "  shift\n"
        "done\n"
        'if [ -z "$output" ]; then exit 2; fi\n'
        'printf \'sealed:%s\' "$input" > "$output"\n',
        encoding="utf-8",
    )
    unseal = bin_dir / "kmyth-unseal"
    unseal.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    seal.chmod(0o755)
    unseal.chmod(0o755)
    return bin_dir


def test_validate_kmyth_installation_reports_missing_tools(tmp_path: Path) -> None:
    from infrastructure.steganography.kmyth_adapter import validate_kmyth_installation

    result = validate_kmyth_installation(
        binary_dir=tmp_path / "missing-bin",
        source_dir=tmp_path / "missing-source",
    )

    assert result.available is False
    assert "kmyth-seal executable not found" in result.summary()


def test_validate_kmyth_installation_accepts_custom_binary_dir(tmp_path: Path) -> None:
    from infrastructure.steganography.kmyth_adapter import validate_kmyth_installation

    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    result = validate_kmyth_installation(
        binary_dir=bin_dir,
        source_dir=tmp_path / "missing-source",
    )

    assert result.available is True
    assert result.seal_path == (bin_dir / "kmyth-seal").resolve()
    assert result.unseal_path == (bin_dir / "kmyth-unseal").resolve()


def test_seal_file_with_kmyth_writes_sidecar(tmp_path: Path) -> None:
    from infrastructure.steganography.kmyth_adapter import KmythSealOptions, seal_file_with_kmyth

    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    artifact = tmp_path / "paper.hashes.json"
    artifact.write_text('{"hashes": {}}', encoding="utf-8")

    sealed = seal_file_with_kmyth(
        artifact,
        options=KmythSealOptions(binary_dir=bin_dir, source_dir=tmp_path / "source", pcrs=(0, 2, 7)),
    )

    assert sealed == Path(str(artifact) + ".ski")
    assert sealed.read_text(encoding="utf-8") == f"sealed:{artifact}"


def test_seal_file_with_kmyth_honors_overwrite_false(tmp_path: Path) -> None:
    from infrastructure.steganography.kmyth_adapter import KmythSealOptions, seal_file_with_kmyth

    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    artifact = tmp_path / "paper.pdf"
    artifact.write_bytes(b"%PDF-1.4\n")
    sealed = Path(str(artifact) + ".ski")
    sealed.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        seal_file_with_kmyth(
            artifact,
            options=KmythSealOptions(binary_dir=bin_dir, source_dir=tmp_path / "source", overwrite=False),
        )


def test_processor_kmyth_step_seals_selected_artifacts(tmp_path: Path) -> None:
    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor

    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    pdf = tmp_path / "paper_steganography.pdf"
    manifest = tmp_path / "paper.hashes.json"
    pdf.write_bytes(b"%PDF-1.4\n")
    manifest.write_text('{"hashes": {}}', encoding="utf-8")

    config = SteganographyConfig(
        enabled=True,
        kmyth_enabled=True,
        kmyth_binary_dir=str(bin_dir),
        kmyth_source_dir=str(tmp_path / "source"),
        kmyth_seal_artifacts=["hash_manifest", "pdf"],
    )
    sealed = SteganographyProcessor(config)._step_kmyth(pdf, manifest)

    assert sealed == [Path(str(manifest) + ".ski"), Path(str(pdf) + ".ski")]
    assert sealed[0].exists()
    assert sealed[1].exists()


def test_processor_kmyth_step_skips_unavailable_when_not_required(tmp_path: Path) -> None:
    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor

    pdf = tmp_path / "paper_steganography.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    config = SteganographyConfig(
        enabled=True,
        kmyth_enabled=True,
        kmyth_required=False,
        kmyth_source_dir=str(tmp_path / "missing-source"),
        kmyth_binary_dir=str(tmp_path / "missing-bin"),
        kmyth_seal_artifacts=["pdf"],
    )

    assert SteganographyProcessor(config)._step_kmyth(pdf, None) == []


def test_processor_kmyth_step_fails_unavailable_when_required(tmp_path: Path) -> None:
    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor
    from infrastructure.steganography.kmyth_adapter import KmythUnavailableError

    pdf = tmp_path / "paper_steganography.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    config = SteganographyConfig(
        enabled=True,
        kmyth_enabled=True,
        kmyth_required=True,
        kmyth_source_dir=str(tmp_path / "missing-source"),
        kmyth_binary_dir=str(tmp_path / "missing-bin"),
        kmyth_seal_artifacts=["pdf"],
    )

    with pytest.raises(KmythUnavailableError):
        SteganographyProcessor(config)._step_kmyth(pdf, None)


def test_fake_kmyth_tools_are_executable(tmp_path: Path) -> None:
    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")

    assert os.access(bin_dir / "kmyth-seal", os.X_OK)
    assert os.access(bin_dir / "kmyth-unseal", os.X_OK)
