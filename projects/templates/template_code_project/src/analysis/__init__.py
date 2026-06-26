"""Optimization analysis package — re-export barrel plus cross-algorithm comparison.

Public API
----------
Core pipeline (unchanged):
    run_analysis_pipeline, main
    run_convergence_experiment, save_optimization_results
    run_stability_analysis, run_performance_benchmarking
    extract_optimization_metadata, generate_citations_from_metadata
    save_publishing_materials, save_validation_report
    validate_generated_outputs, register_figure

Cross-algorithm comparison (new):
    compare_algorithms          → AlgorithmComparison
    multi_factor_analysis       → MultiFactorReport

Infrastructure probes (re-exported):
    INFRASTRUCTURE_AVAILABLE, ProgressBar, ScriptExecutionError,
    SystemHealthChecker, TemplateError

Logging helpers (re-exported):
    _get_logger, _setup_fallback_logging

Scientific helpers (re-exported):
    _benchmark_timings, _stability_score_from_runs
    benchmark_function, check_numerical_stability

Misc (re-exported):
    verify_output_integrity, log_success, project_root
"""

from __future__ import annotations

import logging
import time as _time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ._infra import (
    INFRASTRUCTURE_AVAILABLE,
    ProgressBar,
    ScriptExecutionError,
    SystemHealthChecker,
    TemplateError,
    benchmark_function,
    check_numerical_stability,
    log_success,
    verify_output_integrity,
)
from ._logging import _setup_fallback_logging, get_logger as _get_logger
from ..project_paths import _DEFAULT_ROOT as project_root
from .pipeline import (
    extract_optimization_metadata,
    generate_citations_from_metadata,
    register_figure,
    run_convergence_experiment,
    run_performance_benchmarking,
    run_stability_analysis,
    save_optimization_results,
    save_publishing_materials,
    save_validation_report,
    validate_generated_outputs,
)
from .scientific_reports import _benchmark_timings, _stability_score_from_runs
from .workflow import main, run_analysis_pipeline

if not INFRASTRUCTURE_AVAILABLE:

    def log_success(  # pragma: no cover — only executed when infrastructure import fails
        message: str, logger: "logging.Logger | None" = None
    ) -> None:
        return None


# ---------------------------------------------------------------------------
# Cross-algorithm comparison data structures
# ---------------------------------------------------------------------------


@dataclass
class AlgorithmVariant:
    """Descriptor for one gradient-descent configuration under comparison.

    Attributes
    ----------
    name:
        Human-readable label used in reports, e.g. ``"GD α=0.10"``.
    step_size:
        Fixed step size used by gradient descent.
    converged:
        Whether the run terminated before ``max_iterations``.
    iterations:
        Number of update steps taken.
    final_objective:
        Objective value at the terminal iterate.
    gradient_norm:
        Gradient ‖∇f‖ at termination.
    objective_history:
        Full objective-value trace (may be empty when unavailable).
    convergence_rate:
        Estimated per-step improvement rate (mean |Δf| / step).  ``0.0``
        when fewer than two history points are available.
    stability_score:
        Numerical stability score ∈ [0, 1] computed by
        :func:`_stability_score_from_runs`.  ``None`` before the
        cross-algorithm comparison run populates it.
    timing_s:
        Wall-clock seconds for the gradient-descent run.
    """

    name: str
    step_size: float
    converged: bool
    iterations: int
    final_objective: float
    gradient_norm: float
    objective_history: list[float] = field(default_factory=list)
    convergence_rate: float = 0.0
    stability_score: float | None = None
    timing_s: float = 0.0


