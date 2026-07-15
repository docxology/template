"""Deterministic worked-example analysis used by the textbook pipeline."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

from textbook import models

LOGISTIC_PARAMETERS = {"r": 0.8, "carrying_capacity": 100.0, "initial": 5.0}
DECAY_PARAMETERS = {"initial": 100.0, "rate": 0.5}
LOGISTIC_SENSITIVITY_RATES = (0.4, 0.8, 1.2)


def _build_case_study_summary(dataset_path: Path, *, source_label: str | None = None) -> dict[str, Any]:
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["condition"], []).append(float(row["measurement"]))

    condition_order = ("control", "treatment_low", "treatment_high")
    means = {condition: float(np.mean(groups[condition])) for condition in condition_order}
    response = np.array([means[condition] for condition in condition_order])
    dose = np.arange(len(condition_order), dtype=float)
    fit = models.linear_fit(dose, response)
    all_measurements = np.array([float(row["measurement"]) for row in rows])
    extrapolation_dose = 3.0
    return {
        "source": source_label or dataset_path.as_posix(),
        "condition_means": means,
        "overall": models.descriptive_statistics(all_measurements),
        "linear_fit": {
            "slope": fit.slope,
            "intercept": fit.intercept,
            "r_squared": fit.r_squared,
        },
        "extrapolation": {
            "dose": extrapolation_dose,
            "linear_prediction": fit.slope * extrapolation_dose + fit.intercept,
        },
    }


def build_worked_model_summary(dataset_path: Path, *, source_label: str | None = None) -> dict[str, Any]:
    """Compute canonical examples with clone-independent input provenance."""
    time = np.linspace(0, 10, 11)
    growth = models.logistic_growth(time, **LOGISTIC_PARAMETERS)
    decay = models.exponential_decay(time, **DECAY_PARAMETERS)
    return {
        "logistic_growth": {
            "parameters": dict(LOGISTIC_PARAMETERS),
            "sensitivity_rates": list(LOGISTIC_SENSITIVITY_RATES),
            "unfilled_capacity_percent_at_final_time": (
                (LOGISTIC_PARAMETERS["carrying_capacity"] - float(growth[-1]))
                / LOGISTIC_PARAMETERS["carrying_capacity"]
                * 100
            ),
            "t": time.tolist(),
            "N": growth.tolist(),
            "stats": models.descriptive_statistics(growth),
        },
        "exponential_decay": {
            "parameters": dict(DECAY_PARAMETERS),
            "t": time.tolist(),
            "y": decay.tolist(),
            "half_life": models.half_life(DECAY_PARAMETERS["rate"]),
        },
        "case_study": _build_case_study_summary(dataset_path, source_label=source_label),
    }
