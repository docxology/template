"""Persist sophisticated-inference T-maze run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import (
    PymdpConfig,
    SimulationMode,
    apply_pymdp_overrides,
    config_snapshot,
    load_pymdp_config,
)
from simulation.pymdp_runtime import write_runtime_diagnostics
from simulation.si_loop import SIRunResult, run_si_tmaze

# Replay-hashed artifacts must be byte-stable across runner generations and
# numpy versions. Raw exp/log-derived floats (softmax policy posteriors,
# entropies, expected free energy) drift at ULP level between x86_64 numpy
# builds, which flips the sha256 recorded by reproducibility_replay.json and
# the sheaf replay matrix. Ten decimals sits ~1e5 above that drift and ~50x
# below the tightest downstream claim tolerance (1e-9 posterior normalization
# over length-2 q_pi vectors), so quantized bytes are platform-invariant
# without weakening any gate.
REPLAY_FLOAT_DECIMALS = 10


def quantize_replay_floats(value: Any) -> Any:
    """Round every float in a JSON-serializable payload to the replay grid.

    Applied at the write boundary of artifacts whose bytes feed replay
    hashing. Normalizes -0.0 to 0.0 so the serialized text is sign-stable.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, REPLAY_FLOAT_DECIMALS) + 0.0
    if isinstance(value, dict):
        return {key: quantize_replay_floats(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [quantize_replay_floats(item) for item in value]
    return value


def write_si_artifacts(
    project_root: Path,
    result: SIRunResult,
    *,
    config: PymdpConfig | None = None,
    trace_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    """Write si artifacts to the output path."""
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
    if result.runtime_diagnostics:
        write_runtime_diagnostics(root, [result.runtime_diagnostics])

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
    """Run and persist."""
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
    horizons: tuple[int, ...] | None = None,
    seeds: tuple[int, ...] | None = None,
    modes: tuple[SimulationMode, ...] | None = None,
) -> Path:
    """Write deterministic state-vs-policy comparison rows without changing main SI artifacts."""
    root = project_root.resolve()
    base = load_pymdp_config(root)
    configured_horizons = horizons if horizons is not None else base.comparison.horizons
    configured_seeds = seeds if seeds is not None else base.comparison.seeds
    configured_modes = modes if modes is not None else base.comparison.modes
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for horizon in configured_horizons:
        for seed in configured_seeds:
            for mode in configured_modes:
                cfg = apply_pymdp_overrides(base, horizon=horizon, steps=horizon, seed=seed, mode=mode)
                logger = RunLogger(
                    root / "output" / "logs" / f"pymdp_compare_{mode}_{horizon}_{seed}.jsonl", enabled=False
                )
                result = run_si_tmaze(root, config=cfg, logger=logger)
                diagnostics.append(result.runtime_diagnostics)
                methods: dict[str, int] = {}
                posterior_steps = []
                efe_values: list[float] = []
                fallback_reasons: set[str] = set()
                for step in result.trace_steps:
                    method = str(step.get("policy_method", mode))
                    methods[method] = methods.get(method, 0) + 1
                    posterior_steps.append(
                        {
                            "step": step.get("step"),
                            "posterior_available": step.get("policy_posterior_available") is True,
                            "posterior_source": step.get("policy_posterior_source"),
                            "q_pi": step.get("q_pi", []),
                            "q_pi_sum": step.get("q_pi_sum"),
                            "q_pi_entropy": step.get("q_pi_entropy"),
                            "q_pi_normalized": step.get("q_pi_normalized") is True,
                            "selected_policy": step.get("selected_policy"),
                            "fallback_reason": step.get("fallback_reason"),
                        }
                    )
                    efe_values.extend(float(value) for value in step.get("expected_free_energy_values", []) or [])
                    if step.get("fallback_reason") and not step.get("expected_free_energy_available"):
                        fallback_reasons.add(str(step["fallback_reason"]))
                available_posteriors = [step for step in posterior_steps if step["posterior_available"]]
                entropy_values = [
                    float(step["q_pi_entropy"]) for step in posterior_steps if step.get("q_pi_entropy") is not None
                ]
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
                        "policy_method": max(methods, key=lambda method: methods[method]),
                        "selected_policy": next(
                            (
                                step["selected_policy"]
                                for step in reversed(posterior_steps)
                                if step.get("selected_policy") is not None
                            ),
                            None,
                        ),
                        "policy_posterior_steps": posterior_steps,
                        "policy_posterior_available_count": len(available_posteriors),
                        "policy_posterior_all_normalized": bool(available_posteriors)
                        and all(step["q_pi_normalized"] for step in available_posteriors),
                        "mean_policy_posterior_entropy": (
                            sum(entropy_values) / len(entropy_values) if entropy_values else None
                        ),
                        "expected_free_energy_values": efe_values,
                        "expected_free_energy_available": bool(efe_values),
                        "expected_free_energy_fallback_reasons": sorted(fallback_reasons)
                        or (
                            ["pymdp did not expose expected-free-energy values for this run"] if not efe_values else []
                        ),
                    }
                )
    expected_run_count = len(configured_modes) * len(configured_horizons) * len(configured_seeds)
    payload = {
        "schema": "template_active_inference.si_policy_comparison.v1",
        "runs": rows,
        "summary": {
            "run_count": len(rows),
            "modes": sorted({row["mode"] for row in rows}),
            "horizons": sorted({row["horizon"] for row in rows}),
            "seeds": sorted({row["seed"] for row in rows}),
            "expected_run_count": expected_run_count,
            "complete_grid": len(rows) == expected_run_count,
            "goal_reached_count": sum(1 for row in rows if row["goal_reached"]),
            "posterior_available_run_count": sum(1 for row in rows if row["policy_posterior_available_count"]),
            "all_available_posteriors_normalized": all(
                row["policy_posterior_all_normalized"] or row["policy_posterior_available_count"] == 0 for row in rows
            ),
            "all_efe_rows_explained": all(
                row["expected_free_energy_available"] or row["expected_free_energy_fallback_reasons"] for row in rows
            ),
        },
    }
    payload = quantize_replay_floats(payload)
    out = root / "output" / "data" / "si_policy_comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_runtime_diagnostics(root, diagnostics)
    write_policy_posterior_grid(root, comparison=payload)
    return out


