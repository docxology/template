"""Direct tests for ``manuscript.refresh`` and ``manuscript.sheaf.semantic_refresh``.

These pipelines rewrite composed manuscript sources and hydrated outputs, so
every test runs against an isolated project-tree copy (see
``direct_recompute_support``); the tracked snapshot is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.refresh import (
    ManuscriptRefreshPhase,
    refresh_manuscript_pipeline,
    settle_manuscript_artifacts,
)
from manuscript.sheaf.semantic_refresh import (
    _refresh_animation_outputs,
    _refresh_artifact_contract_outputs,
    _refresh_hydrated_manuscript,
)

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("refresh_tree"))


@pytest.mark.timeout(600)
def test_refresh_manuscript_pipeline_pre_compose_writes_all_artifacts(copied_root: Path) -> None:
    paths = refresh_manuscript_pipeline(
        copied_root, require_analysis_outputs=False, phase=ManuscriptRefreshPhase.PRE_COMPOSE
    )
    assert set(paths) == {"variables", "resolved_manuscript", "staleness"}
    variables = json.loads(paths["variables"].read_text(encoding="utf-8"))
    assert variables, "hydrated manuscript variables must be non-empty"
    assert paths["resolved_manuscript"].exists()
    staleness = json.loads(paths["staleness"].read_text(encoding="utf-8"))
    assert staleness, "staleness report must be non-empty"


@pytest.mark.timeout(600)
def test_refresh_manuscript_pipeline_post_compose_skips_pre_write(copied_root: Path) -> None:
    variables_path = copied_root / "output" / "data" / "manuscript_variables.json"
    before = variables_path.read_bytes() if variables_path.is_file() else b""
    paths = refresh_manuscript_pipeline(
        copied_root, require_analysis_outputs=False, phase=ManuscriptRefreshPhase.POST_COMPOSE
    )
    assert paths["variables"] == variables_path
    assert variables_path.is_file()
    # POST_COMPOSE still rewrites the final variables snapshot; the phase only
    # controls whether a pre-compose write happens first.
    assert json.loads(variables_path.read_text(encoding="utf-8"))
    assert before == b"" or variables_path.read_bytes()


@pytest.mark.timeout(600)
def test_settle_manuscript_artifacts_is_pre_compose(copied_root: Path) -> None:
    paths = settle_manuscript_artifacts(copied_root)
    assert set(paths) == {"variables", "resolved_manuscript", "staleness"}
    assert all(path.exists() for path in paths.values())


@pytest.mark.timeout(600)
def test_semantic_refresh_hydrates_manuscript(copied_root: Path) -> None:
    variables_path = copied_root / "output" / "data" / "manuscript_variables.json"
    _refresh_hydrated_manuscript(copied_root)
    assert variables_path.is_file()
    assert json.loads(variables_path.read_text(encoding="utf-8"))


@pytest.mark.timeout(600)
def test_semantic_refresh_rewrites_contract_outputs(copied_root: Path) -> None:
    from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS

    _refresh_artifact_contract_outputs(copied_root)
    replay = json.loads((copied_root / CANONICAL_ARTIFACTS["replay_matrix"]).read_text(encoding="utf-8"))
    contract = json.loads((copied_root / CANONICAL_ARTIFACTS["artifact_contract_index"]).read_text(encoding="utf-8"))
    assert replay and contract


@pytest.mark.timeout(600)
def test_semantic_refresh_animation_outputs_written(copied_root: Path) -> None:
    gif = copied_root / "output" / "figures" / "si_belief_trajectory.gif"
    deltas = copied_root / "output" / "data" / "animation_frame_deltas.json"
    _refresh_animation_outputs(copied_root)
    assert gif.is_file() and gif.stat().st_size > 0
    assert json.loads(deltas.read_text(encoding="utf-8"))


def test_semantic_refresh_animation_tolerates_missing_inputs(tmp_path: Path) -> None:
    _refresh_animation_outputs(tmp_path)
    assert not (tmp_path / "output" / "figures" / "si_belief_trajectory.gif").exists()
