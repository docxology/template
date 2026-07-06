"""Deterministic artifact-refresh helpers used before semantic certificate writes."""

from __future__ import annotations

import json
from pathlib import Path


def _refresh_hydrated_manuscript(root: Path) -> None:
    from manuscript.refresh import ManuscriptRefreshPhase, refresh_manuscript_pipeline

    refresh_manuscript_pipeline(root, require_analysis_outputs=False, phase=ManuscriptRefreshPhase.POST_COMPOSE)


def _refresh_artifact_contract_outputs(root: Path) -> None:
    """Refresh contract artifacts that hash semantic outputs after final writes."""
    from roadmap_tracks.integration_audit import write_integration_audit_artifacts
    from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS, build_artifact_contract_index, build_replay_matrix

    write_integration_audit_artifacts(root)
    replay_path = root / CANONICAL_ARTIFACTS["replay_matrix"]
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    replay_path.write_text(
        json.dumps(build_replay_matrix(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contract_path = root / CANONICAL_ARTIFACTS["artifact_contract_index"]
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(build_artifact_contract_index(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refresh_animation_outputs(root: Path) -> None:
    """Refresh deterministic animation artifacts before semantic validation."""
    from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif

    try:
        write_belief_trajectory_gif(root)
        write_animation_frame_deltas(root)
    except FileNotFoundError:
        return
