"""Tests for src.manuscript_variables — {{TOKEN}} generation, no mocks.

Builds real config.yaml / output/data / output/reports fixtures under
``tmp_path`` rather than mocking file I/O.
"""

from __future__ import annotations

import json

import pytest
import yaml

from src.manuscript_variables import generate_variables, save_variables


def _write_config(project_root) -> None:
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "paper": {"version": "1.0"},
        "authors": [{"name": "Test Author"}],
        "keywords": ["methods", "controlled systems"],
    }
    (manuscript_dir / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")


def test_generate_variables_draft_mode_without_outputs(tmp_path):
    _write_config(tmp_path)
    variables = generate_variables(tmp_path, require_analysis_outputs=False)
    assert variables["CONFIG_VERSION"] == "1.0"
    assert variables["CONFIG_FIRST_AUTHOR"] == "Test Author"
    assert variables["PBS_STEP_COUNT"] == "N/A"
    assert variables["TOTAL_GATES_RUN"] == "N/A"
    # DSL constants and the live determinism check never depend on output/.
    assert variables["DETERMINISM_CHECK"] == "Yes"
    assert variables["EXAMPLE_METHOD_COUNT"] == "2"
    assert int(variables["DSL_UNIT_COUNT"]) > 0


def test_generate_variables_raises_when_required_outputs_missing(tmp_path):
    _write_config(tmp_path)
    with pytest.raises(FileNotFoundError, match="compiled_plans.json"):
        generate_variables(tmp_path, require_analysis_outputs=True)


def test_generate_variables_reads_compiled_plans_and_reports(tmp_path):
    _write_config(tmp_path)
    data_dir = tmp_path / "output" / "data"
    reports_dir = tmp_path / "output" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    plans = [
        {
            "method_name": "PBSPreparation",
            "method_version": "1.0",
            "target": "human",
            "plan_hash": "a" * 64,
            "step_count": 5,
        },
        {
            "method_name": "SensorCalibrationSweep",
            "method_version": "1.0",
            "target": "automated",
            "plan_hash": "b" * 64,
            "step_count": 4,
        },
    ]
    (data_dir / "compiled_plans.json").write_text(json.dumps(plans), encoding="utf-8")
    (reports_dir / "gate_report.json").write_text(
        json.dumps({"total_gates_run": 8, "total_gates_passed": 8}), encoding="utf-8"
    )
    (reports_dir / "trust_chain_report.json").write_text(
        json.dumps({"chain_length": 3, "verified": True}), encoding="utf-8"
    )

    variables = generate_variables(tmp_path, require_analysis_outputs=True)
    assert variables["PBS_STEP_COUNT"] == "5"
    assert variables["PBS_PLAN_HASH"] == "a" * 12
    assert variables["CALIBRATION_STEP_COUNT"] == "4"
    assert variables["TOTAL_GATES_RUN"] == "8"
    assert variables["TOTAL_GATES_PASSED"] == "8"
    assert variables["TRUST_CHAIN_LENGTH"] == "3"
    assert variables["TRUST_CHAIN_VERIFIED"] == "Yes"


def test_save_variables_writes_json(tmp_path):
    out_path = tmp_path / "nested" / "vars.json"
    result = save_variables({"KEY": "value"}, out_path)
    assert result == out_path
    assert json.loads(out_path.read_text(encoding="utf-8")) == {"KEY": "value"}


def test_generate_variables_missing_config_uses_defaults(tmp_path):
    variables = generate_variables(tmp_path, require_analysis_outputs=False)
    assert variables["CONFIG_VERSION"] == "1.0"
    assert variables["CONFIG_FIRST_AUTHOR"] == "Unknown"
