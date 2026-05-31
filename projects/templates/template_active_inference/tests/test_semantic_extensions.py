"""Semantic extension artifact tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageSequence


def test_validate_all_gnn_ontology_covers_si_tmaze(project_root: Path) -> None:
    from ontology.bindings import validate_all_gnn_ontology

    assert validate_all_gnn_ontology(project_root) == []

    gnn_path = project_root / "gnn" / "si_tmaze.gnn.md"
    original = gnn_path.read_text(encoding="utf-8")
    try:
        gnn_path.write_text(original.replace("pi=PolicyPosterior", "pi=HiddenState"), encoding="utf-8")
        gaps = validate_all_gnn_ontology(project_root)
        assert any("si_tmaze" in gap and "PolicyPosterior" in gap for gap in gaps)
    finally:
        gnn_path.write_text(original, encoding="utf-8")


def test_validate_all_gnn_ontology_rejects_extra_section_alias(project_root: Path) -> None:
    from ontology.bindings import validate_all_gnn_ontology

    ontology_path = project_root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml"
    original = ontology_path.read_text(encoding="utf-8")
    try:
        ontology_path.write_text(original + "\nalien_alias: HiddenState\n", encoding="utf-8")
        gaps = validate_all_gnn_ontology(project_root)
    finally:
        ontology_path.write_text(original, encoding="utf-8")

    assert any("alien_alias" in gap for gap in gaps)


@pytest.mark.requires_pymdp
def test_policy_comparison_artifact_records_modes_horizons_and_seeds(project_root: Path) -> None:
    from simulation.si_runner import pymdp_available
    from simulation.si_artifacts import write_policy_comparison

    if not pymdp_available():
        pytest.skip("pymdp not installed")

    path = write_policy_comparison(project_root, horizons=(2, 3), seeds=(0,))
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.relative_to(project_root).as_posix() == "output/data/si_policy_comparison.json"
    assert {row["mode"] for row in payload["runs"]} == {"state_inference", "policy_inference"}
    assert {row["horizon"] for row in payload["runs"]} == {2, 3}
    assert all("goal_reached" in row and "mean_belief_entropy" in row for row in payload["runs"])
    assert payload["summary"]["run_count"] == 4


def test_graph_world_extension_writes_real_summary_and_trace(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts

    paths = write_graph_world_artifacts(project_root)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))

    assert summary["status"] == "ok"
    assert summary["node_count"] >= 4
    assert summary["goal_reached"] is True
    assert trace["steps"]
    assert "not_implemented" not in json.dumps(summary)


def test_animation_extension_renders_distinct_trace_frames(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts
    from visualizations.animation import write_belief_trajectory_gif

    write_graph_world_artifacts(project_root)
    gif_path = write_belief_trajectory_gif(project_root)

    with Image.open(gif_path) as image:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]

    assert len(frames) >= 3
    assert any(ImageChops.difference(frames[0], frame).getbbox() is not None for frame in frames[1:])


def test_validate_outputs_rejects_graph_world_summary_trace_mismatch(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.graph_world import write_graph_world_artifacts

    paths = write_graph_world_artifacts(project_root)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    original = paths["summary"].read_text(encoding="utf-8")
    try:
        summary["steps"] = 999
        paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        paths["summary"].write_text(original, encoding="utf-8")

    assert checks["si_graph_world_schema"] is False
