"""Deterministic worked-example analysis used by the textbook pipeline."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

import numpy as np

from textbook import models

LOGISTIC_PARAMETERS = {"r": 0.8, "carrying_capacity": 100.0, "initial": 5.0}
DECAY_PARAMETERS = {"initial": 100.0, "rate": 0.5}
LOGISTIC_SENSITIVITY_RATES = (0.4, 0.8, 1.2)


@dataclass(frozen=True)
class CaseStudyObservation:
    """One source-bound observation in the worked case-study dataset."""

    condition: str
    replicate: int
    measurement: float
    standard_error: float


def load_case_study_observations(dataset_path: Path) -> tuple[CaseStudyObservation, ...]:
    """Load and validate the observations shared by the analysis and figure."""
    required_fields = {"condition", "replicate", "measurement", "standard_error"}
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_fields = required_fields - set(reader.fieldnames or ())
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"case-study dataset is missing required columns: {missing}")
        rows = list(reader)

    observations: list[CaseStudyObservation] = []
    seen_keys: set[tuple[str, int]] = set()
    for row_number, row in enumerate(rows, start=2):
        condition = (row.get("condition") or "").strip()
        try:
            replicate = int(row["replicate"])
            measurement = float(row["measurement"])
            standard_error = float(row["standard_error"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"case-study dataset row {row_number} contains invalid numeric data") from exc
        if not condition:
            raise ValueError(f"case-study dataset row {row_number} has a blank condition")
        if replicate < 1:
            raise ValueError(f"case-study dataset row {row_number} has a non-positive replicate")
        if not isfinite(measurement) or not isfinite(standard_error) or standard_error < 0:
            raise ValueError(f"case-study dataset row {row_number} has an invalid measurement or standard error")
        key = (condition, replicate)
        if key in seen_keys:
            raise ValueError(f"case-study dataset has duplicate condition/replicate row: {condition}/{replicate}")
        seen_keys.add(key)
        observations.append(
            CaseStudyObservation(
                condition=condition,
                replicate=replicate,
                measurement=measurement,
                standard_error=standard_error,
            )
        )
    if not observations:
        raise ValueError("case-study dataset contains no observations")
    return tuple(observations)


def _build_case_study_summary(dataset_path: Path, *, source_label: str | None = None) -> dict[str, Any]:
    observations = load_case_study_observations(dataset_path)
    groups: dict[str, list[float]] = {}
    for observation in observations:
        groups.setdefault(observation.condition, []).append(observation.measurement)

    condition_order = ("control", "treatment_low", "treatment_high")
    means = {condition: float(np.mean(groups[condition])) for condition in condition_order}
    response = np.array([means[condition] for condition in condition_order])
    dose = np.arange(len(condition_order), dtype=float)
    fit = models.linear_fit(dose, response)
    all_measurements = np.array([observation.measurement for observation in observations])
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
