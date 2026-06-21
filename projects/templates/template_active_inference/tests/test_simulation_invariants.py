"""Tests for simulation invariants and logging schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from simulation.invariants import run_simulation_invariants, write_simulation_invariants
from simulation.logging_utils import RunLogger, validate_record
from simulation.si_runner import pymdp_available, run_and_persist

# test_validate_outputs_gate_checks can refresh the full gate-artifact bundle
# after earlier mutation tests; give this module the same ceiling as the other
# heavy Active Inference artifact-contract tests.
pytestmark = pytest.mark.timeout(600)


def test_validate_record_requires_step_keys() -> None:
    with pytest.raises(ValueError, match="missing keys"):
        validate_record({"event": "si_tmaze_step", "step": 0})


def test_run_logger_header_schema(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit_run_header(config_hash="abc", mode="state_inference", seed=0, policy_len=2)
    record = log.records()[0]
    assert record["event"] == "si_tmaze_run_header"
    assert record["config_hash"] == "abc"


@pytest.mark.requires_pymdp
def test_simulation_invariants_after_run(project_root: Path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    results = run_simulation_invariants(project_root)
    assert all(results.values())
    out = write_simulation_invariants(project_root)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True


@pytest.mark.requires_pymdp
def test_validate_outputs_gate_checks(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from gate_support import ensure_gate_artifacts, refresh_output_gate_contracts

    ensure_gate_artifacts(project_root)
    refresh_output_gate_contracts(project_root)
    checks = validate_outputs(project_root)
    assert checks.get("si_trace_present")
    assert checks.get("si_summary_schema")
    assert checks.get("experiment_plan_metrics")
