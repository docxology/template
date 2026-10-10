"""Independent finite plotted meanings for six selected Code PNG roles.

The actual outer Source/analysis reader supplies completed-write and native asset
custody separately. This predicate uses stdlib scalar recurrences and existing
SDK report meaning, never a project plotting callback or companion pass bit.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_stability_domain import validate_sdk_stability_report
from infrastructure.reporting.native_code_value_predicate import (
    ScalarQuadraticConfig,
    _objective,
    _result,
    validate_scalar_csv,
)

SELECTED = (
    "convergence_plot.png",
    "convergence_rate_comparison.png",
    "step_size_sensitivity.png",
    "algorithm_complexity.png",
    "stability_analysis.png",
    "performance_benchmark.png",
)
GRID = (0.005, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4)
PROFILES = (
    ("Identity (H=I)", 1.0),
    ("Mild cond. (H=2I)", 2.0),
    ("Moderate cond. (H=5I)", 5.0),
    ("Ill-conditioned (H=10I)", 10.0),
)


def _history(cfg: ScalarQuadraticConfig, alpha: float, deadline: float) -> list[float]:
    result = _result(cfg, alpha, deadline)
    x = float(cfg.initial_point)
    values = [_objective(cfg, x)]
    for _ in range(result.iterations):
        remaining(deadline)
        x -= alpha * (cfg.coefficient * x - cfg.linear)
        values.append(_objective(cfg, x))
    if len(values) != result.iterations + 1 or values[-1] != result.objective:
        raise ValueError("Code plotted trajectory lost its complete independent scalar recurrence")
    return values


def _line(x: Any, y: Any, label: str | None = None, transform: str = "data") -> dict[str, Any]:
    return {"x": list(x), "y": list(y), "label": label, "transform": transform}


def _horizontal(y: float, label: str | None = None) -> dict[str, Any]:
    return _line((0, 1), (y, y), label, "horizontal")


def _vertical(x: float, label: str | None = None) -> dict[str, Any]:
    return _line((x, x), (0, 1), label, "vertical")


def _bars(values: Any) -> list[dict[str, float]]:
    return [{"x": float(i) - 0.4, "y": 0.0, "width": 0.8, "height": float(value)} for i, value in enumerate(values)]


def _text(
    text: str,
    x: float,
    y: float,
    annotation: Any = None,
    *,
    coordinate: str = "data",
    xycoords: str = "data",
    textcoords: str = "offset points",
) -> dict[str, Any]:
    row = {"text": text, "position": [x, y], "annotation_xy": annotation, "coordinate": coordinate}
    if annotation is not None:
        row.update(coordinate="annotation", xycoords=xycoords, textcoords=textcoords)
    return row


def _axis(
    title: str,
    xlabel: str,
    ylabel: str,
    *,
    xscale: str = "linear",
    yscale: str = "linear",
    lines: Any = (),
    bars: Any = (),
    images: Any = (),
    texts: Any = (),
    legend: Any = None,
) -> dict[str, Any]:
    return dict(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        xscale=xscale,
        yscale=yscale,
        lines=list(lines),
        bars=list(bars),
        images=list(images),
        texts=list(texts),
        legend=legend,
        colorbar=None,
    )


def _agency(alpha: float) -> str:
    return (
        "Conservative" if alpha < 0.3 else "Near-optimal" if alpha <= 1 else "Aggressive" if alpha < 2 else "Divergent"
    )


def expected_figure_payloads(
    cfg: ScalarQuadraticConfig,
    csv: bytes,
    stability_report: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, dict[str, Any]]:
    """Compute exactly the configured series/panels used by the existing Source."""
    validate_scalar_csv(cfg, csv, deadline=deadline)
    validate_sdk_stability_report(cfg, stability_report, {}, frozenset(), deadline=deadline)
    # The actual ExperimentConfig normalizes authored integer alphas to floats.
    cfg = replace(
        cfg,
        step_sizes=tuple(float(alpha) for alpha in cfg.step_sizes),
        stability_step_sizes=tuple(float(alpha) for alpha in cfg.stability_step_sizes),
    )
    steps = cfg.step_sizes
    results = [_result(cfg, alpha, deadline) for alpha in steps]
    histories = [_history(cfg, alpha, deadline) for alpha in steps]
    f_star = _objective(cfg, cfg.linear / cfg.coefficient)
    labels = [f"α = {alpha} ({_agency(alpha)})" for alpha in steps]
    iterations = [row.iterations for row in results]
    errors = [math.log10(max(abs(row.objective - f_star), 1e-16)) for row in results]
    rho = [abs(1 - alpha) for alpha in steps]
    theory = [1 / (2 * alpha * (1 - r)) if 0 < r < 1 else math.inf for alpha, r in zip(steps, rho, strict=True)]
    convergence = [
        _line(range(len(h)), [min(100.0, max(-10.0, value)) for value in h], label)
        for h, label in zip(histories, labels, strict=True)
    ]
    convergence.append(_horizontal(f_star, f"Optimal: f(x*) = {f_star:.4g}"))
    first = _axis(
        "Gradient Descent Convergence Analysis\nQuadratic Minimization",
        "Iteration",
        "Objective Value f(x)",
        lines=convergence,
        legend=[*labels, f"Optimal: f(x*) = {f_star:.4g}"],
    )
    first["ylim"] = [-0.7, 10.0]
    tolerance = cfg.convergence_tolerance
    tol_str = f"{tolerance:.0e}".replace("e-0", "e-").replace("e+0", "e+")
    rates = [
        _line(range(min(50, len(h))), [abs(v - f_star) for v in h[:50]], label)
        for h, label in zip(histories, labels, strict=True)
    ]
    rates.append(_horizontal(tolerance))
    rate = _axis(
        "Convergence Rate Comparison\nLinear Convergence on Logarithmic Scale",
        "Iteration",
        "Absolute Error |f(x) − f(x*)|",
        yscale="log",
        lines=rates,
        legend=labels,
        texts=[
            _text(
                f"Tolerance ε = {tol_str}",
                0.85,
                0.35,
                [0.85, 0.35],
                xycoords="axes fraction",
                textcoords="axes fraction",
            )
        ],
    )
    rate["ylim"] = [1e-12, 1e4]
    swept = [_result(replace(cfg, max_iterations=500), alpha, deadline) for alpha in GRID]
    sweep_iterations = [row.iterations for row in swept]
    sweep_objectives = [row.objective for row in swept]
    sensitivity = [
        _axis(
            "Convergence Speed vs Step Size\nIterations decrease geometrically with α",
            "Step Size (α)",
            "Iterations to Convergence",
            xscale="log",
            yscale="log",
            lines=[_line(GRID, sweep_iterations)],
            texts=[
                _text(str(sweep_iterations[i]), 0, 10, [GRID[i], sweep_iterations[i]]) for i in (0, 4, len(GRID) - 1)
            ],
        ),
        _axis(
            f"Solution Quality vs Step Size\nAll stable step sizes reach f(x*)={f_star:.4g}",
            "Step Size (α)",
            "Final Objective Value",
            xscale="log",
            lines=[
                _line(GRID, sweep_objectives, "Achieved f(x)"),
                _horizontal(f_star, f"Optimal f(x*) = {f_star:.4g}"),
                _horizontal(0, "Initial f(x₀) = 0"),
            ],
            legend=["Achieved f(x)", f"Optimal f(x*) = {f_star:.4g}", "Initial f(x₀) = 0"],
        ),
    ]
    sensitivity[1]["ylim"] = [f_star - 0.1, 0.1]
    log_tol = math.log10(tolerance)
    widths = [2 / scale for _, scale in PROFILES]
    optimal = [1 / scale for _, scale in PROFILES]
    alpha_max = max(widths) * 1.05
    # Match the fixed NumPy linspace Source arithmetic/end-point contract.
    fine = [0.001 + i * ((alpha_max - 0.001) / 299) for i in range(300)]
    fine[-1] = alpha_max
    overlay = []
    for (name, scale), width in zip(PROFILES, widths, strict=True):
        overlay += [_line(fine, [abs(1 - a * scale) for a in fine], name), _vertical(width)]
    overlay.append(_horizontal(1, "ρ = 1 (divergence)"))
    complexity = [
        _axis(
            "Empirical Convergence Iterations",
            "Step Size",
            "Iterations",
            bars=_bars(iterations),
            texts=[_text(f"{value:.0f}", i, value + max(iterations) * 0.03) for i, value in enumerate(iterations)],
        ),
        _axis(
            "Solution Accuracy\n(Lower = More Accurate)",
            "Step Size",
            "log₁₀ |f(x) − f(x*)|",
            bars=_bars(errors),
            lines=[_horizontal(log_tol, f"ε = {tolerance:.0e} tolerance")],
            texts=[_text(f"{value:.1f}", i, min(value, 0) - 0.5) for i, value in enumerate(errors)],
            legend=[f"ε = {tolerance:.0e} tolerance"],
        ),
        _axis(
            "Theoretical vs Empirical Complexity",
            "Step Size (α)",
            "Iterations (log)",
            yscale="log",
            lines=[_line(steps, iterations, "Empirical"), _line(steps, theory, "Theoretical 1/(2α·L·(1−αL))")],
            legend=["Empirical", "Theoretical 1/(2α·L·(1−αL))"],
        ),
        _axis(
            "Error Contraction per Step (Identity (H=I))\nρ = |1 − αL|  (smaller ρ ⇒ faster)",
            "Step Size",
            "Contraction Factor ρ",
            bars=_bars(rho),
            lines=[
                _horizontal(1, "ρ = 1 (divergence boundary)"),
                _vertical(steps.index(min(steps, key=lambda a: abs(a - 1))), "α* = 1"),
            ],
            texts=[
                _text(f"{value:.3f}", i, value + (1 if value >= 0 else -1) * max(rho) * 0.03)
                for i, value in enumerate(rho)
            ],
            legend=["ρ = 1 (divergence boundary)", "α* = 1"],
        ),
        _axis(
            "Stable Region Width per Backend Profile\n2/L boundary and optimal α* = 1/L",
            "Backend Profile",
            "Step Size (α)",
            bars=[*_bars(widths), *_bars(optimal)],
            texts=[_text(f"{value:.3g}", i, value + max(widths) * 0.03) for i, value in enumerate(widths)],
            legend=["Stable width 2/L", "Optimal α* = 1/L"],
        ),
        _axis(
            "Cross-Profile Contraction Curves\nDotted verticals = 2/L stability boundary",
            "Step Size (α)",
            "Contraction Factor ρ = |1 − αL|",
            lines=overlay,
            legend=[*[name for name, _ in PROFILES], "ρ = 1 (divergence)"],
        ),
    ]
    for index in (0, 1, 3):
        complexity[index]["xticklabels"] = [f"α={step}" for step in steps]
    complexity[4]["xticklabels"] = [name for name, _ in PROFILES]
    complexity[3]["ylim"] = [0, max(1.05, max(rho) * 1.15)]
    complexity[5]["ylim"] = [0, 2.1]
    heat = []
    for point in cfg.stability_starting_points:
        row = []
        for alpha in cfg.stability_step_sizes:
            result = _result(replace(cfg, initial_point=point), alpha, deadline)
            row.append(math.log10(max(abs(result.objective - f_star), 1e-16)))
        heat.append(row)
    score = stability_report["stability_score"]
    cells = [value for row in heat for value in row]
    stability = [
        _axis(
            "Numerical Stability Heatmap\nlog₁₀ |f(x) − f(x*)|  (darker green = more accurate)",
            "Step Size",
            "Starting Point",
            images=[
                {
                    "array": heat,
                    "extent": [
                        -0.5,
                        len(cfg.stability_step_sizes) - 0.5,
                        len(cfg.stability_starting_points) - 0.5,
                        -0.5,
                    ],
                    "clim": [-16, 0],
                    "cmap": "RdYlGn_r",
                    "origin": "upper",
                }
            ],
            texts=[_text(f"{value:.0f}", j, i) for i, row in enumerate(heat) for j, value in enumerate(row)],
        ),
        _axis(
            f"Stability Score: {score:.2f}",
            "Stability Score",
            "",
            bars=[{"x": 0, "y": -0.2, "width": score, "height": 0.4}, {"x": 0, "y": -0.2, "width": 1, "height": 0.4}],
            texts=[
                _text(f"{score:.2f}", score + 0.02, 0),
                _text(f"Cells tested: {len(cells)}", 0.05, -0.8, coordinate="horizontal"),
                _text(f"Min error: 10^{min(cells):.0f}", 0.05, -1.2, coordinate="horizontal"),
                _text(f"Max error: 10^{max(cells):.0f}", 0.05, -1.6, coordinate="horizontal"),
            ],
        ),
        _axis("", "", "log₁₀ |error|"),
    ]
    stability[0]["xticklabels"] = [f"α={step}" for step in cfg.stability_step_sizes]
    stability[0]["yticklabels"] = [f"x₀={point:g}" for point in cfg.stability_starting_points]
    stability[1].update(xlim=[0, 1.1], ylim=[-2.5, 0.8], yticklabels=["Overall"])
    stability[2]["colorbar"] = {"clim": [-16, 0], "cmap": "RdYlGn_r"}
    work, counts = [], []
    for dimension in cfg.benchmark_dimensions:
        remaining(deadline)
        if dimension > 10000:
            raise ValueError("Code plotted identity benchmark exceeds its finite selected dimension bound")
        x, count = 0.0, 0
        while count < 500 and abs(x - 1) * math.sqrt(dimension) >= 1e-10:
            remaining(deadline)
            x -= 0.1 * (x - 1)
            count += 1
        counts.append(count)
        work.append(dimension * count)
    benchmark = [
        _axis(
            "Deterministic Work Proxy vs Dimension\nd × convergence iterations",
            "Problem Dimension (d)",
            "Dimension × Iterations (work units)",
            bars=_bars(work),
            texts=[_text(str(value), i, value + max(work) * 0.02) for i, value in enumerate(work)],
        ),
        _axis(
            "Convergence Iterations vs Dimension\nα=0.1, tol=10⁻¹⁰, identity Hessian",
            "Problem Dimension (d)",
            "Iterations to Convergence",
            bars=_bars(counts),
            texts=[_text(str(value), i, value + max(counts) * 0.02) for i, value in enumerate(counts)],
        ),
    ]
    for axis in benchmark:
        axis["xticklabels"] = [str(dimension) for dimension in cfg.benchmark_dimensions]
    expected_figures: dict[str, dict[str, Any]] = {
        name: {"axes": axes, "figure_texts": []}
        for name, axes in zip(SELECTED, ([first], [rate], sensitivity, complexity, stability, benchmark), strict=True)
    }
    expected_figures["algorithm_complexity.png"]["figure_texts"] = [
        {
            "text": "Algorithm Performance Analysis\nGradient Descent Convergence Characteristics",
            "position": [0.5, 1.01],
            "coordinate": "figure",
        }
    ]
    remaining(deadline)
    return expected_figures


def _equal(actual: Any, expected: Any, *, deadline: float) -> None:
    remaining(deadline)
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if not isinstance(actual, str):
            raise ValueError("Code figure numeric observation lost its exact binary64 encoding")
        value = float.fromhex(actual)
        if (
            math.isnan(value)
            or (math.isinf(expected) and value != expected)
            or (
                math.isfinite(expected)
                and (not math.isfinite(value) or not math.isclose(value, expected, rel_tol=1e-12, abs_tol=0.0))
            )
            or (value == expected == 0 and math.copysign(1, value) != math.copysign(1, expected))
        ):
            raise ValueError("Code figure plotted numeric meaning differs from independent Source recurrence")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError("Code figure lost/reordered its complete independent plotted roster")
        for left, right in zip(actual, expected, strict=True):
            _equal(left, right, deadline=deadline)
    elif isinstance(expected, dict):
        if not isinstance(actual, dict) or not set(expected) <= set(actual):
            raise ValueError("Code figure omitted an independent Source panel field")
        for key, value in expected.items():
            if key == "label" and value is None:
                label = actual[key]
                if not isinstance(label, str) or not label.startswith("_child") or not label[6:].isdigit():
                    raise ValueError("Code figure changed its implicit Source artist label")
            else:
                _equal(actual[key], value, deadline=deadline)
    elif actual != expected:
        raise ValueError("Code figure labels/scales/geometry differ from complete selected Source meaning")


def validate_figure_payload(name: str, observed: dict[str, Any], expected: dict[str, Any], *, deadline: float) -> None:
    """Check every selected scientific artist; retained placement stays native-owned."""
    if name not in SELECTED or set(observed) != {"producer", "save", "png", "axes", "figure_texts"}:
        raise ValueError("Code figure observation differs from the fixed actual selected Source fields")
    if observed["save"] != {"dpi": 300, "bbox_inches": "tight", "facecolor": "white", "edgecolor": "none"}:
        raise ValueError("Code actual figure save changed its Source flags")
    _equal(observed["axes"], expected["axes"], deadline=deadline)
    _equal(observed["figure_texts"], expected["figure_texts"], deadline=deadline)
