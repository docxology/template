"""Shared I/O for analytical parameter sweep CSV artifacts."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np


def read_parameter_sweep(path: Path) -> list[dict[str, float]]:
    """Read ``parameter_sweep.csv`` rows as floats."""
    if not path.is_file():
        return []
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "lambda": float(row["lambda"]),
                    "closed_form_mi": float(row["closed_form_mi"]),
                    "empirical_mi": float(row["empirical_mi"]),
                }
            )
    return rows


def summarize_sweep_rows(rows: list[dict[str, float]]) -> dict[str, Any]:
    """Summarize sweep residuals and grid size from parsed rows."""
    if not rows:
        return {"max_residual": 0.0, "rmse_mi": 0.0, "argmax_lambda": 0.0, "grid_points": 0}
    lambdas = [row["lambda"] for row in rows]
    closed = [row["closed_form_mi"] for row in rows]
    empirical = [row["empirical_mi"] for row in rows]
    residuals = [abs(e - c) for e, c in zip(empirical, closed, strict=True)]
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    argmax_idx = int(np.argmax(empirical))
    return {
        "max_residual": float(max(residuals)),
        "rmse_mi": rmse,
        "argmax_lambda": float(lambdas[argmax_idx]),
        "grid_points": len(lambdas),
    }


def summarize_sweep_file(path: Path) -> dict[str, Any]:
    """Summarize sweep statistics from a CSV path."""
    return summarize_sweep_rows(read_parameter_sweep(path))
