"""Tests for simulation invariants and logging schema."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from simulation.invariants import run_simulation_invariants, write_simulation_invariants
from simulation.logging_utils import (
    HEADER_EVENT,
    STEP_EVENT,
    RunLogger,
    _json_default,
    validate_record,
)
from simulation.si_runner import pymdp_available, run_and_persist

# test_validate_outputs_gate_checks can refresh the full gate-artifact bundle
# after earlier mutation tests; give this module the same ceiling as the other
# heavy Active Inference artifact-contract tests.
pytestmark = pytest.mark.timeout(600)


def test_validate_record_requires_step_keys() -> None:
    with pytest.raises(ValueError, match="missing keys"):
        validate_record({"event": "si_tmaze_step", "step": 0})


def test_validate_record_unknown_event_passes() -> None:
    """An unrecognised event type has no required key contract; must not raise."""
    validate_record({"event": "unknown_custom_event", "data": 42})


def test_validate_record_no_event_key_passes() -> None:
    """A record with no 'event' key is also unconstrained; must not raise."""
    validate_record({"step": 0, "obs": 1})


def test_json_default_converts_ndarray() -> None:
    """_json_default must call .tolist() on numpy arrays."""
    arr = np.array([1.0, 2.0, 3.0])
    result = _json_default(arr)
    assert result == [1.0, 2.0, 3.0]


def test_json_default_raises_for_non_serializable() -> None:
    """_json_default must raise TypeError for objects without .tolist()."""
    with pytest.raises(TypeError, match="not JSON serializable"):
        _json_default(object())


def test_run_logger_header_schema(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit_run_header(config_hash="abc", mode="state_inference", seed=0, policy_len=2)
    record = log.records()[0]
    assert record["event"] == "si_tmaze_run_header"
    assert record["config_hash"] == "abc"


def test_run_logger_disabled_emits_nothing(tmp_path: Path) -> None:
    """A disabled RunLogger must not write any files when emit is called."""
    log = RunLogger(tmp_path / "silent.jsonl", enabled=False)
    log.emit({"event": "si_tmaze_step", "step": 0, "obs": 0, "action": 0, "belief_entropy": 0.5})
    assert not (tmp_path / "silent.jsonl").exists()


def test_run_logger_disabled_fresh_is_noop(tmp_path: Path) -> None:
    """fresh() on a disabled logger must not create the file."""
    log = RunLogger(tmp_path / "noop.jsonl", enabled=False)
    log.fresh()
    assert not (tmp_path / "noop.jsonl").exists()


def test_run_logger_records_empty_when_missing(tmp_path: Path) -> None:
    """records() must return an empty list when the log file does not exist."""
    log = RunLogger(tmp_path / "nofile.jsonl")
    assert log.records() == []


def test_run_logger_step_records_filters_events(tmp_path: Path) -> None:
    """step_records() must return only STEP_EVENT records."""
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit_run_header(config_hash="x", mode="state_inference", seed=0, policy_len=2)
    log.emit({"event": STEP_EVENT, "step": 0, "obs": 0, "action": 0, "belief_entropy": 0.1})
    all_records = log.records()
    step_records = log.step_records()
    assert len(all_records) == 2  # header + step
    assert len(step_records) == 1
    assert step_records[0]["event"] == STEP_EVENT


def test_run_logger_timed_emits_runtime_ms(tmp_path: Path) -> None:
    """The timed() context manager must append a 'runtime_ms' field to the emitted record."""
    log = RunLogger(tmp_path / "timed.jsonl")
    log.fresh()
    with log.timed(event="custom_event") as ctx:
        ctx["custom_field"] = "value"
    records = log.records()
    assert len(records) == 1
    assert "runtime_ms" in records[0]
    assert isinstance(records[0]["runtime_ms"], float)


def test_run_logger_from_project_root_default_path(tmp_path: Path) -> None:
    """from_project_root must resolve the path relative to project_root."""
    log = RunLogger.from_project_root(tmp_path)
    assert log.path == tmp_path / "output" / "logs" / "pymdp_runs.jsonl"


def test_run_logger_records_skips_blank_lines(tmp_path: Path) -> None:
    """records() must skip blank/whitespace-only lines in the JSONL file."""
    jl = tmp_path / "blanks.jsonl"
    jl.write_text('{"event": "x"}\n\n   \n{"event": "y"}\n', encoding="utf-8")
    log = RunLogger(jl)
    records = log.records()
    assert len(records) == 2


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