def write_policy_posterior_grid(
    project_root: Path,
    *,
    comparison: dict[str, Any] | None = None,
) -> Path:
    """Write step-level PyMDP policy posterior normalization evidence."""
    root = project_root.resolve()
    payload = comparison
    if payload is None:
        path = root / "output" / "data" / "si_policy_comparison.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    rows: list[dict[str, Any]] = []
    for run_index, run in enumerate(payload.get("runs") or []):
        for step in run.get("policy_posterior_steps") or []:
            q_pi = [float(value) for value in step.get("q_pi", []) or []]
            q_sum = float(sum(q_pi)) if q_pi else None
            rows.append(
                {
                    "run_index": run_index,
                    "step": step.get("step"),
                    "mode": run.get("mode"),
                    "horizon": run.get("horizon"),
                    "seed": run.get("seed"),
                    "posterior_available": step.get("posterior_available") is True,
                    "posterior_source": step.get("posterior_source"),
                    "q_pi": q_pi,
                    "q_pi_sum": q_sum,
                    "q_pi_entropy": step.get("q_pi_entropy"),
                    "normalized": q_sum is not None and abs(q_sum - 1.0) <= 1e-9,
                    "fallback_reason": step.get("fallback_reason"),
                }
            )
    available = [row for row in rows if row["posterior_available"]]
    unavailable = [row for row in rows if not row["posterior_available"]]
    grid = {
        "schema": "template_active_inference.pymdp_policy_posterior_grid.v1",
        "source": "output/data/si_policy_comparison.json",
        "rows": rows,
        "row_count": len(rows),
        "available_row_count": len(available),
        "all_available_posteriors_normalized": bool(available) and all(row["normalized"] for row in available),
        "all_unavailable_rows_explained": all(bool(row["fallback_reason"]) for row in unavailable),
    }
    grid = quantize_replay_floats(grid)
    out = root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(grid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
