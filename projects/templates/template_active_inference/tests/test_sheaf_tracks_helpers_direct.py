"""Direct real-file controls for sheaf-track I/O and artifact helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from direct_recompute_support import copy_project_tree
from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext
from roadmap_tracks.sheaf_tracks_helpers import (
    _canonical_artifact_rows,
    _copied_parity,
    _portable_repo_path,
    _remove_legacy_artifacts,
)
from roadmap_tracks.sheaf_tracks_io import (
    _bound_tracks,
    _claim_ids_by_path,
    _load_structured,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, LEGACY_ARTIFACTS


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide a disposable project copy for canonical-map traversal."""
    return Path(copy_project_tree(tmp_path_factory.mktemp("sheaf_helpers_tree")))


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_load_structured_normalizes_non_object_json_to_empty(tmp_path: Path) -> None:
    path = tmp_path / "rows.json"
    path.write_text('["not", "an", "object"]\n', encoding="utf-8")

    assert _load_structured(path) == {}


def test_load_structured_normalizes_non_object_yaml_to_empty(tmp_path: Path) -> None:
    path = tmp_path / "rows.yaml"
    path.write_text("- not\n- an\n- object\n", encoding="utf-8")

    assert _load_structured(path) == {}


def test_bound_tracks_ignores_non_mapping_yaml_tracks(tmp_path: Path) -> None:
    manifest = tmp_path / "manuscript" / "sheaf" / "manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        "sections:\n  - id: ignored\n    tracks: [analytical]\n  - id: valid\n    tracks:\n      analytical: {}\n",
        encoding="utf-8",
    )

    assert _bound_tracks(tmp_path) == {"analytical": ["valid"]}


def test_claim_ids_by_path_ignores_incomplete_yaml_rows(tmp_path: Path) -> None:
    ledger = tmp_path / "data" / "claim_ledger.yaml"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        "claims:\n"
        "  - id: missing-path\n"
        "  - path: output/data/missing-id.json\n"
        "  - id: complete\n"
        "    path: output/data/complete.json\n",
        encoding="utf-8",
    )

    assert _claim_ids_by_path(tmp_path) == {"output/data/complete.json": ["complete"]}


def test_portable_repo_path_falls_back_for_path_outside_detected_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "example"
    project.mkdir(parents=True)
    (repo / "run.sh").touch()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")

    assert _portable_repo_path(outside, project) == outside.as_posix()


def test_copied_parity_classifies_real_file_states(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "example"
    copied = repo / "output" / "templates" / "example"
    project.mkdir(parents=True)
    (repo / "run.sh").touch()

    matched = "output/data/matched.json"
    changed = "output/data/changed.json"
    missing = "output/data/missing.json"
    copied_only = "output/data/copied-only.json"
    deferred_render = "output/pdf/manuscript.pdf"
    _write_bytes(project / matched, b"same")
    _write_bytes(copied / "data/matched.json", b"same")
    _write_bytes(project / changed, b"source")
    _write_bytes(copied / "data/changed.json", b"copied")
    _write_bytes(copied / "data/copied-only.json", b"copied")

    payload = _copied_parity(
        project,
        [matched, changed, missing, copied_only, deferred_render],
    )
    rows = {row["artifact"]: row for row in payload["rows"]}

    assert rows[matched]["status"] == "matched"
    assert rows[changed]["status"] == "deferred"
    assert rows[missing]["status"] == "missing_copied_output"
    assert rows[copied_only]["status"] == "mismatch"
    assert rows[deferred_render]["status"] == "deferred"
    assert payload["copied_root"] == "<repo-root>/output/templates/example"
    assert payload["row_count"] == 5
    assert payload["all_required_sources_present"] is False
    assert payload["all_copied_outputs_match"] is False
    assert payload["all_copied_outputs_match_or_deferred"] is False
    assert payload["pre_copy_stage"] is True


def test_remove_legacy_artifacts_deletes_present_real_file(tmp_path: Path) -> None:
    present = tmp_path / LEGACY_ARTIFACTS[0]
    absent = tmp_path / LEGACY_ARTIFACTS[1]
    _write_bytes(present, b"legacy")
    assert not absent.exists()

    _remove_legacy_artifacts(tmp_path)

    assert not present.exists()
    assert not absent.exists()


def test_canonical_artifact_rows_bind_known_project_copy_state(copied_root: Path) -> None:
    config = copied_root / "manuscript" / "config.yaml"
    ledger = copied_root / "data" / "claim_ledger.yaml"
    artifact = copied_root / "output" / "data" / "parameter_sweep.csv"
    snapshots = {path: path.read_bytes() for path in (config, ledger, artifact)}

    try:
        config.write_text(
            "analysis:\n  scripts:\n    - run_analytical_sweep.py\n",
            encoding="utf-8",
        )
        ledger.write_text(
            "claims:\n  - id: test-claim\n    path: output/data/parameter_sweep.csv\n",
            encoding="utf-8",
        )
        artifact.write_text("value\n1\n", encoding="utf-8")
        context = _ProvenanceContext(
            config_digest="f" * 64,
            deterministic_seed=23,
            source_commit="test-commit",
        )

        rows = _canonical_artifact_rows(copied_root, context)
        by_artifact = {row["artifact"]: row for row in rows}
        row = by_artifact["output/data/parameter_sweep.csv"]
        cycle_row = by_artifact[CANONICAL_ARTIFACTS["provenance"]]

        assert row["exists"] is True
        assert row["size_bytes"] == len(b"value\n1\n")
        assert len(row["sha256"]) == 64
        assert row["deterministic_seed"] == 23
        assert row["config_digest"] == "f" * 64
        assert row["source_commit"] == "test-commit"
        assert row["producer_configured"] is True
        assert row["consumers"]
        assert row["validation_gates"]
        assert row["claim_ids"] == ["test-claim"]
        assert row["complete"] is True
        assert cycle_row["cycle_excluded"] is True
        assert cycle_row["hash_checked"] is False
    finally:
        for path, payload in snapshots.items():
            path.write_bytes(payload)
