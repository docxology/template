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
    from visualizations.animation import (
        validate_animation_frame_deltas,
        write_animation_frame_deltas,
        write_belief_trajectory_gif,
    )

    write_graph_world_artifacts(project_root)
    gif_path = write_belief_trajectory_gif(project_root)
    deltas_path = write_animation_frame_deltas(project_root)
    deltas = json.loads(deltas_path.read_text(encoding="utf-8"))

    with Image.open(gif_path) as image:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]

    assert len(frames) >= 3
    assert any(ImageChops.difference(frames[0], frame).getbbox() is not None for frame in frames[1:])
    assert deltas["all_nonzero"] is True
    assert deltas["all_frame_hashes_present"] is True
    assert deltas["all_adjacent_hashes_distinct"] is True
    assert len(deltas["frames"]) == deltas["frame_count"]
    assert all(row["perceptual_hash"] and row["width"] > 0 and row["height"] > 0 for row in deltas["frames"])
    assert all(row["hash_changed"] for row in deltas["rows"])
    assert validate_animation_frame_deltas(project_root) == []


def test_animation_frame_delta_manifest_allows_live_platform_hash_drift(
    monkeypatch,
    project_root: Path,
) -> None:
    from simulation.graph_world import write_graph_world_artifacts
    import visualizations.animation as animation

    write_graph_world_artifacts(project_root)
    animation.write_belief_trajectory_gif(project_root)
    animation.write_animation_frame_deltas(project_root)
    live = animation.build_animation_frame_deltas(project_root)
    drifted_live = json.loads(json.dumps(live))
    for idx, frame in enumerate(drifted_live["frames"], start=1):
        frame["sha256"] = f"{idx:064x}"
        frame["perceptual_hash"] = f"{idx:016x}"
    for idx, row in enumerate(drifted_live["rows"]):
        row["from_perceptual_hash"] = drifted_live["frames"][idx]["perceptual_hash"]
        row["to_perceptual_hash"] = drifted_live["frames"][idx + 1]["perceptual_hash"]
        row["hash_changed"] = True
    monkeypatch.setattr(animation, "build_animation_frame_deltas", lambda project_root: drifted_live)

    assert animation.validate_animation_frame_deltas(project_root) == []


def test_animation_frame_delta_manifest_rejects_static_manifest(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts
    from visualizations.animation import (
        validate_animation_frame_deltas,
        write_animation_frame_deltas,
        write_belief_trajectory_gif,
    )

    write_graph_world_artifacts(project_root)
    write_belief_trajectory_gif(project_root)
    path = write_animation_frame_deltas(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["frames"][1]["perceptual_hash"] = payload["frames"][0]["perceptual_hash"]
        payload["rows"][0]["to_perceptual_hash"] = payload["rows"][0]["from_perceptual_hash"]
        payload["rows"][0]["hash_changed"] = False
        payload["all_adjacent_hashes_distinct"] = True
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_animation_frame_deltas(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert any("duplicate frame hashes" in issue or "stale" in issue for issue in issues)


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


def test_pymdp_runtime_diagnostics_captures_known_warning_and_rejects_unexpected(
    project_root: Path,
) -> None:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.pymdp_runtime import (
        construct_agent_with_diagnostics,
        validate_runtime_diagnostics,
        write_runtime_diagnostics,
    )
    from simulation.tmaze_model import build_tmaze_generative_model, spec_from_config

    cfg = load_pymdp_config(project_root)
    model = build_tmaze_generative_model(cfg)
    spec = spec_from_config(cfg)
    diagnostics_path = project_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    original = diagnostics_path.read_text(encoding="utf-8") if diagnostics_path.is_file() else None

    def noisy_factory(**kwargs):
        import warnings
        from pymdp.agent import Agent

        warnings.warn("unexpected agent construction warning", UserWarning, stacklevel=2)
        return Agent(**kwargs)

    try:
        _, record = construct_agent_with_diagnostics(
            project_root,
            config=cfg,
            model=model,
            policy_len=spec.policy_len,
            context="negative_control",
            agent_factory=noisy_factory,
        )
        path = write_runtime_diagnostics(project_root, [record])
        payload = json.loads(path.read_text(encoding="utf-8"))

        assert payload["known_warning_count"] >= 1
        assert payload["unexpected_warning_count"] == 1
        assert {"construction", "inference", "backend", "warning", "fallback"} <= set(payload["phase_types"])
        assert payload["all_phase_rows_ok"] is False
        assert any("unexpected warning" in issue for issue in validate_runtime_diagnostics(project_root))
    finally:
        if original is None:
            diagnostics_path.unlink(missing_ok=True)
        else:
            diagnostics_path.write_text(original, encoding="utf-8")


def test_policy_comparison_uses_configured_grid_and_writes_posterior_rows(project_root: Path) -> None:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    cfg = load_pymdp_config(project_root)
    path = write_policy_comparison(project_root)
    grid_path = write_policy_posterior_grid(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    posterior = json.loads(grid_path.read_text(encoding="utf-8"))

    assert payload["summary"]["modes"] == sorted(cfg.comparison.modes)
    assert payload["summary"]["horizons"] == sorted(cfg.comparison.horizons)
    assert payload["summary"]["seeds"] == sorted(cfg.comparison.seeds)
    assert payload["summary"]["run_count"] == (
        len(cfg.comparison.modes) * len(cfg.comparison.horizons) * len(cfg.comparison.seeds)
    )
    assert posterior["schema"] == "template_active_inference.pymdp_policy_posterior_grid.v1"
    assert posterior["row_count"] >= 1
    assert posterior["all_available_posteriors_normalized"] is True


def test_validate_outputs_rejects_unnormalized_policy_posterior(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    write_policy_comparison(project_root)
    path = write_policy_posterior_grid(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        row = next(row for row in payload["rows"] if row["posterior_available"])
        row["q_pi"] = [0.8, 0.8]
        row["q_pi_sum"] = 1.6
        row["normalized"] = False
        payload["all_available_posteriors_normalized"] = False
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["pymdp_policy_posterior_grid_schema"] is False
