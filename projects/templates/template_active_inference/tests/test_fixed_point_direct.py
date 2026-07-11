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


@pytest.mark.timeout(600)
def test_unfixable_source_defect_raises_instead_of_converging(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Negative control: the fixed point must FAIL, not launder, an unfixable defect.

    Corrupting a SOURCE contract (an ontology annotation with no variable
    declaration in a tracked GNN model) means every settlement pass rebuilds
    artifacts that still fail validation — writers regenerate outputs from the
    corrupted source, so no number of passes can converge. A fixed point that
    returned successfully here would be green-by-construction. (First version
    of this control exposed exactly that: validation bound only to SAVED
    artifacts, so the corrupted source fast-pathed straight through — closed
    by the saved-vs-live gnn_lint staleness check in
    validate_formal_interop_artifacts.)
    """
    broken_root = copy_project_tree(tmp_path_factory.mktemp("fixed_point_broken_tree"))
    gnn_model = broken_root / "gnn" / "si_tmaze.gnn.md"
    gnn_model.write_text(
        gnn_model.read_text(encoding="utf-8") + "\nghost_variable=FabricatedOntologyTerm\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="semantic fixed point"):
        run_semantic_fixed_point(broken_root, require_analysis_outputs=False, max_passes=2)
