from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from json_io import read_json


def pymdp_logging_expected(root: Path) -> bool:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_runner import pymdp_available

    if not pymdp_available():
        return False
    cfg = load_pymdp_config(root)
    return bool(cfg.logging.enabled)


def _efe_values_explained(payload: dict) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(
        (row.get("terms_available") and bool((row.get("terms") or {}).get("values")))
        or (not row.get("terms_available") and bool(row.get("fallback_reason")))
        for row in rows
    )


def efe_values_explained(payload: dict) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(
        (row.get("terms_available") and bool((row.get("terms") or {}).get("values")))
        or (not row.get("terms_available") and bool(row.get("fallback_reason")))
        for row in rows
    )


def add_simulation_checks(root: Path, checks: dict[str, bool]) -> dict[str, Any]:
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    analysis_stats_path = root / "output" / "data" / "analysis_statistics.json"
    analysis_stats = read_json(analysis_stats_path)
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
    si_stats = analysis_stats.get("si_tmaze") or {}
    if analysis_stats:
        checks["analysis_statistics_schema"] = (
            analysis_stats.get("sweep", {}).get("grid_points", 0) >= 1
            and si_stats.get("trace_summary_steps_match") is True
            and si_stats.get("finite_trace") is True
            and int(si_stats.get("action_switch_count", -1) or -1) >= 0
            and float(si_stats.get("action_switch_rate", -1.0) or -1.0) >= 0.0
            and "entropy_drop" in si_stats
        )

    comparison_path = root / "output" / "data" / "si_policy_comparison.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        runs = comparison.get("runs") or []
        checks["si_policy_comparison_schema"] = (
            bool(runs)
            and {row.get("mode") for row in runs} == {"state_inference", "policy_inference"}
            and all("horizon" in row and "goal_reached" in row for row in runs)
            and (comparison.get("summary") or {}).get("complete_grid") is True
            and (comparison.get("summary") or {}).get("all_efe_rows_explained") is True
            # Re-derived from runs (PR#23 class): every run must carry EFE values
            # or an explicit fallback reason — a forged summary flag cannot pass.
            and all(
                bool(row.get("expected_free_energy_values")) or bool(row.get("expected_free_energy_fallback_reasons"))
                for row in runs
            )
        )
    posterior_path = root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    if posterior_path.exists():
        posterior = json.loads(posterior_path.read_text(encoding="utf-8"))
        rows = posterior.get("rows") or []
        checks["pymdp_policy_posterior_grid_schema"] = (
            posterior.get("schema") == "template_active_inference.pymdp_policy_posterior_grid.v1"
            and bool(rows)
            and posterior.get("all_available_posteriors_normalized") is True
            and posterior.get("all_unavailable_rows_explained") is True
            and all(
                (not row.get("posterior_available")) or abs(float(sum(row.get("q_pi") or [])) - 1.0) <= 1e-9
                for row in rows
            )
        )
    runtime_path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    if runtime_path.exists():
        from simulation.pymdp_runtime import validate_runtime_diagnostics

        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        checks["pymdp_runtime_diagnostics_schema"] = (
            runtime.get("schema") == "template_active_inference.pymdp_runtime_diagnostics.v1"
            and runtime.get("ok") is True
            and int(runtime.get("unexpected_warning_count", 0) or 0) == 0
            and not validate_runtime_diagnostics(root)
        )

    graph_summary_path = root / "output" / "data" / "si_graph_world_summary.json"
    graph_trace_path = root / "output" / "data" / "si_graph_world_trace.json"
    if graph_summary_path.exists() and graph_trace_path.exists():
        graph_summary = json.loads(graph_summary_path.read_text(encoding="utf-8"))
        graph_trace = json.loads(graph_trace_path.read_text(encoding="utf-8"))
        checks["si_graph_world_schema"] = (
            graph_summary.get("status") == "ok"
            and graph_summary.get("goal_reached") is True
            and len(graph_trace.get("steps") or []) == int(graph_summary.get("steps", 0))
            and "not_implemented" not in json.dumps(graph_summary)
        )

    return {
        "summary_path": summary_path,
        "si_summary_present": si_summary_present,
        "comparison_path": comparison_path,
        "graph_summary_path": graph_summary_path,
    }


def add_log_check(root: Path, checks: dict[str, bool]) -> None:
    log_path = root / "output" / "logs" / "pymdp_runs.jsonl"
    if pymdp_logging_expected(root):
        checks["si_log_present"] = log_path.exists() and any(
            line.strip() for line in log_path.read_text(encoding="utf-8").splitlines()
        )

    else:
        checks["si_log_present"] = False
