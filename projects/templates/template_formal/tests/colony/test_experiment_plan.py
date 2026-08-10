"""Contract tests for the typed, source-owned ablation plan."""

from __future__ import annotations

from pathlib import Path

import pytest

from template_formal.colony.experiment_plan import (
    REQUIRED_ABLATION_PARAMETERS,
    load_experiment_plan,
    validate_experiment_plan,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_live_plan_covers_every_required_trial_axis() -> None:
    plan = load_experiment_plan(PROJECT_ROOT / "experiment_plan.yaml")
    assert plan.parameters == REQUIRED_ABLATION_PARAMETERS
    assert all(axis.values and axis.negative_control for axis in plan.axes)


@pytest.mark.parametrize(
    "value",
    [
        [{"name": "bad", "parameter": "not_a_trial_field", "values": [1], "negative_control": "x"}],
        [{"name": "missing-values", "parameter": "decay", "values": [], "negative_control": "x"}],
    ],
)
def test_plan_rejects_unknown_or_empty_axis_data(value: object) -> None:
    raw = {
        "schema_version": 1,
        "ablation_axes": value,
    }
    with pytest.raises(ValueError):
        validate_experiment_plan(raw)


def test_plan_rejects_omitted_required_axis() -> None:
    raw = {
        "schema_version": 1,
        "ablation_axes": [
            {
                "name": "only-decay",
                "parameter": "decay",
                "values": [0.46],
                "negative_control": "baseline comparison",
            }
        ],
    }
    with pytest.raises(ValueError, match="omits required ablation"):
        validate_experiment_plan(raw)
