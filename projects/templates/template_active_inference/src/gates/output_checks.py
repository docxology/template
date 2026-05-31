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

    comparison_path = root / "output" / "data" / "si_policy_comparison.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        runs = comparison.get("runs") or []
        checks["si_policy_comparison_schema"] = (
            bool(runs)
            and {row.get("mode") for row in runs} == {"state_inference", "policy_inference"}
            and all("horizon" in row and "goal_reached" in row for row in runs)
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

    crosswalk_path = root / "output" / "data" / "sheaf_evidence_crosswalk.json"
    dependency_path = root / "output" / "data" / "validation_dependency_graph.json"
    if crosswalk_path.exists():
        crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
        checks["sheaf_evidence_crosswalk_schema"] = crosswalk.get(
            "schema"
        ) == "template_active_inference.evidence_crosswalk.v1" and int(crosswalk.get("claim_count", 0)) == len(
            crosswalk.get("claims") or []
        )
    if dependency_path.exists():
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        artifacts = dependency.get("artifacts") or {}
        checks["validation_dependency_graph_schema"] = (
            dependency.get("schema") == "template_active_inference.validation_dependency_graph.v1"
            and not dependency.get("issues")
            and bool(artifacts.get("output/data/sheaf_gluing_certificate.json"))
            and bool(artifacts.get("output/figures/si_belief_trajectory.gif"))
        )

    provenance_path = root / "output" / "data" / "artifact_provenance.json"
    replay_path = root / "output" / "reports" / "reproducibility_replay.json"
    counterexample_path = root / "output" / "reports" / "counterexample_matrix.json"
    if provenance_path.exists():
        from validation_spine import validate_artifact_provenance

        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        checks["artifact_provenance_schema"] = (
            provenance.get("schema") == "template_active_inference.artifact_provenance.v1"
            and provenance.get("all_hashed") is True
            and provenance.get("all_producers_configured") is True
            and not validate_artifact_provenance(root)
        )
    if replay_path.exists():
        from validation_spine import validate_reproducibility_replay

        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        checks["reproducibility_replay_schema"] = (
            replay.get("schema") == "template_active_inference.reproducibility_replay.v1"
            and replay.get("all_passed") is True
            and not validate_reproducibility_replay(root)
        )
    if counterexample_path.exists():
        from validation_spine import validate_counterexample_matrix

        counterexamples = json.loads(counterexample_path.read_text(encoding="utf-8"))
        checks["counterexample_matrix_schema"] = (
            counterexamples.get("schema") == "template_active_inference.counterexample_matrix.v1"
            and counterexamples.get("all_expected_failures_documented") is True
            and not validate_counterexample_matrix(root)
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
    if comparison_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_policy_comparison_schema",
            False,
        )
    if graph_summary_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_graph_world_schema",
            False,
        )
    if crosswalk_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "sheaf_evidence_crosswalk_schema",
            False,
        )
    if dependency_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "validation_dependency_graph_schema",
            False,
        )
    if provenance_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "artifact_provenance_schema",
            False,
        )
    if replay_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "reproducibility_replay_schema",
            False,
        )
    if counterexample_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "counterexample_matrix_schema",
            False,
        )

    return checks
