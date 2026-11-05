"""Real-file controls for diagnostic scope, custody, bounds and actual issue lists."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from gates.artifact_manifest import REQUIRED_OUTPUTS
from gates.pipeline_diagnostics import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    main,
    record_snapshot,
    record_validator_issues,
    selected_paths,
)

PROJECT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.timeout(120)


def _tree(tmp_path: Path) -> tuple[Path, Path]:
    """Create only public diagnostic inputs and a separate output directory."""
    root, directory = tmp_path / "project", tmp_path / "diagnostics"
    (root / "output/data").mkdir(parents=True)
    (root / "output/reports").mkdir()
    (root / "manuscript").mkdir()
    directory.mkdir()
    return root, directory


def _rows(path: Path) -> dict[str, dict]:
    """Index one actual diagnostic manifest by its source-relative paths."""
    return {row["path"]: row for row in json.loads(path.read_text())["files"]}


def test_phase_deltas_and_failure_bytes_are_original_and_scope_confined(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    artifact = root / "output/data/artifact_provenance.json"
    section = root / "manuscript/02_intro.md"
    artifact.write_bytes(b'{"actual": 1}\n')
    section.write_bytes(b"# Actual compiled section\n")
    (root / "pyproject.toml").write_text("[project]\nname='source-only'\n")
    (root / "output/.pipeline").mkdir()
    (root / "output/.pipeline/private-cache.json").write_text("DO NOT CAPTURE")
    (root / "manuscript/private.json").write_text("DO NOT CAPTURE")
    before = _rows(record_snapshot(root, directory, "analysis-after"))
    artifact.write_bytes(b'{"actual": 2}\n')
    after = _rows(record_snapshot(root, directory, "render-after", retain=True))
    assert (
        before["output/data/artifact_provenance.json"]["sha256"]
        != after["output/data/artifact_provenance.json"]["sha256"]
    )
    row = after["output/data/artifact_provenance.json"]
    assert row["sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert (directory / row["raw_file"]).read_bytes() == artifact.read_bytes()
    assert (directory / after["manuscript/02_intro.md"]["raw_file"]).read_bytes() == section.read_bytes()
    assert "raw_file" not in after["pyproject.toml"]
    assert "output/.pipeline/private-cache.json" not in after
    assert "manuscript/private.json" not in after
    assert any(row["status"] == "unavailable" for row in after.values())
    payload = json.loads((directory / "render-after-manifest.json").read_text())
    assert payload["diagnostic_only"] is True
    assert payload["acceptance_authorized"] is False


@pytest.mark.parametrize("relative", ("output/data/artifact_provenance.json", "manuscript/02_intro.md"))
def test_source_symlinks_never_capture_outside_bytes(tmp_path: Path, relative: str) -> None:
    root, directory = _tree(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"PRIVATE OUTSIDE CONTENT")
    (root / relative).symlink_to(outside)
    rows = _rows(record_snapshot(root, directory, "failed", retain=True))
    assert rows[relative]["status"] == "unavailable"
    assert "sha256" not in rows[relative]
    assert "raw_file" not in rows[relative]
    assert all(b"PRIVATE OUTSIDE CONTENT" not in path.read_bytes() for path in directory.iterdir())


def test_linked_source_directory_and_output_destination_refuse(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    (root / "output/data").rmdir()
    (root / "output/data").symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="directory ancestor"):
        record_snapshot(root, directory, "failed")
    linked = tmp_path / "linked-diagnostics"
    linked.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="directory ancestor"):
        record_snapshot(root, linked, "failed")


def test_oversized_file_is_unavailable_instead_of_partially_hashed(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    path = root / "output/data/artifact_provenance.json"
    path.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    row = _rows(record_snapshot(root, directory, "failed", retain=True))[path.relative_to(root).as_posix()]
    assert row["status"] == "unavailable"
    assert "sha256" not in row
    assert "raw_file" not in row


def test_aggregate_limit_never_grants_hashes_to_unread_remainder(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    paths = [
        relative for relative in REQUIRED_OUTPUTS if relative.startswith("output/data/") and relative.endswith(".json")
    ]
    count = MAX_TOTAL_BYTES // MAX_FILE_BYTES + 1
    for relative in paths[:count]:
        (root / relative).write_bytes(b"x" * MAX_FILE_BYTES)
    rows = _rows(record_snapshot(root, directory, "failed"))
    actual = [rows[relative] for relative in paths[:count]]
    assert sum(row["status"] == "observed" for row in actual) == count - 1
    assert sum(row["status"] == "unavailable" for row in actual) == 1
    assert json.loads((directory / "failed-manifest.json").read_text())["observed_bytes"] == MAX_TOTAL_BYTES


def test_directory_census_refuses_overflow_instead_of_claiming_a_complete_subset(tmp_path: Path) -> None:
    root, _ = _tree(tmp_path)
    for index in range(MAX_FILES + 1):
        (root / "output/data" / f"candidate_{index:04d}.json").write_text("{}")
    with pytest.raises(ValueError, match="census exceeds"):
        selected_paths(root)


def test_manifest_cannot_overwrite_a_linked_destination(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("original")
    (directory / "failed-manifest.json").symlink_to(outside)
    with pytest.raises(ValueError):
        record_snapshot(root, directory, "failed")
    assert outside.read_text() == "original"


def test_invalid_labels_and_in_project_destinations_refuse(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    with pytest.raises(ValueError, match="bounded label"):
        record_snapshot(root, directory, "../escape")
    with pytest.raises(ValueError, match="outside the project"):
        record_snapshot(root, root / "output", "failed")
    with pytest.raises(ValueError, match="root or active"):
        record_validator_issues(root, directory, "invented")


def test_real_validators_report_actual_project_issues_and_wrong_source_origin(tmp_path: Path) -> None:
    root, directory = _tree(tmp_path)
    observed = json.loads(record_validator_issues(PROJECT, directory, "root").read_text())
    assert {row["validator"] for row in observed["observations"]} == {
        "semantic_gluing",
        "integration_audit",
        "canonical_sheaf",
    }
    assert any(row["status"] == "observed" for row in observed["observations"])
    for row in observed["observations"]:
        if row["status"] == "observed":
            assert row["issue_count"] >= len(row["issues"])
            assert all(isinstance(issue, str) for issue in row["issues"])
            assert Path(row["module_file"]).is_relative_to(PROJECT / "src")
    refused = json.loads(record_validator_issues(root, directory, "active").read_text())
    assert all(row["status"] == "unavailable" for row in refused["observations"])
    assert all("outside the observed project source" in row["reason"] for row in refused["observations"])
    assert refused["acceptance_authorized"] is False


def test_cli_modes_preserve_diagnostic_only_records(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root, directory = _tree(tmp_path)
    for mode, phase in (("snapshot", "before"), ("raw", "failed"), ("validators", "active")):
        assert main([mode, "--project-root", str(root), "--directory", str(directory), "--phase", phase]) == 0
        assert json.loads(capsys.readouterr().out)["diagnostic_only"] is True