@dataclass
class AlgorithmComparison:
    """Ranked cross-algorithm comparison for gradient-descent variants.

    Attributes
    ----------
    variants:
        One :class:`AlgorithmVariant` per step-size tested, ranked by
        convergence quality (converged first, then by final objective).
    best_variant:
        The variant with the lowest final objective value among those
        that converged; falls back to the overall minimum if none converged.
    convergence_summary:
        Percentage of variants that converged (0–100).
    objective_spread:
        ``max(final_objective) - min(final_objective)`` across all variants.
    mean_iterations:
        Mean iteration count across all variants.
    fastest_convergence:
        Name of the variant that converged in fewest iterations.
    slowest_convergence:
        Name of the variant that required most iterations (or ``"none"``).
    ranking_table:
        List of ``{"rank", "name", "step_size", "converged",
        "final_objective", "iterations", "convergence_rate",
        "stability_score", "timing_s"}`` dicts sorted best → worst.
    """

    variants: list[AlgorithmVariant]
    best_variant: AlgorithmVariant
    convergence_summary: float
    objective_spread: float
    mean_iterations: float
    fastest_convergence: str
    slowest_convergence: str
    ranking_table: list[dict[str, Any]]


@dataclass
class MultiFactorReport:
    """Multi-factor analysis combining convergence, stability, and performance.

    Factors
    -------
    convergence_factor:
        Fraction of step sizes that converged (0.0–1.0).
    stability_factor:
        Mean numerical stability score across tested starting points (0.0–1.0).
    performance_factor:
        Normalised speed score: ``1 / (1 + mean_timing_s * 1 000)``.  Higher
        is faster (bounded in (0, 1]).
    efficiency_factor:
        ``convergence_factor × (1 - mean_iterations / max_iterations)``.
        Rewards both convergence and fewer iterations.
    composite_score:
        Weighted combination of all factors; weights sum to 1.0.
    factor_weights:
        ``{"convergence": w0, "stability": w1, "performance": w2, "efficiency": w3}``
    factor_breakdown:
        Full detail dict with raw and weighted contributions.
    recommendations:
        Actionable list drawn from sub-threshold factors.
    best_overall_variant:
        Name of the step size recommended for production use.
    """

    convergence_factor: float
    stability_factor: float
    performance_factor: float
    efficiency_factor: float
    composite_score: float
    factor_weights: dict[str, float]
    factor_breakdown: dict[str, Any]
    recommendations: list[str]
    best_overall_variant: str


# ---------------------------------------------------------------------------
# Cross-algorithm comparison
# ---------------------------------------------------------------------------


