"""Persist sophisticated-inference T-maze run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import PymdpConfig, apply_pymdp_overrides, config_snapshot, load_pymdp_config
from simulation.si_loop import SIRunResult, run_si_tmaze


def write_si_artifacts(
    project_root: Path,
    result: SIRunResult,
    *,
    config: PymdpConfig | None = None,
    trace_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    root = project_root.resolve()
    cfg = config or load_pymdp_config(root)
    data_dir = root / "output" / "data"
    reports_dir = root / "output" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    snapshot = config_snapshot(cfg)
    summary = {
        "steps": result.steps,
        "policy_len": result.policy_len,
        "num_policies": result.num_policies,
        "mean_belief_entropy": result.mean_belief_entropy,
        "actions": result.actions,
        "observations": result.observations,
        "mode": result.mode,
        "config_hash": result.config_hash,
        "goal_reached": result.goal_reached,
        "action_diversity": result.action_diversity,
        "config": snapshot,
    }
    summary_path = data_dir / "si_tmaze_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    steps_payload = trace_steps if trace_steps is not None else result.trace_steps
    trace_path = data_dir / "si_tmaze_trace.json"
    trace_path.write_text(json.dumps({"steps": steps_payload}, indent=2), encoding="utf-8")

    log_path = root / cfg.logging.path
    log_records = 0
    if log_path.exists():
        log_records = sum(1 for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip())
    run_report = {
        "config": snapshot,
        "config_hash": result.config_hash,
        "mode": result.mode,
        "seed": cfg.random_seed,
        "policy_len": result.policy_len,
        "steps": result.steps,
        "log_path": str(cfg.logging.path),
        "log_record_count": log_records,
        "goal_reached": result.goal_reached,
    }
    report_path = reports_dir / "si_tmaze_run_report.json"
    report_path.write_text(json.dumps(run_report, indent=2), encoding="utf-8")

    from simulation.invariants import merge_simulation_into_invariants_report, write_simulation_invariants

    write_simulation_invariants(root)
    merge_simulation_into_invariants_report(root)

    return {
        "summary": summary_path,
        "trace": trace_path,
        "run_report": report_path,
    }


def run_and_persist(
    project_root: Path,
    *,
    config: PymdpConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_pymdp_config(project_root)
    logger = RunLogger.from_project_root(
        project_root,
        relative_path=cfg.logging.path,
        enabled=cfg.logging.enabled,
    )
    logger.fresh()
    result = run_si_tmaze(project_root, config=cfg, logger=logger)
    paths = write_si_artifacts(project_root, result, config=cfg, trace_steps=result.trace_steps)
    return {"result": result, "paths": paths, "log_records": len(logger.records())}


def write_policy_comparison(
    project_root: Path,
    *,
    horizons: tuple[int, ...] = (2, 3),
    seeds: tuple[int, ...] = (0,),
) -> Path:
    """Write deterministic state-vs-policy comparison rows without changing main SI artifacts."""
    root = project_root.resolve()
    base = load_pymdp_config(root)
    rows: list[dict[str, Any]] = []
    for horizon in horizons:
        for seed in seeds:
            for mode in ("state_inference", "policy_inference"):
                cfg = apply_pymdp_overrides(base, horizon=horizon, steps=horizon, seed=seed, mode=mode)
                logger = RunLogger(
                    root / "output" / "logs" / f"pymdp_compare_{mode}_{horizon}_{seed}.jsonl", enabled=False
                )
                result = run_si_tmaze(root, config=cfg, logger=logger)
                methods: dict[str, int] = {}
                for step in result.trace_steps:
                    method = str(step.get("policy_method", mode))
                    methods[method] = methods.get(method, 0) + 1
                rows.append(
                    {
                        "mode": mode,
                        "horizon": horizon,
                        "seed": seed,
                        "steps": result.steps,
                        "policy_len": result.policy_len,
                        "num_policies": result.num_policies,
                        "goal_reached": result.goal_reached,
                        "action_diversity": result.action_diversity,
                        "mean_belief_entropy": result.mean_belief_entropy,
                        "actions": result.actions,
                        "observations": result.observations,
                        "policy_methods": methods,
                    }
                )
    payload = {
        "schema": "template_active_inference.si_policy_comparison.v1",
        "runs": rows,
        "summary": {
            "run_count": len(rows),
            "modes": sorted({row["mode"] for row in rows}),
            "horizons": sorted({row["horizon"] for row in rows}),
            "seeds": sorted({row["seed"] for row in rows}),
            "goal_reached_count": sum(1 for row in rows if row["goal_reached"]),
        },
    }
    out = root / "output" / "data" / "si_policy_comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
