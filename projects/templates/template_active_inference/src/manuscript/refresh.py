"""Canonical manuscript hydration refresh pipeline."""

from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any
from json_io import write_json


class ManuscriptRefreshPhase(str, Enum):
    PRE_COMPOSE = "pre_compose"
    POST_COMPOSE = "post_compose"


def refresh_manuscript_pipeline(
    root: Path, *, require_analysis_outputs: bool, phase: ManuscriptRefreshPhase
) -> dict[str, Path]:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables
    from roadmap_tracks.integration_audit import write_manuscript_staleness_report

    project_root = root.resolve()
    variables_path = project_root / "output" / "data" / "manuscript_variables.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    if phase is ManuscriptRefreshPhase.PRE_COMPOSE:
        write_json(variables_path, generate_variables(project_root, require_analysis_outputs=require_analysis_outputs))
    compose_all_sections(project_root)
    variables: dict[str, Any] = generate_variables(project_root, require_analysis_outputs=require_analysis_outputs)
    write_json(variables_path, variables)
    return {
        "variables": variables_path,
        "resolved_manuscript": write_resolved_manuscript(project_root, variables),
        "staleness": write_manuscript_staleness_report(project_root),
    }


def settle_manuscript_artifacts(root: Path, *, require_analysis_outputs: bool = False) -> dict[str, Path]:
    return refresh_manuscript_pipeline(
        root, require_analysis_outputs=require_analysis_outputs, phase=ManuscriptRefreshPhase.PRE_COMPOSE
    )
