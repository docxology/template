"""Finite actual report/temporal DATA controls; no fabricated native owner."""

from __future__ import annotations

import copy
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_code_stability_domain import (
    HYDRATION,
    PROJECT,
    REPORT,
    SRC,
    STABILITY_KEYS,
    VARIABLES,
    _registered_report_origin,
    validate_sdk_stability_report,
)
from infrastructure.reporting.native_code_value_predicate import ScalarQuadraticConfig
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _config(points: tuple[float, ...] = (1e5, 100001.0, 5e-6, 0.0, 1e8)) -> ScalarQuadraticConfig:
    # For A=2, b=0 the objective is x*x. The fifth configured point must not
    # affect the Source-selected first-four score, unlike a full grid sweep.
    return ScalarQuadraticConfig((0.5,), 2.0, 0.0, 1.0, 2, 1e-6, 1e-6, points, (0.1,), (1,))


def _report(score: float = 0.65) -> dict:
    return {
        "function_name": "quadratic_function",
        "stability_score": score,
        "expected_behavior": "Stable numerical behavior across input range",
        "actual_behavior": f"Stability score: {score:.2f}",
        "recommendations": ["Consider adding input validation and error handling"] if score < 0.8 else [],
    }


def test_configured_first_four_objective_score_and_formatter() -> None:
    variables = {"STABILITY_SCORE": "0.65", "STABILITY_FUNCTION": "quadratic_function"}
    assert (
        validate_sdk_stability_report(_config(), _report(), variables, STABILITY_KEYS, deadline=time.monotonic() + 10)
        == variables
    )


@pytest.mark.parametrize("point,score", [(1e5, 1.0), (100001.0, 0.3), (5e-6, 0.3), (0.0, 1.0)])
def test_exact_large_near_underflow_and_zero_boundaries(point: float, score: float) -> None:
    values = {"STABILITY_SCORE": f"{score:.2f}", "STABILITY_FUNCTION": "quadratic_function"}
    assert (
        validate_sdk_stability_report(
            _config((point,)), _report(score), values, STABILITY_KEYS, deadline=time.monotonic() + 10
        )
        == values
    )


@pytest.mark.parametrize("mutation", ["score", "function", "behavior", "recommendation", "fallback", "extra"])
def test_report_mutations_and_gradient_descent_fallback_refuse(mutation: str) -> None:
    report = _report()
    if mutation == "score":
        report["stability_score"] = 1.0
    elif mutation == "function":
        report["function_name"] = "another_function"
    elif mutation == "behavior":
        report["actual_behavior"] = "Stable"
    elif mutation == "recommendation":
        report["recommendations"] = []
    elif mutation == "fallback":
        report["expected_behavior"] = "Converge to f(x*)=0 for all starting points"
    else:
        report["undocumented"] = True
    with pytest.raises(ValueError, match="SDK objective-stability"):
        validate_sdk_stability_report(
            _config(),
            report,
            {"STABILITY_SCORE": "0.65"},
            frozenset({"STABILITY_SCORE"}),
            deadline=time.monotonic() + 10,
        )


def test_selected_formatted_payload_drift_refuses() -> None:
    with pytest.raises(ValueError, match="report formatter"):
        validate_sdk_stability_report(
            _config(),
            _report(),
            {"STABILITY_SCORE": "0.650"},
            frozenset({"STABILITY_SCORE"}),
            deadline=time.monotonic() + 10,
        )


def test_finite_inputs_whose_objective_overflows_refuse() -> None:
    with pytest.raises(ValueError, match="finite configured objective"):
        validate_sdk_stability_report(
            _config((1e308,)),
            _report(),
            {"STABILITY_SCORE": "0.65"},
            frozenset({"STABILITY_SCORE"}),
            deadline=time.monotonic() + 10,
        )


