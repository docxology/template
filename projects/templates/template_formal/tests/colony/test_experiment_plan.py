"""Contract tests for the typed, source-owned ablation plan."""

from __future__ import annotations

from pathlib import Path
import copy

import pytest
import yaml

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


@pytest.mark.parametrize(
    "mutation,diagnostic",
    [
        ("not-mapping", "experiment plan must be a mapping"),
        ("boolean-version", "unsupported experiment plan schema_version"),
        ("retired-version", "unsupported experiment plan schema_version"),
        ("scalar-axes", "ablation_axes must be a non-empty sequence"),
        ("empty-axes", "ablation_axes must be a non-empty sequence"),
        ("scalar-axis", "must be a mapping"),
        ("empty-name", "name must be a non-empty string"),
        ("duplicate-name", "duplicate ablation axis name"),
        ("duplicate-parameter", "duplicate ablation parameter"),
        ("empty-control", "negative_control must be a non-empty string"),
        ("boolean-value", "must contain only numbers"),
        ("duplicate-value", "must not contain duplicate values"),
        ("scalar-values", "must be a non-empty sequence"),
    ],
)
def test_declared_plan_rejects_ambiguous_registration_inputs(mutation: str, diagnostic: str) -> None:
    raw = yaml.safe_load((PROJECT_ROOT / "experiment_plan.yaml").read_text())
    axis = raw["ablation_axes"][0]
    if mutation == "not-mapping":
        raw = []
    elif mutation in {"boolean-version", "retired-version"}:
        raw["schema_version"] = True if mutation == "boolean-version" else 0
    elif mutation in {"scalar-axes", "empty-axes"}:
        raw["ablation_axes"] = "axis" if mutation == "scalar-axes" else []
    elif mutation == "scalar-axis":
        raw["ablation_axes"][0] = "axis"
    elif mutation == "empty-name":
        axis["name"] = " "
    elif mutation in {"duplicate-name", "duplicate-parameter"}:
        duplicate = copy.deepcopy(axis)
        if mutation == "duplicate-parameter":
            duplicate["name"] = "distinct-control-with-duplicate-parameter"
        raw["ablation_axes"].append(duplicate)
    elif mutation == "empty-control":
        axis["negative_control"] = " "
    elif mutation == "boolean-value":
        axis["values"] = [True]
    elif mutation == "duplicate-value":
        axis["values"] = [1.0, 1.0]
    else:
        axis["values"] = "1.0"
    with pytest.raises(ValueError, match=diagnostic):
        validate_experiment_plan(raw)
