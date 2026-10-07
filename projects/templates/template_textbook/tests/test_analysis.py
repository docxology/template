"""Tests for the source-owned worked-example analysis."""

from __future__ import annotations

from pathlib import Path

import pytest

from textbook.analysis import (
    DECAY_PARAMETERS,
    LOGISTIC_PARAMETERS,
    build_worked_model_summary,
    load_case_study_observations,
)

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


def test_case_study_observations_retain_measurements_and_uncertainty() -> None:
    observations = load_case_study_observations(DATASET)

    assert len(observations) == 6
    assert observations[0].condition == "control"
    assert observations[0].replicate == 1
    assert observations[0].measurement == pytest.approx(2.10)
    assert observations[0].standard_error == pytest.approx(0.20)


@pytest.mark.parametrize(
    "contents, message",
    [
        ("condition,replicate,measurement\ncontrol,1,2.1\n", "missing required columns"),
        (
            "condition,replicate,measurement,standard_error\ncontrol,bad,2.1,0.2\n",
            "invalid numeric data",
        ),
        ("condition,replicate,measurement,standard_error\n,1,2.1,0.2\n", "blank condition"),
        (
            "condition,replicate,measurement,standard_error\ncontrol,0,2.1,0.2\n",
            "non-positive replicate",
        ),
        (
            "condition,replicate,measurement,standard_error\ncontrol,1,2.1,-0.2\n",
            "invalid measurement or standard error",
        ),
        (
            "condition,replicate,measurement,standard_error\ncontrol,1,2.1,0.2\ncontrol,1,2.3,0.1\n",
            "duplicate condition/replicate",
        ),
        ("condition,replicate,measurement,standard_error\n", "contains no observations"),
    ],
)
def test_case_study_observations_fail_closed(tmp_path: Path, contents: str, message: str) -> None:
    dataset = tmp_path / "case_study.csv"
    dataset.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_case_study_observations(dataset)


@pytest.mark.parametrize("remove_instructional_evidence", [False, True])
def test_computed_evidence_supports_authored_strict_analysis(
    tmp_path: Path, remove_instructional_evidence: bool
) -> None:
    import json

    from infrastructure.validation.evidence_registry import (
        build_project_evidence_registry,
        validate_text_against_registry,
    )

    summary = build_worked_model_summary(DATASET)
    if remove_instructional_evidence:
        del summary["instructional_examples"]
    data = tmp_path / "output/data/worked_model_summary.json"
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps(summary), encoding="utf-8")
    registry = build_project_evidence_registry(tmp_path)
    target_values = {"-1.4", "17.59", "2.236"}
    unsupported = set()
    for relative in (
        "labs/part_0/lab_orientation.md",
        "labs/part_II/lab_systems_overview.md",
        "labs/part_0/lab_quantitative_foundations.md",
    ):
        passage = PROJECT_ROOT / "manuscript" / relative
        report = validate_text_against_registry(passage.read_text(encoding="utf-8"), registry)
        unsupported.update(issue.value for issue in report.errors if issue.kind == "number")
    assert unsupported & target_values == (target_values if remove_instructional_evidence else set())
