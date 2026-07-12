"""Real artifact integration test for the source-owned analysis service."""

from __future__ import annotations

import json
from pathlib import Path

from template_formal.colony.analysis import SWEEP_NUM_TRIALS, run_publication_analysis


def test_publication_analysis_writes_complete_real_artifact_set(tmp_path: Path) -> None:
    project_root = tmp_path / "formal"
    artifacts = run_publication_analysis(project_root)

    assert all(path.is_file() and path.stat().st_size > 0 for path in artifacts.paths)
    assert len(artifacts.demo_databases) == 3

    sweep = json.loads(artifacts.sweep_summary.read_text(encoding="utf-8"))
    assert sweep["num_trials"] == SWEEP_NUM_TRIALS
    assert sweep["successes"] == 37
    assert len(sweep["consensus_ticks"]) == SWEEP_NUM_TRIALS

    registry = json.loads(artifacts.figure_registry.read_text(encoding="utf-8"))
    assert set(registry) == {"fig:demo-convergence", "fig:convergence-tick-distribution"}
    assert {entry["filename"] for entry in registry.values()} == {
        artifacts.demo_figure.name,
        artifacts.sweep_figure.name,
    }
