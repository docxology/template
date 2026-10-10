"""Real artists and independent finite math; no NativeOwner or pass factories."""

from __future__ import annotations

import time
from dataclasses import replace

import pytest
from matplotlib.figure import Figure

from infrastructure.core.analysis_figure_custody import SAVE, observe_figure
from infrastructure.reporting.native_code_figure_domains import expected_figure_payloads, validate_figure_payload
from infrastructure.reporting.native_code_value_predicate import ScalarQuadraticConfig


def _configured() -> tuple[ScalarQuadraticConfig, bytes, dict[str, object]]:
    cfg = ScalarQuadraticConfig((1.0,), 1.0, 1.0, 0.0, 2, 1e-9, 1e-6, (0.0,), (0.5,), (1,))
    csv = (
        b"step_size,solution,objective_value,iterations,converged,gradient_norm,termination_reason\n"
        b"1.0,1.000000,-0.500000,1,True,0.00e+00,converged\n"
    )
    report = {
        "function_name": "quadratic_function",
        "stability_score": 1.0,
        "expected_behavior": "Stable numerical behavior across input range",
        "actual_behavior": "Stability score: 1.00",
        "recommendations": [],
    }
    return cfg, csv, report


@pytest.mark.parametrize(
    "control", ["baseline", "integer-alpha", "changed-series", "changed-axis-meaning", "changed-scale", "extra-series"]
)
def test_real_convergence_artists_detect_selected_domain_mutants(control: str) -> None:
    cfg, csv, report = _configured()
    if control == "integer-alpha":
        cfg = replace(cfg, step_sizes=(1,), stability_step_sizes=(1,))
    deadline = time.monotonic() + 10
    payloads = expected_figure_payloads(cfg, csv, report, deadline=deadline)
    expected = payloads["convergence_plot.png"]
    if control == "integer-alpha":
        assert payloads["algorithm_complexity.png"]["axes"][0]["xticklabels"] == ["α=1.0"]
        assert payloads["stability_analysis.png"]["axes"][0]["xticklabels"] == ["α=1.0"]
    figure = Figure()
    ax = figure.subplots()
    ax.plot([0, 1], [0, -0.5], label="α = 1.0 (Near-optimal)")
    ax.axhline(-0.5, label="Optimal: f(x*) = -0.5")
    ax.set_title("Gradient Descent Convergence Analysis\nQuadratic Minimization")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Objective Value f(x)")
    ax.set_ylim(-0.7, 10)
    ax.legend()
    if control == "changed-series":
        ax.lines[0].set_ydata([0, -0.4])
    elif control == "changed-axis-meaning":
        ax.set_ylabel("Elapsed time")
    elif control == "changed-scale":
        ax.set_yscale("symlog")
    elif control == "extra-series":
        ax.plot([0, 1], [0, -0.5])
    observed = {"producer": {}, "png": {}, "save": SAVE, "axes": observe_figure(figure), "figure_texts": []}
    if control in ("baseline", "integer-alpha"):
        validate_figure_payload("convergence_plot.png", observed, expected, deadline=deadline)
    else:
        with pytest.raises(ValueError):
            validate_figure_payload("convergence_plot.png", observed, expected, deadline=deadline)


def test_independent_payloads_keep_exact_stability_and_benchmark_roles() -> None:
    cfg, csv, report = _configured()
    values = expected_figure_payloads(cfg, csv, report, deadline=time.monotonic() + 10)
    stability = values["stability_analysis.png"]["axes"]
    # Two alpha=.5 updates from x0=0 leave x=.75; objective=-.46875,
    # so the heatmap is log10(.03125), distinct from objective SDK score=1.
    assert stability[0]["images"][0]["array"][0][0] == pytest.approx(-1.505149978319906)
    assert stability[1]["bars"][0]["width"] == 1.0
    benchmark = values["performance_benchmark.png"]["axes"]
    # The benchmark uses its explicit identity/alpha=.1/tol=1e-10/500 cap,
    # independently of the experiment's alpha=1/max_iterations=2.
    assert benchmark[0]["bars"][0]["height"] == 219.0
    assert benchmark[1]["bars"][0]["height"] == 219.0


def test_real_artist_capture_retains_image_bar_and_annotation_coordinates() -> None:
    figure = Figure()
    ax = figure.subplots()
    ax.bar([0], [3.0])
    image = ax.imshow([[0.5, 1.0]], vmin=0, vmax=1, origin="upper")
    figure.colorbar(image, ax=ax)
    ax.text(0.05, -0.8, "Cells tested: 2", transform=ax.get_yaxis_transform())
    ax.annotate("3", (0, 3), xytext=(0, 10), textcoords="offset points")
    observed = observe_figure(figure)[0]
    assert float.fromhex(observed["bars"][0]["height"]) == 3
    assert [[float.fromhex(value) for value in row] for row in observed["images"][0]["array"]] == [[0.5, 1.0]]
    assert observed["texts"][0]["coordinate"] == "horizontal"
    assert observed["texts"][1]["coordinate"] == "annotation"
    assert observed["texts"][1]["xycoords"] == "data"
    assert observed["texts"][1]["textcoords"] == "offset points"


def test_unknown_actual_collection_cannot_disappear_from_capture() -> None:
    figure = Figure()
    ax = figure.subplots()
    ax.plot([0, 1], [0, -0.5])
    ax.scatter([0], [4])
    with pytest.raises(ValueError, match="unsupported actual Source collection"):
        observe_figure(figure)


@pytest.mark.parametrize("control", ["reordered-csv", "wrong-SDK-score", "unknown-figure"])
def test_unqualified_source_domains_do_not_gain_a_figure_meaning(control: str) -> None:
    cfg, csv, report = _configured()
    deadline = time.monotonic() + 10
    if control == "reordered-csv":
        csv = csv.replace(b"1.0,", b"0.5,")
    elif control == "wrong-SDK-score":
        report = {**report, "stability_score": 0.7}
    with pytest.raises(ValueError):
        values = expected_figure_payloads(cfg, csv, report, deadline=deadline)
        validate_figure_payload("benchmark_timings.png", {}, values["performance_benchmark.png"], deadline=deadline)
