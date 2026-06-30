"""Tests for scripts/methods_analysis.py — the thin orchestrator."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "methods_analysis.py"
_spec = importlib.util.spec_from_file_location("methods_analysis_script", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
methods_analysis_script = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("methods_analysis_script", methods_analysis_script)
_spec.loader.exec_module(methods_analysis_script)


def test_run_methods_analysis_writes_expected_artifacts(tmp_path):
    written = methods_analysis_script.run_methods_analysis(tmp_path)
    assert all(path.exists() for path in written)

    names = {path.name for path in written}
    assert "compiled_plans.json" in names
    assert "gate_report.json" in names
    assert "trust_chain_report.json" in names
    assert "step_counts.png" in names
    assert "pbspreparation_worklist.md" in names
    assert "pbspreparation_plan.csv" in names
    assert "pbspreparation_graph.mmd" in names
    assert "pbspreparation_plan.json" in names


def test_run_methods_analysis_compiled_plans_content(tmp_path):
    methods_analysis_script.run_methods_analysis(tmp_path)
    plans_path = tmp_path / "output" / "data" / "compiled_plans.json"
    plans = json.loads(plans_path.read_text(encoding="utf-8"))
    assert {p["method_name"] for p in plans} == {"PBSPreparation", "SensorCalibrationSweep"}
    for plan in plans:
        assert len(plan["plan_hash"]) == 64


def test_run_methods_analysis_gate_report_all_passed(tmp_path):
    methods_analysis_script.run_methods_analysis(tmp_path)
    gate_report = json.loads((tmp_path / "output" / "reports" / "gate_report.json").read_text(encoding="utf-8"))
    assert gate_report["total_gates_run"] == gate_report["total_gates_passed"]
    assert gate_report["total_gates_run"] == 8  # 2 methods x 4 gates each


def test_run_methods_analysis_trust_chain_verified(tmp_path):
    methods_analysis_script.run_methods_analysis(tmp_path)
    trust_report = json.loads((tmp_path / "output" / "reports" / "trust_chain_report.json").read_text(encoding="utf-8"))
    assert trust_report == {"chain_length": 3, "verified": True}
