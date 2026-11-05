"""Benchmark support: evaluate a pure project function with an infra rubric.

Thin domain helper that demonstrates ``infrastructure.benchmark`` from inside
the code exemplar. It evaluates :func:`quadratic_function` across fixed inputs
and scores deterministic facts through the real ``infrastructure.benchmark``
rubric API. Wall-clock measurements are retained only in memory as runtime
diagnostics; tracked reports omit them. Orchestration (writing reports and
figures) lives in ``scripts/``; this module only computes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from infrastructure.benchmark import (
    BenchmarkScore,
    RubricScore,
    RubricSet,
    score_rubric,
    scores_to_markdown,
)

from .optimizer import quadratic_function

PROJECT_NAME = "template_code_project"
DEFAULT_INPUT_SIZES: tuple[int, ...] = (2, 4, 8, 16)
DEFAULT_REPEATS = 50
_SEED = 7
TIMING_POLICY = (
    "Wall-clock measurements are environment-dependent runtime diagnostics "
    "and are intentionally omitted from tracked benchmark artifacts."
)

_RUBRIC = RubricSet.from_dict(
    {
        "name": "code-project-benchmark",
        "dimensions": [
            {"name": "all_sizes_evaluated", "weight": 1.0},
            {"name": "finite_objective_values", "weight": 1.0},
            {"name": "repeat_budget_completed", "weight": 1.0},
            {"name": "deterministic_objective", "weight": 1.0},
        ],
    }
)


@dataclass(frozen=True)
class TimingMeasurement:
    """One benchmark measurement; timing is a runtime-only diagnostic."""

    input_size: int
    repeats: int
    calls: int
    best_seconds: float
    objective_value: float


@dataclass(frozen=True)
class BenchmarkRun:
    """Full benchmark run: measurements plus infra-scored rubric result."""

    measurements: tuple[TimingMeasurement, ...]
    checks: dict[str, bool]
    rubric: RubricSet
    rubric_score: RubricScore
    benchmark_score: BenchmarkScore


def _fixed_input(size: int) -> np.ndarray:
    """Deterministic input vector for a given size (fixed seed)."""
    rng = np.random.default_rng(_SEED + size)
    return rng.standard_normal(size)


def _time_one(size: int, repeats: int) -> TimingMeasurement:
    """Time ``quadratic_function`` at ``size`` over ``repeats`` real calls."""
    x = _fixed_input(size)
    best = float("inf")
    objective = 0.0
    for _ in range(repeats):
        start = perf_counter()
        objective = quadratic_function(x)
        elapsed = perf_counter() - start
        best = min(best, elapsed)
    return TimingMeasurement(
        input_size=size,
        repeats=repeats,
        calls=repeats,
        best_seconds=max(best, 0.0),
        objective_value=float(objective),
    )


def run_quadratic_benchmark(
    input_sizes: tuple[int, ...] = DEFAULT_INPUT_SIZES,
    repeats: int = DEFAULT_REPEATS,
) -> BenchmarkRun:
    """Evaluate the pure quadratic objective and score deterministic facts."""
    measurements = tuple(_time_one(size, repeats) for size in input_sizes)

    # Deterministic re-computation to assert the objective is reproducible.
    repeated = {m.input_size: float(quadratic_function(_fixed_input(m.input_size))) for m in measurements}

    checks: dict[str, bool] = {
        "all_sizes_evaluated": len(measurements) == len(input_sizes),
        "finite_objective_values": all(np.isfinite(m.objective_value) for m in measurements),
        "repeat_budget_completed": all(m.calls == repeats and m.repeats == repeats for m in measurements),
        "deterministic_objective": all(repeated[m.input_size] == m.objective_value for m in measurements),
    }

    rubric_score = score_rubric(checks, _RUBRIC)
    benchmark_score = BenchmarkScore(
        project=PROJECT_NAME,
        passed=rubric_score.passed,
        score=int(rubric_score.score),
        max_score=int(rubric_score.max_score),
        issues=tuple(f"failed check: {name}" for name in rubric_score.failed_dimensions),
    )
    return BenchmarkRun(
        measurements=measurements,
        checks=checks,
        rubric=_RUBRIC,
        rubric_score=rubric_score,
        benchmark_score=benchmark_score,
    )


def benchmark_payload(run: BenchmarkRun) -> dict[str, Any]:
    """Convert a run into a byte-stable, JSON-safe canonical payload."""
    return {
        "schema_version": "template_code_project/benchmark_rubric/v2",
        "project": PROJECT_NAME,
        "passed": run.benchmark_score.passed,
        "timing_policy": TIMING_POLICY,
        "checks": dict(run.checks),
        "rubric": {
            "name": run.rubric.name,
            "score": run.rubric_score.score,
            "max_score": run.rubric_score.max_score,
            "dimensions": [dimension.name for dimension in run.rubric.dimensions],
            "passed_dimensions": list(run.rubric_score.passed_dimensions),
            "failed_dimensions": list(run.rubric_score.failed_dimensions),
        },
        "measurements": [
            {
                "input_size": m.input_size,
                "repeats": m.repeats,
                "calls": m.calls,
                "objective_value": m.objective_value,
            }
            for m in run.measurements
        ],
        "markdown": scores_to_markdown((run.benchmark_score,)),
    }


def write_benchmark_report(run: BenchmarkRun, output_path: Path) -> Path:
    """Write the benchmark payload as JSON and return the path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = benchmark_payload(run)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
