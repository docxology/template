# Experimental Setup

This section details the complete experimental configuration used to generate the results in this study. Every parameter value below is injected programmatically from `config.yaml` and the analysis pipeline — no value is hardcoded in the manuscript source.

## Problem Definition

The optimization target is the quadratic objective function:

\begin{equation}
\label{eq:quadratic_objective}
f(x) = \frac{1}{2} x^T A x - b^T x
\end{equation}

with $A = {{CONFIG_QUADRATIC_A}}$ and $b = {{CONFIG_QUADRATIC_B}}$, yielding the analytical optimum at $x^* = {{RESULT_OPTIMUM_X}}$ with $f(x^*) = {{RESULT_OPTIMUM_F}}$.

## Parameter Space

The experiment systematically varies the gradient descent step size across {{CONFIG_NUM_STEP_SIZES}} values:

{{CONFIG_STEP_SIZES_BULLETS}}

All runs start from the initial point $x_0 = {{CONFIG_INITIAL_POINT}}$ and use a convergence tolerance of $\|{\nabla f}\| < {{CONFIG_CONVERGENCE_TOL}}$ with a maximum iteration limit of $N_{\max} = {{CONFIG_MAX_ITERATIONS}}$.

## Numerical Stability Grid

To validate robustness, the optimizer is exercised across a grid of {{CONFIG_NUM_STABILITY_STARTS}} starting points and {{CONFIG_NUM_STABILITY_STEPS}} step sizes, producing {{CONFIG_STABILITY_CELLS}} total evaluations. This comprehensive sweep confirms that convergence is not an artifact of a narrow parameter choice.

## Dimensional Scaling

Performance benchmarking spans problem dimensions $d \in \{{{CONFIG_BENCHMARK_DIMS}}\}$, from the scalar case ($d = {{CONFIG_BENCHMARK_MIN_DIM}}$) to moderate dimensionality ($d = {{CONFIG_BENCHMARK_MAX_DIM}}$), using identity-Hessian quadratics to isolate algorithmic scaling from problem conditioning effects.

## Computational Environment

- **Python**: {{PYTHON_VERSION}}
- **NumPy**: {{NUMPY_VERSION}}
- **Platform**: {{PLATFORM}}
- **Generated**: {{GENERATION_TIMESTAMP}}

## Pipeline ordering

Typical `code_project` analysis order (see `scripts/02_run_analysis.py` discovery) is:

1. `optimization_analysis.py` — writes `output/data/optimization_results.csv`, `output/figures/*.png`, and JSON reports under `output/reports/`.
2. `z_generate_manuscript_variables.py` — reads the CSV and YAML, emits `output/data/manuscript_variables.json`, and writes substituted copies to `output/manuscript/` for rendering.
3. `generate_api_docs.py` — refreshes API markdown consumed by documentation targets.

PDF compilation then reads from `output/manuscript/` so that figure paths and numeric tables match the analysis that just completed.

## Relation to figures

| Figure (Section 3) | Primary inputs |
|--------------------|------------------|
| Convergence trajectories | `experiment.step_sizes`, `initial_point`, `tolerance`, `max_iterations` |
| Step-size sensitivity | Dense $\alpha$ sweep internal to `generate_step_size_sensitivity_plot()` |
| Convergence rate | Same trajectories as above; tolerance line uses `convergence_tolerance` |
| Complexity quad panel | One bar chart per row of `optimization_results.csv` |
| Stability heatmap | `stability_starting_points` $\times$ `stability_step_sizes` |
| Dimensional benchmark | `benchmark_dimensions`, fixed $\alpha=0.1$, internal tol $10^{-10}$ |

This table is descriptive documentation only; it is not executed as code during the build.