def compare_algorithms(
    results: dict[float, Any] | None = None,
    *,
    config: Any | None = None,
    stability_check: bool = True,
    time_runs: bool = True,
) -> AlgorithmComparison:
    """Compare gradient-descent variants across all configured step sizes.

    For each step size in *results* (or freshly computed via
    :func:`run_convergence_experiment` when *results* is ``None``) this
    function:

    * ranks variants by convergence quality and final objective value,
    * estimates convergence rate as mean |Δf| per step,
    * optionally computes a numerical stability score via
      :func:`_stability_score_from_runs`,
    * optionally measures wall-clock time for each variant.

    Parameters
    ----------
    results:
        Pre-computed ``{step_size: OptimizationResult}`` mapping.  When
        ``None``, :func:`run_convergence_experiment` is called with *config*.
    config:
        Optional :class:`~src.experiment_config.ExperimentConfig`.  Used both
        to run fresh experiments and to parameterise the stability check.
    stability_check:
        When ``True`` (default), augment each variant with a numerical
        stability score computed on four representative starting points.
    time_runs:
        When ``True`` (default), re-run each variant once and record
        wall-clock seconds.  Set ``False`` for speed when timing is not
        needed.

    Returns
    -------
    AlgorithmComparison
        Ranked comparison with per-variant detail and aggregate statistics.

    Examples
    --------
    >>> from src.analysis import compare_algorithms
    >>> report = compare_algorithms()
    >>> print(report.best_variant.name)
    """
    from ..experiment_config import load_experiment_config
    from ..optimizer import compute_gradient, gradient_descent, quadratic_function, quadratic_optimum
    from .experiments import _project_root

    cfg = config or load_experiment_config(_project_root())

    if results is None:
        results = run_convergence_experiment(config=cfg)

    A = cfg.A_array()
    b = cfg.b_array()
    x0 = cfg.x0()
    _, f_star = quadratic_optimum(A, b)

    # Build AlgorithmVariant objects
    variants: list[AlgorithmVariant] = []
    for step_size, result in results.items():
        history: list[float] = result.objective_history or []
        if len(history) >= 2:
            deltas = [abs(history[i + 1] - history[i]) for i in range(len(history) - 1)]
            conv_rate = float(np.mean(deltas))
        else:
            conv_rate = 0.0

        # Optional timing: single re-run per variant
        timing_s = 0.0
        if time_runs:
            obj_func = lambda x, _A=A, _b=b: quadratic_function(x, _A, _b)  # noqa: E731
            grad_func = lambda x, _A=A, _b=b: compute_gradient(x, _A, _b)  # noqa: E731
            t0 = _time.perf_counter()
            gradient_descent(
                initial_point=x0.copy(),
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=float(step_size),
                max_iterations=cfg.max_iterations,
                tolerance=cfg.tolerance,
            )
            timing_s = _time.perf_counter() - t0

        # Optional stability per variant
        stab_score: float | None = None
        if stability_check:
            test_inputs = [np.array([float(p)]) for p in cfg.stability_starting_points[:4]]
            stab_score, _max_err, _recs = _stability_score_from_runs(test_inputs, A, b, step_size=float(step_size))

        variants.append(
            AlgorithmVariant(
                name=f"GD α={float(step_size):.4g}",
                step_size=float(step_size),
                converged=bool(result.converged),
                iterations=int(result.iterations),
                final_objective=float(result.objective_value),
                gradient_norm=float(result.gradient_norm),
                objective_history=list(history),
                convergence_rate=conv_rate,
                stability_score=stab_score,
                timing_s=timing_s,
            )
        )

    # Sort: converged variants first (by final objective), then diverged (by final objective)
    converged_variants = sorted(
        [v for v in variants if v.converged],
        key=lambda v: v.final_objective,
    )
    diverged_variants = sorted(
        [v for v in variants if not v.converged],
        key=lambda v: v.final_objective,
    )
    ranked_variants = converged_variants + diverged_variants

    best_variant = ranked_variants[0] if ranked_variants else variants[0]

    convergence_summary = 100.0 * sum(1 for v in variants if v.converged) / len(variants) if variants else 0.0

    objectives = [v.final_objective for v in variants]
    objective_spread = float(np.ptp(objectives)) if len(objectives) > 1 else 0.0

    mean_iterations = float(np.mean([v.iterations for v in variants])) if variants else 0.0

    converged_by_iter = sorted(converged_variants, key=lambda v: v.iterations)
    fastest_convergence = converged_by_iter[0].name if converged_by_iter else "none"
    slowest_convergence = converged_by_iter[-1].name if len(converged_by_iter) > 1 else "none"

    ranking_table = [
        {
            "rank": rank + 1,
            "name": v.name,
            "step_size": v.step_size,
            "converged": v.converged,
            "final_objective": v.final_objective,
            "iterations": v.iterations,
            "convergence_rate": v.convergence_rate,
            "stability_score": v.stability_score,
            "timing_s": v.timing_s,
        }
        for rank, v in enumerate(ranked_variants)
    ]

    return AlgorithmComparison(
        variants=ranked_variants,
        best_variant=best_variant,
        convergence_summary=convergence_summary,
        objective_spread=objective_spread,
        mean_iterations=mean_iterations,
        fastest_convergence=fastest_convergence,
        slowest_convergence=slowest_convergence,
        ranking_table=ranking_table,
    )


# ---------------------------------------------------------------------------
# Multi-factor analysis
# ---------------------------------------------------------------------------

_DEFAULT_FACTOR_WEIGHTS: dict[str, float] = {
    "convergence": 0.35,
    "stability": 0.30,
    "performance": 0.15,
    "efficiency": 0.20,
}