def _temporal_data(root: Path) -> tuple:
    # Real public-policy SnapshotReader paths bind DATA bodies. This fixture
    # does not authenticate a NativeStage/NativeOwner or count as native proof.
    names = ("manuscript/config.yaml", REPORT, VARIABLES)
    for name, body in zip(names, (b"experiment: {}\n", b"{}", b"{}"), strict=True):
        path = root / PROJECT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    reader = SnapshotReader(root)
    config, report, variables = (reader.read(PROJECT + "/" + name) for name in names)
    read_config = {
        "path": "manuscript/config.yaml",
        "sha256": config.sha256,
        "bytes": len(config.content),
        "ordinal": 1,
        "consumer": {"source": SRC + "/core/experiment_config.py", "function": "load_experiment_config"},
    }
    report_write = {
        "path": REPORT,
        "sha256": report.sha256,
        "bytes": len(report.content),
        "native_identity": [1, 2, 2, 3, 4],
        "prior_registered_read_count": 1,
        "producer": {"source": SRC + "/analysis/scientific_reports.py", "function": "run_stability_analysis"},
    }
    report_read = {
        "path": REPORT,
        "sha256": report.sha256,
        "bytes": len(report.content),
        "native_identity": [1, 2, 2, 3, 4],
        "ordinal": 2,
        "consumer": {"source": SRC + "/core/manuscript_variables.py", "function": "_load_json_report"},
    }
    variable_write = {
        "path": VARIABLES,
        "sha256": variables.sha256,
        "bytes": len(variables.content),
        "prior_registered_read_count": 2,
        "producer": {"source": SRC + "/core/manuscript_variables.py", "function": "save_variables"},
    }
    producer = {
        "stage_key": "analysis:scripts/analysis.py",
        "analysis_nonce": "DATA",
        "observed_process": {},
        "native_stage_original": {},
        "registered_returned_reads": {"records": [read_config], "completed_writes": {"records": [report_write]}},
    }
    hydration = {
        "stage_key": HYDRATION,
        "analysis_nonce": "DATA",
        "observed_process": {},
        "registered_returned_reads": {"records": [report_read], "completed_writes": {"records": [variable_write]}},
    }
    return {"ordered_stages": [producer, hydration]}, config, report, variables


def test_completed_report_origin_retains_both_temporal_edges(tmp_path: Path) -> None:
    data, config, report, variables = _temporal_data(tmp_path)
    origin, missing = _registered_report_origin(data, config, report, variables, deadline=time.monotonic() + 10)
    assert missing is None and origin is not None
    assert origin["report_completed_write"]["native_identity"] == origin["report_read"]["native_identity"]
    assert origin["report_read"]["ordinal"] <= origin["variables_completed_write"]["prior_registered_read_count"]


@pytest.mark.parametrize("mutation", ["report-body", "inode", "read-after-write", "producer", "config"])
def test_temporal_report_drift_refuses(tmp_path: Path, mutation: str) -> None:
    data, config, report, variables = _temporal_data(tmp_path)
    data = copy.deepcopy(data)
    producer, hydration = data["ordered_stages"]
    written = producer["registered_returned_reads"]["completed_writes"]["records"][0]
    consumed = hydration["registered_returned_reads"]["records"][0]
    if mutation == "report-body":
        written["sha256"] = "0" * 64
    elif mutation == "inode":
        consumed["native_identity"][1] = 99
    elif mutation == "read-after-write":
        consumed["ordinal"] = 3
    elif mutation == "producer":
        written["producer"]["function"] = "another_writer"
    else:
        producer["registered_returned_reads"]["records"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="temporal chain"):
        _registered_report_origin(data, config, report, variables, deadline=time.monotonic() + 10)


def test_missing_completed_report_write_retains_specific_gap(tmp_path: Path) -> None:
    data, config, report, variables = _temporal_data(tmp_path)
    data["ordered_stages"][0]["registered_returned_reads"]["completed_writes"]["records"] = []
    assert _registered_report_origin(data, config, report, variables, deadline=time.monotonic() + 10) == (
        None,
        "missing-completed-report-write-or-hydration-stage",
    )
