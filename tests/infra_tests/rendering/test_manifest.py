"""Tests for ``infrastructure.rendering.manifest``.

Pure data tests — no mocks, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.rendering.manifest import (
    SCHEMA_VERSION,
    ManifestClaim,
    build_manifest,
)


@pytest.fixture
def pinned_values_file(tmp_path: Path) -> Path:
    path = tmp_path / "pinned.json"
    path.write_text(
        json.dumps(
            {
                "_meta": {"schema_version": "1.0"},
                "_example_do_not_use": {"value": 0.0},
                "figure_03_panel_b": {
                    "manuscript_section": "03_results.md / Fig 3(b)",
                    "claim_text": "k = 0.4271 ± 0.0003",
                    "value": 0.4271,
                    "abs_tolerance": 0.0003,
                    "verifier_function": "projects.example.src.compute_k",
                    "verifier_args": {"n_trials": 1000, "seed": 42},
                },
                "table_02_row_3": {
                    "manuscript_section": "03_results.md / Table 2 row 3",
                    "claim_text": "p < 0.001",
                    "value": 0.0008,
                    "rel_tolerance": 0.1,
                    "verifier_function": "projects.example.src.compute_p",
                    "verifier_args": {},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_build_manifest_includes_pinned_claims(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example_project",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
    )
    assert manifest.project_name == "example_project"
    assert manifest.schema_version == SCHEMA_VERSION
    assert len(manifest.claims) == 2
    ids = {c.id for c in manifest.claims}
    assert ids == {"figure_03_panel_b", "table_02_row_3"}


def test_build_manifest_excludes_underscore_keys(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
    )
    ids = {c.id for c in manifest.claims}
    assert "_meta" not in ids
    assert "_example_do_not_use" not in ids


def test_manifest_to_dict_round_trip(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
    )
    d = manifest.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["project_name"] == "example"
    # JSON-roundtrippable
    rt = json.loads(json.dumps(d))
    assert rt["project_name"] == "example"


def test_manifest_write_to_creates_directory(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
    )
    out_path = tmp_path / "nested" / "deeper" / "manifest.json"
    manifest.write_to(out_path)
    assert out_path.exists()
    parsed = json.loads(out_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == SCHEMA_VERSION


def test_build_manifest_missing_pinned_file_returns_empty_claims(
    tmp_path: Path,
) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=tmp_path / "no-such-file.json",
    )
    assert manifest.claims == ()


def test_build_manifest_invalid_pinned_file_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a JSON object"):
        build_manifest(
            project_name="example",
            repo_dir=tmp_path,
            pinned_values_path=bad,
        )


def test_build_manifest_default_entry_points(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
    )
    assert "reproduce_all" in manifest.entry_points
    assert "tests" in manifest.entry_points
    assert "verify_claims" in manifest.entry_points


def test_build_manifest_custom_entry_points(pinned_values_file: Path, tmp_path: Path) -> None:
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
        entry_points={"only_one": "echo hi"},
    )
    assert manifest.entry_points == {"only_one": "echo hi"}


def test_manifest_claim_emits_only_specified_tolerance() -> None:
    c = ManifestClaim(
        id="x",
        manuscript_section="s",
        claim_text="t",
        value=1.0,
        tolerance_abs=0.001,
        tolerance_rel=None,
        verifier_function="f",
        verifier_args={},
    )
    d = c.to_dict()
    assert "abs_tolerance" in d
    assert "rel_tolerance" not in d


def test_manifest_archival_receipts_passthrough(pinned_values_file: Path, tmp_path: Path) -> None:
    receipts = {"zenodo": "10.5281/zenodo.999", "ipfs_pinata": "QmABC"}
    manifest = build_manifest(
        project_name="example",
        repo_dir=tmp_path,
        pinned_values_path=pinned_values_file,
        archival_receipts=receipts,
    )
    assert manifest.archival_receipts == receipts
