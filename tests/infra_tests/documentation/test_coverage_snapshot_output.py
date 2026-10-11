"""Real filesystem and CLI controls for explicitly nominated snapshot DATA."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.documentation import counts_coverage
from infrastructure.documentation._coverage_snapshot_output import CoverageSnapshotOutput

pytestmark = pytest.mark.timeout(30)


def _files(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    retained = tmp_path / "retained"
    retained.mkdir()
    source = Path(counts_coverage.__file__)
    output = retained / "counts_coverage.snapshot.data"
    shutil.copy2(source, output)
    return repo, output, source


def test_snapshot_data_positive_preserves_original_source(tmp_path: Path) -> None:
    repo, output, source = _files(tmp_path)
    before = source.stat()
    original = source.read_bytes()
    admitted = CoverageSnapshotOutput.admit(repo, output, source)
    assert admitted.original_text().encode() == original
    admitted.write_text(original.decode() + "\n")
    assert output.read_bytes() != original
    assert output.stat().st_nlink == 1
    assert source.read_bytes() == original
    assert source.stat() == before


def test_snapshot_data_refuses_protected_repository(tmp_path: Path) -> None:
    repo, output, source = _files(tmp_path)
    protected = repo / "snapshot.data"
    shutil.copy2(output, protected)
    before = protected.read_bytes()
    with pytest.raises(ValueError, match="outside the repository"):
        CoverageSnapshotOutput.admit(repo, protected, source)
    assert protected.read_bytes() == before


def test_snapshot_data_refuses_selected_source_and_physical_alias(tmp_path: Path) -> None:
    repo, _, source = _files(tmp_path)
    before = source.stat()
    with pytest.raises(ValueError, match="outside the repository"):
        CoverageSnapshotOutput.admit(repo, source, source)
    alias = tmp_path / "sdk-alias"
    alias.symlink_to(source.parents[2], target_is_directory=True)
    with pytest.raises(ValueError, match="parent must be a real directory"):
        CoverageSnapshotOutput.admit(repo, alias / "infrastructure/documentation/counts_coverage.py", source)
    assert source.stat() == before


@pytest.mark.parametrize("change", ["symlink", "hardlink", "fifo", "not-copy", "oversize", "missing"])
def test_snapshot_data_refuses_actual_noncopy_files(tmp_path: Path, change: str) -> None:
    repo, output, source = _files(tmp_path)
    source_before = source.stat()
    if change == "symlink":
        independent = output.with_name("independent.data")
        output.rename(independent)
        output.symlink_to(independent)
    elif change == "hardlink":
        # Only task-owned DATA is linked; selected SDK Source is never linked.
        os.link(output, output.with_name("data-alias"))
    elif change == "fifo":
        output.unlink()
        os.mkfifo(output)
    elif change == "not-copy":
        output.write_bytes(b"not selected Source\n")
    elif change == "oversize":
        with output.open("wb") as stream:
            stream.truncate(5 * 1024 * 1024)
    else:
        output.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        CoverageSnapshotOutput.admit(repo, output, source)
    assert source.stat() == source_before


@pytest.mark.parametrize("change", ["body", "mode", "inode", "parent"])
def test_snapshot_data_rechecks_original_copy_before_write(tmp_path: Path, change: str) -> None:
    repo, output, source = _files(tmp_path)
    admitted = CoverageSnapshotOutput.admit(repo, output, source)
    original = source.read_bytes()
    if change == "body":
        output.write_bytes(b"changed after admission\n")
    elif change == "mode":
        output.chmod(0o600 if output.stat().st_mode & 0o777 != 0o600 else 0o644)
    elif change == "inode":
        replacement = output.with_name("replacement.data")
        shutil.copy2(source, replacement)
        replacement.replace(output)
    else:
        output.parent.rename(tmp_path / "detached-retained")
        output.parent.mkdir()
        shutil.copy2(source, output)
    with pytest.raises(ValueError, match="changed|confinement"):
        admitted.write_text(original.decode() + "\n")
    assert source.read_bytes() == original


def test_snapshot_data_rechecks_copied_source_binding(tmp_path: Path) -> None:
    repo, output, selected_source = _files(tmp_path)
    # This Source-body input is an independently copied task fixture, never
    # imported/executed code and never claimed as installed SDK acceptance.
    copied_source = tmp_path / "owned-sdk/infrastructure/documentation/counts_coverage.py"
    copied_source.parent.mkdir(parents=True)
    shutil.copy2(selected_source, copied_source)
    admitted = CoverageSnapshotOutput.admit(repo, output, copied_source)
    copied_source.write_text(copied_source.read_text() + "\n")
    before = output.read_bytes()
    with pytest.raises(ValueError, match="Source changed"):
        admitted.write_text(before.decode() + "\n")
    assert output.read_bytes() == before


def test_public_verifier_refuses_implicit_rewrite_before_measurement(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="--coverage-snapshot-output"):
        counts_coverage.verify_exemplar_coverage_result(tmp_path, rewrite=True)
    with pytest.raises(ValueError, match="--coverage-snapshot-output"):
        counts_coverage.verify_exemplar_coverage(tmp_path, rewrite=True)
    assert list(tmp_path.iterdir()) == []


def test_public_verifier_refuses_unadmitted_copy_before_measurement(tmp_path: Path) -> None:
    repo, output, source = _files(tmp_path)
    original = source.read_bytes()
    output.write_bytes(b"wrong DATA\n")
    with pytest.raises(ValueError, match="must initially copy"):
        counts_coverage.verify_exemplar_coverage_result(repo, rewrite=True, snapshot_output=output)
    assert output.read_bytes() == b"wrong DATA\n"
    assert source.read_bytes() == original


def test_counts_cli_refuses_implicit_write_with_concrete_action() -> None:
    repo = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, str(repo / "scripts/docgen/counts.py"), "--verify-coverage", "--write"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --coverage-snapshot-output" in result.stderr
    assert "measured" not in result.stdout
