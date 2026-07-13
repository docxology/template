"""Tests for the source-owned worked-example analysis."""

from __future__ import annotations

from pathlib import Path

import pytest

from textbook.analysis import DECAY_PARAMETERS, LOGISTIC_PARAMETERS, build_worked_model_summary

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET = PROJECT_ROOT / "manuscript" / "assets" / "data" / "sample_dataset.csv"


def test_worked_model_summary_retains_inputs_and_outputs() -> None:
    summary = build_worked_model_summary(DATASET)

    assert summary["logistic_growth"]["parameters"] == LOGISTIC_PARAMETERS
    assert summary["exponential_decay"]["parameters"] == DECAY_PARAMETERS
    assert summary["logistic_growth"]["N"][0] == LOGISTIC_PARAMETERS["initial"]
    assert summary["logistic_growth"]["N"][-1] < LOGISTIC_PARAMETERS["carrying_capacity"]
    assert summary["exponential_decay"]["y"][0] == DECAY_PARAMETERS["initial"]
    assert summary["case_study"]["condition_means"] == pytest.approx(
        {
            "control": 2.2,
            "treatment_low": 3.5,
            "treatment_high": 4.95,
        }
    )
    assert round(summary["case_study"]["linear_fit"]["slope"], 3) == 1.375
    assert round(summary["case_study"]["linear_fit"]["r_squared"], 3) == 0.999
    assert round(summary["case_study"]["extrapolation"]["linear_prediction"], 1) == 6.3


def test_worked_model_summary_is_deterministic() -> None:
    assert build_worked_model_summary(DATASET) == build_worked_model_summary(DATASET)


def test_worked_model_summary_accepts_portable_source_provenance() -> None:
    summary = build_worked_model_summary(DATASET, source_label="manuscript/assets/data/sample_dataset.csv")

    assert summary["case_study"]["source"] == "manuscript/assets/data/sample_dataset.csv"
