"""Direct tests for ``roadmap_tracks.fixed_point``.

The semantic fixed point rewrites the full generated-artifact surface, so
every writing test runs against an isolated project-tree copy (see
``direct_recompute_support``). This keeps the module's coverage independent of
whether the tracked snapshot happens to read as stale on a given CI leg.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadmap_tracks.fixed_point import (
    _existing_fixed_point_paths,
    _fingerprint,
    _refresh_animation_outputs,
    _validate_fixed_point,
    _write_final_validation_pass,
    _write_fixed_point_pass,
    run_semantic_fixed_point,
)

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("fixed_point_tree"))


def test_fingerprint_is_deterministic_and_content_sensitive(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    assert first == _fingerprint(copied_root)
    probe = copied_root / "output" / "data" / "manuscript_variables.json"
    original = probe.read_bytes()
    try:
        probe.write_bytes(original + b"\n")
        assert _fingerprint(copied_root) != first
    finally:
        probe.write_bytes(original)
    assert _fingerprint(copied_root) == first


def test_refresh_animation_outputs_tolerates_missing_inputs(tmp_path: Path) -> None:
    paths = _refresh_animation_outputs(tmp_path)
    assert paths == {}


@pytest.mark.timeout(600)
def test_fast_path_returns_existing_paths_when_valid(copied_root: Path) -> None:
    # Settle once so the copy is at THIS platform's fixed point (the tracked
    # snapshot may read stale on other legs, e.g. py3.10 float drift). The
    # second call must then take the validated fast path without rewriting.
    run_semantic_fixed_point(copied_root, require_analysis_outputs=False)
    assert _validate_fixed_point(copied_root) == []
    fingerprint_before = _fingerprint(copied_root)
    paths = run_semantic_fixed_point(copied_root, require_analysis_outputs=False)
    expected = {key: path.resolve() for key, path in _existing_fixed_point_paths(copied_root).items()}
    assert {key: path.resolve() for key, path in paths.items()} == expected
    assert paths, "fast path must report the existing artifact paths"
    for key, path in paths.items():
        assert path.exists(), key
    assert _fingerprint(copied_root) == fingerprint_before, "fast path must not rewrite artifacts"


@pytest.mark.timeout(600)
def test_write_pass_and_final_pass_settle_to_valid_state(copied_root: Path) -> None:
    paths = _write_fixed_point_pass(copied_root, require_analysis_outputs=False)
    assert paths, "fixed-point pass must write artifacts"
    final_paths = _write_final_validation_pass(copied_root, require_analysis_outputs=False)
    assert final_paths
    assert _validate_fixed_point(copied_root) == []


@pytest.mark.timeout(600)
def test_stale_artifact_triggers_full_settlement(tmp_path_factory: pytest.TempPathFactory) -> None:
    stale_root = copy_project_tree(tmp_path_factory.mktemp("fixed_point_stale_tree"))
    target = stale_root / "output" / "data" / "interop_roundtrip_report.json"
    target.unlink()
    assert _validate_fixed_point(stale_root) != []
    # Production default budget: a leg whose floats drift (py3.10) may need a
    # third settlement pass, and an exhausted budget raises instead of degrading.
    paths = run_semantic_fixed_point(stale_root, require_analysis_outputs=False, max_passes=4)
    assert paths, "settlement must report written artifact paths"
    assert target.is_file(), "the deleted artifact must be regenerated"
    assert _validate_fixed_point(stale_root) == []
