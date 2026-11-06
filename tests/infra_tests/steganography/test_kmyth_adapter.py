"""Tests for optional Kmyth/TPM integration."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
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


@pytest.mark.parametrize("existing", [False, True])
def test_genuine_unavailable_provider_preserves_input_and_existing_sidecar(tmp_path: Path, existing: bool) -> None:
    """The real adapter has no discoverable provider; no TPM or replacement tool runs."""
    source = tmp_path / "source.pdf"
    destination = tmp_path / "destination.ski"
    source.write_bytes(b"actual caller input")
    if existing:
        destination.write_bytes(b"previous caller sidecar")
    program = """from pathlib import Path
import sys
from infrastructure.steganography.kmyth_adapter import KmythSealOptions,KmythUnavailableError,seal_file_with_kmyth
root=Path(sys.argv[1])
try:
 seal_file_with_kmyth(root/'source.pdf',root/'destination.ski',options=KmythSealOptions(binary_dir=root/'missing-bin',source_dir=root/'missing-source'))
except KmythUnavailableError:
 raise SystemExit(0)
raise SystemExit(9)
"""
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    from infrastructure.core.secrets import strip_secret_env

    env = strip_secret_env()
    env["PATH"] = str(empty_path)
    for name in ("SSH_AUTH_SOCK", "GPG_AGENT_INFO"):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program, str(tmp_path)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert source.read_bytes() == b"actual caller input"
    assert destination.read_bytes() == b"previous caller sidecar" if existing else not destination.exists()
    assert not list(tmp_path.glob(".kmyth-seal-*"))


@pytest.mark.parametrize("alias", ["same-path", "hardlink", "symlink"])
def test_source_alias_is_refused_before_provider_or_file_changes(tmp_path: Path, alias: str) -> None:
    from infrastructure.steganography.kmyth_adapter import KmythSealOptions, seal_file_with_kmyth

    source = tmp_path / "original.pdf"
    source.write_bytes(b"preserve source bytes")
    destination = source if alias == "same-path" else tmp_path / "alias.ski"
    if alias == "hardlink":
        os.link(source, destination)
    elif alias == "symlink":
        destination.symlink_to(source)
    before = source.stat()
    with pytest.raises(ValueError, match="distinct files"):
        seal_file_with_kmyth(
            source,
            destination,
            options=KmythSealOptions(binary_dir=tmp_path / "missing", source_dir=tmp_path / "missing-source"),
        )
    assert source.read_bytes() == destination.read_bytes() == b"preserve source bytes"
    assert source.stat().st_ino == before.st_ino
    assert not list(tmp_path.glob(".kmyth-seal-*"))


@pytest.mark.parametrize("overwrite", [False, True])
def test_real_filesystem_publication_preserves_source_and_previous_mode(tmp_path: Path, overwrite: bool) -> None:
    """This is filesystem DATA publication, not a simulated TPM positive."""
    from infrastructure.steganography.kmyth_adapter import _file_identity, _publish_sealed_file

    source, staged, destination = (tmp_path / name for name in ("input", "staged", "destination"))
    source.write_bytes(b"caller source")
    staged.write_bytes(b"candidate opaque output DATA")
    if overwrite:
        destination.write_bytes(b"previous DATA")
        destination.chmod(0o640)
    expected = _file_identity(destination)
    _publish_sealed_file(staged, source, destination, overwrite=overwrite, expected_destination=expected)
    assert source.read_bytes() == b"caller source"
    assert destination.read_bytes() == b"candidate opaque output DATA"
    if overwrite:
        assert stat.S_IMODE(destination.stat().st_mode) == 0o640


@pytest.mark.parametrize("invalid", ["missing", "empty", "symlink", "hardlink", "same-input"])
def test_invalid_staged_data_preserves_existing_destination_and_input(tmp_path: Path, invalid: str) -> None:
    from infrastructure.steganography.kmyth_adapter import KmythCommandError, _file_identity, _publish_sealed_file

    source, staged, destination = (tmp_path / name for name in ("input", "staged", "destination"))
    source.write_bytes(b"caller source")
    destination.write_bytes(b"previous sidecar")
    if invalid == "empty":
        staged.write_bytes(b"")
    elif invalid == "symlink":
        staged.symlink_to(source)
    elif invalid == "hardlink":
        os.link(source, staged)
    elif invalid == "same-input":
        staged = source
    with pytest.raises((ValueError, KmythCommandError)):
        _publish_sealed_file(
            staged, source, destination, overwrite=True, expected_destination=_file_identity(destination)
        )
    assert source.read_bytes() == b"caller source"
    assert destination.read_bytes() == b"previous sidecar"


@pytest.mark.parametrize("overwrite", [False, True])
def test_changed_destination_is_preserved_before_publication(tmp_path: Path, overwrite: bool) -> None:
    from infrastructure.steganography.kmyth_adapter import _file_identity, _publish_sealed_file

    source, staged, destination = (tmp_path / name for name in ("input", "staged", "destination"))
    source.write_bytes(b"caller source")
    staged.write_bytes(b"candidate DATA")
    if overwrite:
        destination.write_bytes(b"original preimage")
    expected = _file_identity(destination)
    destination.write_bytes(b"new caller edit")
    with pytest.raises(FileExistsError):
        _publish_sealed_file(staged, source, destination, overwrite=overwrite, expected_destination=expected)
    assert source.read_bytes() == b"caller source"
    assert destination.read_bytes() == b"new caller edit"


def test_subprocess_environment_removes_credentials_and_agents_preserving_nominees() -> None:
    from infrastructure.steganography.kmyth_adapter import KmythSealOptions, _build_subprocess_env

    original = {
        "GH_TOKEN": "controlled-not-real",
        "API_KEY": "controlled-not-real",
        "SSH_AUTH_SOCK": "/controlled/socket",
        "GPG_AGENT_INFO": "/controlled/gpg",
        "TSS2_TCTI_DEFAULT": "old-transport",
        "DYLD_LIBRARY_PATH": "/declared/libs",
        "PATH": "/declared/bin",
    }
    result = _build_subprocess_env(KmythSealOptions(tcti_config="device:/declared/tpm"), original)
    assert not {"GH_TOKEN", "API_KEY", "SSH_AUTH_SOCK", "GPG_AGENT_INFO"}.intersection(result)
    assert result["TSS2_TCTI_DEFAULT"] == "device:/declared/tpm"
    assert result["DYLD_LIBRARY_PATH"].endswith("/declared/libs") and result["PATH"] == "/declared/bin"
    assert original["GH_TOKEN"] == "controlled-not-real" and original["TSS2_TCTI_DEFAULT"] == "old-transport"