def multi_factor_analysis(
    comparison: AlgorithmComparison | None = None,
    *,
    config: Any | None = None,
    factor_weights: dict[str, float] | None = None,
) -> MultiFactorReport:
    """Combine convergence, stability, and performance into a composite score.

    This function aggregates the per-variant data already collected by
    :func:`compare_algorithms` into four normalised factors, weights them,
    and produces a single composite score together with actionable
    recommendations.

    Factor definitions
    ------------------
    convergence_factor (weight 0.35 by default):
        Fraction of tested step sizes that converged (0.0–1.0).

    stability_factor (weight 0.30):
        Mean numerical stability score across variants.  Uses
        :func:`_stability_score_from_runs` scores embedded in the
        *comparison* variants, or recomputes them if unavailable.

    performance_factor (weight 0.15):
        Normalised speed score ``1 / (1 + mean_timing_ms)``, where
        *mean_timing_ms* is the average run duration in milliseconds.
        Approaches 1.0 for very fast runs and 0.0 for very slow ones.

    efficiency_factor (weight 0.20):
        ``convergence_factor × (1 − mean_iterations / max_iterations)``.
        Rewards fast convergence within the iteration budget.

    Parameters
    ----------
    comparison:
        Pre-computed :class:`AlgorithmComparison`.  When ``None``,
        :func:`compare_algorithms` is called with *config*.
    config:
        Optional :class:`~src.experiment_config.ExperimentConfig`.  Forwarded
        to :func:`compare_algorithms` when *comparison* is ``None``.
    factor_weights:
        Custom weight dict.  Keys must be a subset of
        ``{"convergence", "stability", "performance", "efficiency"}``;
        weights are normalised to sum to 1.0 before use.

    Returns
    -------
    MultiFactorReport
        Full factor breakdown, composite score, and recommendations.

    Examples
    --------
    >>> from src.analysis import compare_algorithms, multi_factor_analysis
    >>> cmp = compare_algorithms()
    >>> report = multi_factor_analysis(cmp)
    >>> print(f"Composite score: {report.composite_score:.3f}")
    """
    from ..experiment_config import load_experiment_config
    from .experiments import _project_root

    cfg = config or load_experiment_config(_project_root())

    if comparison is None:
        comparison = compare_algorithms(config=cfg)

    variants = comparison.variants
    if not variants:
        # Degenerate case — return a zeroed report
        return MultiFactorReport(
            convergence_factor=0.0,
            stability_factor=0.0,
            performance_factor=0.0,
            efficiency_factor=0.0,
            composite_score=0.0,
            factor_weights=_DEFAULT_FACTOR_WEIGHTS,
            factor_breakdown={},
            recommendations=["No algorithm variants available for analysis."],
            best_overall_variant="none",
        )

    # --- Resolve factor weights ---
    weights = dict(_DEFAULT_FACTOR_WEIGHTS)
    if factor_weights:
        for k, v in factor_weights.items():
            if k in weights:
                weights[k] = float(v)
    # Normalise to sum to 1.0
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {k: v / total_w for k, v in weights.items()}

    # --- Factor 1: Convergence ---
    convergence_factor = comparison.convergence_summary / 100.0

    # --- Factor 2: Stability ---
    stab_scores = [v.stability_score for v in variants if v.stability_score is not None]
    if stab_scores:
        stability_factor = float(np.mean(stab_scores))
    else:
        # Fall back: recompute stability from experiments using converged variants
        A = cfg.A_array()
        b = cfg.b_array()
        test_inputs = [np.array([float(p)]) for p in cfg.stability_starting_points[:4]]
        per_variant_stab: list[float] = []
        for variant in variants:
            score, _err, _recs = _stability_score_from_runs(test_inputs, A, b, step_size=variant.step_size)
            per_variant_stab.append(score)
        stability_factor = float(np.mean(per_variant_stab)) if per_variant_stab else 0.0

    # --- Factor 3: Performance ---
    timings_ms = [v.timing_s * 1000.0 for v in variants]
    mean_timing_ms = float(np.mean(timings_ms)) if timings_ms else 0.0
    performance_factor = 1.0 / (1.0 + mean_timing_ms)

    # --- Factor 4: Efficiency ---
    max_iter = float(cfg.max_iterations)
    mean_iter_fraction = float(np.mean([v.iterations for v in variants])) / max_iter if max_iter > 0 else 1.0
    efficiency_factor = convergence_factor * max(0.0, 1.0 - mean_iter_fraction)

    # --- Composite score ---
    composite_score = (
        weights["convergence"] * convergence_factor
        + weights["stability"] * stability_factor
        + weights["performance"] * performance_factor
        + weights["efficiency"] * efficiency_factor
    )

    # --- Recommendations ---
    recommendations: list[str] = []
    if convergence_factor < 0.5:
        recommendations.append(
            "More than half of the tested step sizes failed to converge — "
            "consider restricting the sweep to α < 2/λ_max(A)."
        )
    if stability_factor < 0.8:
        recommendations.append(
            f"Mean stability score {stability_factor:.2f} is below 0.80 — "
            "consider adaptive step-size control or preconditioned gradient descent."
        )
    if performance_factor < 0.5:
        recommendations.append(
            f"Mean per-run time {mean_timing_ms:.2f} ms is elevated — "
            "profile the gradient and objective functions for vectorisation opportunities."
        )
    if efficiency_factor < 0.3:
        recommendations.append(
            f"Efficiency factor {efficiency_factor:.2f} is low — "
            "many runs use the full iteration budget; tighten the step-size range or "
            "increase max_iterations."
        )
    if not recommendations:
        recommendations.append(f"All factors are within acceptable ranges (composite score: {composite_score:.3f}).")

    # --- Best overall variant ---
    # Pick the converged variant with highest weighted score per variant:
    #   variant_score = stability * (1 - iter_fraction) * converged
    def _variant_score(v: AlgorithmVariant) -> float:
        if not v.converged:
            return -1.0
        iter_frac = v.iterations / max_iter if max_iter > 0 else 1.0
        stab = v.stability_score if v.stability_score is not None else stability_factor
        return stab * (1.0 - iter_frac)

    best_overall = max(variants, key=_variant_score)
    best_overall_variant = best_overall.name

    # --- Factor breakdown ---
    factor_breakdown: dict[str, Any] = {
        "convergence": {
            "raw": convergence_factor,
            "weight": weights["convergence"],
            "weighted": weights["convergence"] * convergence_factor,
            "n_converged": int(comparison.convergence_summary / 100.0 * len(variants) + 0.5),
            "n_total": len(variants),
        },
        "stability": {
            "raw": stability_factor,
            "weight": weights["stability"],
            "weighted": weights["stability"] * stability_factor,
            "per_variant": {v.name: v.stability_score for v in variants},
        },
        "performance": {
            "raw": performance_factor,
            "weight": weights["performance"],
            "weighted": weights["performance"] * performance_factor,
            "mean_timing_ms": mean_timing_ms,
            "per_variant_timing_ms": {v.name: v.timing_s * 1000.0 for v in variants},
        },
        "efficiency": {
            "raw": efficiency_factor,
            "weight": weights["efficiency"],
            "weighted": weights["efficiency"] * efficiency_factor,
            "mean_iter_fraction": mean_iter_fraction,
            "max_iterations": int(max_iter),
        },
        "composite": composite_score,
        "best_variant": best_overall_variant,
    }

    return MultiFactorReport(
        convergence_factor=convergence_factor,
        stability_factor=stability_factor,
        performance_factor=performance_factor,
        efficiency_factor=efficiency_factor,
        composite_score=composite_score,
        factor_weights=weights,
        factor_breakdown=factor_breakdown,
        recommendations=recommendations,
        best_overall_variant=best_overall_variant,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Infrastructure probes
    "INFRASTRUCTURE_AVAILABLE",
    "ProgressBar",
    "ScriptExecutionError",
    "SystemHealthChecker",
    "TemplateError",
    # Scientific helpers
    "_benchmark_timings",
    "_stability_score_from_runs",
    "benchmark_function",
    "check_numerical_stability",
    # Logging
    "_get_logger",
    "_setup_fallback_logging",
    # Pipeline steps
    "extract_optimization_metadata",
    "generate_citations_from_metadata",
    "log_success",
    "main",
    "project_root",
    "register_figure",
    "run_analysis_pipeline",
    "run_convergence_experiment",
    "run_performance_benchmarking",
    "run_stability_analysis",
    "save_optimization_results",
    "save_publishing_materials",
    "save_validation_report",
    "validate_generated_outputs",
    "verify_output_integrity",
    # Cross-algorithm comparison (new)
    "AlgorithmVariant",
    "AlgorithmComparison",
    "MultiFactorReport",
    "compare_algorithms",
    "multi_factor_analysis",
]
