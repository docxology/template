"""Analysis orchestration: parameter sweeps and artifact writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from analytical.bernoulli_toy import empirical_mutual_information, ising_mutual_information
from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.invariants import run_invariants
from simulation.pymdp_config import config_hash, load_pymdp_config
from simulation.statistics import load_si_artifacts, summarize_si_trace


def write_parameter_sweep(project_root: Path) -> Path:
    root = project_root.resolve()
    out = root / "output" / "data" / "parameter_sweep.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    hp = load_hyperparameters()
    rows: list[dict[str, float]] = []
    for lam in lambda_grid(hp):
        rows.append(
            {
                "lambda": lam,
                "closed_form_mi": ising_mutual_information(lam),
                "empirical_mi": empirical_mutual_information(lam),
            }
        )
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lambda", "closed_form_mi", "empirical_mi"])
        writer.writeheader()
        writer.writerows(rows)
    return out


def write_invariants_report(
    project_root: Path,
    results: dict[str, bool] | None = None,
) -> Path:
    root = project_root.resolve()
    out = root / "output" / "reports" / "invariants.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    from simulation.invariants import build_merged_invariants_payload

    payload = build_merged_invariants_payload(root, analytical_results=results)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def summarize_sweep(csv_path: Path) -> dict[str, Any]:
    if not csv_path.exists():
        return {"max_residual": 0.0, "rmse_mi": 0.0, "argmax_lambda": 0.0, "grid_points": 0}
    lambdas: list[float] = []
    closed: list[float] = []
    empirical: list[float] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lambdas.append(float(row["lambda"]))
            closed.append(float(row["closed_form_mi"]))
            empirical.append(float(row["empirical_mi"]))
    if not lambdas:
        return {"max_residual": 0.0, "rmse_mi": 0.0, "argmax_lambda": 0.0, "grid_points": 0}
    residuals = [abs(e - c) for e, c in zip(empirical, closed, strict=True)]
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    argmax_idx = int(np.argmax(empirical))
    return {
        "max_residual": float(max(residuals)),
        "rmse_mi": rmse,
        "argmax_lambda": float(lambdas[argmax_idx]),
        "grid_points": len(lambdas),
    }


def write_analysis_statistics(project_root: Path) -> Path:
    root = project_root.resolve()
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    summary, trace = load_si_artifacts(root)
    cfg = load_pymdp_config(root)
    payload = {
        "sweep": summarize_sweep(sweep_path),
        "si_tmaze": summarize_si_trace(trace, summary),
        "pymdp_mode": summary.get("mode", cfg.mode),
        "pymdp_config_hash": summary.get("config_hash", config_hash(cfg)),
    }
    out = root / "output" / "data" / "analysis_statistics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def run_analysis(project_root: Path) -> dict[str, Path]:
    inv_results = run_invariants()
    return {
        "parameter_sweep": write_parameter_sweep(project_root),
        "invariants": write_invariants_report(project_root, inv_results),
    }
