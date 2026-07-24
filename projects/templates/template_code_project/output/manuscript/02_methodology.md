# Methodology {#sec:methodology}

This section describes the implementation methodology, explicitly detailing how the optimization algorithms are constructed, validated, and analyzed using the Generalized Research Template's `infrastructure` and `tests` ecosystems.

## Algorithm Implementation

### Gradient Descent Algorithm

The core algorithm implements the iterative procedure for unconstrained optimization. The [`optimizer` module](https://github.com/docxology/template/blob/main/projects/templates/template_code_project/src/optimizer.py) uses the standard-library `logging` logger for optional verbose diagnostics; the [analysis orchestrator](https://github.com/docxology/template/blob/main/projects/templates/template_code_project/scripts/optimization_analysis.py) uses `infrastructure.core.logging.utils.get_logger`. Tests run under the hermetic boundaries defined in the [test configuration](https://github.com/docxology/template/blob/main/projects/templates/template_code_project/tests/conftest.py).

**Algorithm — Gradient Descent (implemented in the [optimizer module](https://github.com/docxology/template/blob/main/projects/templates/template_code_project/src/optimizer.py#L87-L173))**

> **Input:** Initial point $x_0$, step size $\alpha$, tolerance $\epsilon$, max iterations $N_{\max}$
>
> 1. Initialize $k \leftarrow 0$
> 2. **While** $k < N_{\max}$ **do:**
>    - Compute gradient $g_k = \nabla f(x_k)$
>    - **If** $\|g_k\|_2 < \epsilon$ **then return** $x_k$ *(converged)*
>    - Update: $x_{k+1} \leftarrow x_k - \alpha \cdot g_k$
>    - $k \leftarrow k + 1$
> 3. **Return** $x_k$ *(max iterations reached)*

## Infrastructure Integration

The methodology explicitly bridges theoretical mathematics with production-grade validation through the `infrastructure.scientific` module.

### Numerical Stability Analysis

Rather than writing ad-hoc validation code, the project imports `infrastructure.scientific.stability.check_numerical_stability`. This utility subjects the objective function to a barrage of extreme inputs (NaN, Inf, $\pm 10^{10}$) to calculate a formalized stability score. If this score degrades, the [analysis orchestrator](https://github.com/docxology/template/blob/main/scripts/pipeline/stage_02_analysis.py) execution deliberately aborts, ensuring the methodology cannot enter unrecoverable states.

### Performance Benchmarking

The analysis exercises [`infrastructure.scientific.benchmarking.benchmark_function`](https://github.com/docxology/template/blob/main/infrastructure/scientific/benchmarking.py) as a runtime diagnostic. Host-dependent timing and memory observations are logged but excluded from tracked evidence. The canonical report records fixed inputs and exact objective values, while the dimensional figure reports deterministic convergence iterations and the proxy $d \times \text{iterations}$; neither surface claims that one host run proves an asymptotic bound.

## Convergence Analysis

For quadratic functions $f(x) = \frac{1}{2}x^T A x - b^T x$ where $A$ is positive definite, the convergence factor becomes [@bertsekas1999nonlinear]:

\begin{equation}
\label{eq:convergence_factor}
\rho = \frac{|\lambda_{\max} - \alpha\lambda_{\min}|}{|\lambda_{\min} + \alpha\lambda_{\max}|}
\end{equation}

Optimal convergence occurs when $\alpha = \frac{2}{\lambda_{\min} + \lambda_{\max}}$, yielding $\rho = \frac{\kappa - 1}{\kappa + 1}$.

## Experimental Setup

### Step Size Analysis

Step sizes are not chosen ad hoc in the manuscript: they are read from `experiment.step_sizes` in `manuscript/config.yaml` and passed through `run_convergence_experiment()` in `src/analysis/` (entry: `scripts/optimization_analysis.py`). The active grid for this build is:

- $\alpha = 0.01$ (conservative)
- $\alpha = 0.1$ (conservative)
- $\alpha = 0.5$ (near-optimal)
- $\alpha = 1.0$ (near-optimal)
- $\alpha = 1.5$ (aggressive)
- $\alpha = 2.5$ (divergent (expected unstable for H = I))

Labels follow the same agency taxonomy used for plot colours (`_agency_category` in the analysis script): **conservative** (small $\alpha$, slow but stable on $H=I$), **near-optimal** (including $\alpha=1$ where the method reaches $x^\ast$ in one step for this quadratic), **aggressive** ($1 < \alpha < 2$, still linearly contracting in $|x-x^\ast|$ but oscillatory in sign), and **divergent** ($|1-\alpha| \geq 1$).

### Zero-Mock Testing Methodology

The most critical aspect of the project's methodology is its validation framework. The project is governed by a strict Zero-Mock testing policy, evaluated actively by executing `uv run pytest projects/templates/template_code_project/tests/` during the infrastructure build phase.

1. **Project tests**: [`projects/templates/template_code_project/tests/test_optimizer.py`](../tests/test_optimizer.py) exercises `src/optimizer.py` (typical, edge, boundary, and pathological inputs including NaN/Inf and zero gradients) and, when infrastructure imports succeed, call into `optimization_analysis.py` helpers—without mocks. Suite size: [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).
2. **Infrastructure validation**: The repository-level `tests/infra_tests/` suite validates shared template modules (e.g. pipeline and discovery helpers) independently of this project’s manuscript.
3. **Coverage Gates**: The [GitHub Actions CI workflow](https://github.com/docxology/template/blob/main/.github/workflows/ci.yml) enforces a mandatory ≥90% statement coverage gate on `projects/templates/template_code_project/src/` prior to treating the project as build-green.

### Stopping rule and reporting

`gradient_descent()` terminates when $\|\nabla f(x_k)\|$ falls below `experiment.tolerance`, when $k$ reaches `experiment.max_iterations`, or when an objective, gradient, or update becomes non-finite. The boolean `converged` plus `termination_reason` in exported CSV rows distinguish these outcomes. A non-finite candidate is rejected before it enters `objective_history`, preserving the last finite state for reproducible reporting. Downstream, `scripts/z_generate_manuscript_variables.py` aggregates the CSV into `RESULT_*` placeholders so tables and prose cannot drift from the last analysis run.

### Figure generation contract

Each figure in `03_results.md` maps to a generator in `src/figures/` (`generate_convergence_plot`, `generate_step_size_sensitivity_plot`, `generate_convergence_rate_plot`, `generate_complexity_visualization`, `generate_stability_visualization`, `generate_benchmark_visualization`), orchestrated by `src/analysis/` / `scripts/optimization_analysis.py`. Captions in the markdown intentionally name the function and the key parameters (tolerance lines, grids, dimensions) so reviewers can navigate from PDF to code without inferring hidden defaults.

The same generator writes explicit `metadata.alt_text` for every registered
figure. The alt text states what the visual encodes and preserves the boundary
between deterministic observations and host-dependent diagnostics. Run the
opt-in publication migration gate with
`--require-figure-accessibility` to verify that every referenced figure has
this metadata before promotion.

## Analysis Pipeline & LaTeX Integration

The automated analysis script leverages [`infrastructure.core.progress`](https://github.com/docxology/template/blob/main/infrastructure/core/progress.py) (`ProgressBar`, `SubStageProgress`) to orchestrate experiments, collect convergence trajectories, and generate publication-quality visualizations seamlessly.

The research template supports advanced LaTeX customization through the `preamble.md` configuration. This is ingested directly by `infrastructure.rendering.latex_utils.py` and `pdf_renderer.py`, automatically linking compiled PGF plots and BibTeX citations. This automated approach ensures an unbreakable chain of custody from raw algorithmic execution to the final rendered manuscript.
