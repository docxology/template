"""Pipeline output artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

from gates.artifact_manifest import REQUIRED_OUTPUTS


def _pymdp_logging_expected(root: Path) -> bool:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_runner import pymdp_available

    if not pymdp_available():
        return False
    cfg = load_pymdp_config(root)
    return bool(cfg.logging.enabled)


def validate_outputs(project_root: Path) -> dict[str, bool]:
    root = project_root.resolve()
    required = [root / rel for rel in REQUIRED_OUTPUTS]
    checks = {str(p.relative_to(root)): p.exists() for p in required}

    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    si_inv_path = root / "output" / "reports" / "si_invariants.json"
    si_summary_present = summary_path.exists()
    if si_summary_present and not si_inv_path.exists():
        checks["si_invariants_all_pass"] = False
    elif si_inv_path.exists():
        si_inv = json.loads(si_inv_path.read_text(encoding="utf-8"))
        checks["si_invariants_all_pass"] = bool(si_inv.get("all_pass"))

    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.exists():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        checks["invariants_all_pass"] = bool(inv.get("all_pass"))
        sim = inv.get("simulation") or {}
        if sim:
            checks["simulation_invariants_all_pass"] = all(sim.values())

    if summary_path.exists() and trace_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        steps = int(summary.get("steps", 0))
        trace_steps = trace.get("steps") or []
        checks["si_trace_present"] = len(trace_steps) == steps and steps >= 1
        checks["si_summary_schema"] = (
            steps >= 1
            and float(summary.get("mean_belief_entropy", -1.0)) >= 0.0
            and "mode" in summary
            and "config" in summary
        )

    log_path = root / "output" / "logs" / "pymdp_runs.jsonl"
    if _pymdp_logging_expected(root):
        checks["si_log_present"] = log_path.exists() and any(
            line.strip() for line in log_path.read_text(encoding="utf-8").splitlines()
        )

    checks["experiment_plan_metrics"] = checks.get("invariants_all_pass", False) and checks.get(
        str(summary_path.relative_to(root)),
        False,
    )
    if si_summary_present:
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_invariants_all_pass",
            False,
        )

    return checks
