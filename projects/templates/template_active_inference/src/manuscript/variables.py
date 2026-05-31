"""Manuscript variable generation from measured project outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from analytical.hyperparameters import load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from manuscript.invariant_counts import load_invariant_counts
from simulation.pymdp_config import load_pymdp_config


def _ising_mi_saturation_from_sweep(sweep_rows: list[dict[str, float]]) -> float:
    """Maximum closed-form MI on the measured λ grid (nats)."""
    if not sweep_rows:
        return 0.0
    return max(row["closed_form_mi"] for row in sweep_rows)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _pipeline_track_count(project_root: Path) -> int:
    """Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``)."""
    tracks_path = project_root / "tracks.yaml"
    if not tracks_path.is_file():
        return 0
    raw = yaml.safe_load(tracks_path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return sum(1 for track in tracks if track.get("required", True))


def _gnn_spec_version(project_root: Path) -> str:
    path = project_root / "gnn" / "bernoulli_toy.gnn.md"
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "## GNNVersionAndFlags":
            continue
        for follow in lines[idx + 1 :]:
            text = follow.strip()
            if not text:
                continue
            return text
    return ""


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = True) -> dict[str, Any]:
    root = project_root.resolve()
    hp = load_hyperparameters()
    pymdp_cfg = load_pymdp_config(root)
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    stats_path = root / "output" / "data" / "analysis_statistics.json"
    inv_passed, inv_total = load_invariant_counts(root)

    if require_analysis_outputs and not sweep_path.exists():
        raise FileNotFoundError(f"missing analysis artifact: {sweep_path}")

    sweep_rows = read_parameter_sweep(sweep_path)
    si_data = _load_json(si_summary)
    stats_data = _load_json(stats_path)
    policy_data = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    graph_data = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    provenance_data = _load_json(root / "output" / "data" / "artifact_provenance.json")
    replay_data = _load_json(root / "output" / "reports" / "reproducibility_replay.json")
    counterexample_data = _load_json(root / "output" / "reports" / "counterexample_matrix.json")
    si_stats = stats_data.get("si_tmaze") or {}
    sweep_stats = stats_data.get("sweep") or {}
    policy_summary = policy_data.get("summary") or {}

    mean_entropy = float(si_data.get("mean_belief_entropy", si_stats.get("entropy_mean", 0.0)))
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    return {
        "project_name": root.name,
        "lambda_grid_points": hp.lambda_grid_points,
        "lambda_max": hp.lambda_max,
        "bernoulli_state_count": hp.bernoulli_state_count,
        "gnn_spec_version": _gnn_spec_version(root),
        "pymdp_horizon": pymdp_cfg.horizon,
        "random_seed": pymdp_cfg.random_seed,
        "param_sweep_grid_points": len(sweep_rows) or hp.lambda_grid_points,
        "ising_mi_saturation": _ising_mi_saturation_from_sweep(sweep_rows),
        "invariants_passed": inv_passed,
        "invariants_total": inv_total,
        "si_tmaze_steps": si_data.get("steps", si_stats.get("steps", 0)),
        "si_tmaze_policy_len": si_data.get("policy_len", pymdp_cfg.policy_len),
        "si_tmaze_mean_belief_entropy": mean_entropy,
        "si_tmaze_mean_belief_entropy_formatted": f"{mean_entropy:.4f}",
        "si_goal_reached": int(bool(si_data.get("goal_reached", si_stats.get("goal_reached", False)))),
        "si_action_diversity": si_data.get("action_diversity", si_stats.get("action_diversity", 0)),
        "si_entropy_min": si_stats.get("entropy_min", 0.0),
        "si_entropy_max": si_stats.get("entropy_max", 0.0),
        "sweep_max_residual": sweep_stats.get("max_residual", 0.0),
        "sweep_rmse_mi": sweep_stats.get("rmse_mi", 0.0),
        "pymdp_mode": stats_data.get("pymdp_mode", si_data.get("mode", pymdp_cfg.mode)),
        "pymdp_config_hash": stats_data.get("pymdp_config_hash", si_data.get("config_hash", "")),
        "si_policy_comparison_run_count": policy_summary.get("run_count", 0),
        "si_policy_comparison_goal_reached_count": policy_summary.get("goal_reached_count", 0),
        "si_graph_world_steps": graph_data.get("steps", 0),
        "si_graph_world_node_count": graph_data.get("node_count", 0),
        "si_graph_world_goal_reached": int(bool(graph_data.get("goal_reached", False))),
        "validation_spine_artifact_count": provenance_data.get("artifact_count", 0),
        "reproducibility_check_count": replay_data.get("check_count", 0),
        "reproducibility_all_passed": int(bool(replay_data.get("all_passed", False))),
        "counterexample_count": counterexample_data.get("counterexample_count", 0),
        "pipeline_track_count": _pipeline_track_count(root),
        **counts,
    }
