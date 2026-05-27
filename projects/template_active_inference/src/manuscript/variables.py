"""Manuscript variable generation from measured project outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from analytical.hyperparameters import load_hyperparameters
from analytical.invariants import run_invariants
from simulation.pymdp_config import load_pymdp_config


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _pipeline_track_count(project_root: Path) -> int:
    """Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``)."""
    tracks_path = project_root / "tracks.yaml"
    if not tracks_path.is_file():
        return 0
    raw = yaml.safe_load(tracks_path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return sum(1 for track in tracks if track.get("required", True))


def _ising_mi_saturation_from_sweep(sweep_rows: list[dict[str, str]]) -> float:
    """Maximum closed-form MI on the measured λ grid (nats)."""
    if not sweep_rows:
        return 0.0
    return max(float(row["closed_form_mi"]) for row in sweep_rows)


def _invariant_counts(project_root: Path) -> tuple[int, int]:
    """Passed/total from merged invariants report when present, else live analytical run."""
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.is_file():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        analytical = data.get("invariants") or {}
        simulation = data.get("simulation") or {}
        if not simulation:
            si_inv_path = root / "output" / "reports" / "si_invariants.json"
            if si_inv_path.is_file():
                si_data = json.loads(si_inv_path.read_text(encoding="utf-8"))
                simulation = si_data.get("invariants") or {}
        combined = {**analytical, **simulation}
        if combined:
            return sum(1 for value in combined.values() if value), len(combined)
    inv = run_invariants()
    return sum(1 for value in inv.values() if value), len(inv)


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = True) -> dict[str, Any]:
    root = project_root.resolve()
    hp = load_hyperparameters()
    pymdp_cfg = load_pymdp_config(root)
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    stats_path = root / "output" / "data" / "analysis_statistics.json"
    inv_passed, inv_total = _invariant_counts(root)

    if require_analysis_outputs and not sweep_path.exists():
        raise FileNotFoundError(f"missing analysis artifact: {sweep_path}")

    sweep_rows = _read_csv_rows(sweep_path)
    si_data = _load_json(si_summary)
    stats_data = _load_json(stats_path)
    si_stats = stats_data.get("si_tmaze") or {}
    sweep_stats = stats_data.get("sweep") or {}

    mean_entropy = float(si_data.get("mean_belief_entropy", si_stats.get("entropy_mean", 0.0)))
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    return {
        "project_name": root.name,
        "lambda_grid_points": hp.lambda_grid_points,
        "lambda_max": hp.lambda_max,
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
        "pipeline_track_count": _pipeline_track_count(root),
        **counts,
    }
