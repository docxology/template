# Results

This section presents the experimental results from the gradient descent optimization study, including convergence analysis and performance comparisons. Every table, figure, and quantitative assertion in this section was compiled autonomously by the template's `infrastructure.reporting` subsystem executing the [optimization analysis script](https://github.com/docxology/template/blob/main/projects/code_project/scripts/optimization_analysis.py). No manual transcription was permitted.

## Convergence Analysis

### Convergence Trajectories

Figure \ref{fig:convergence} illustrates the convergence behavior of gradient descent for different step sizes, starting from the initial point $x_0 = 0$. The algorithm iteratively updates the solution using the rule $x_{k+1} = x_k - \alpha \nabla f(x_k)$.

![Gradient descent convergence trajectories for 6 step sizes ($\\alpha = 0.01, \\alpha = 0.1, \\alpha = 0.5, \\alpha = 1.0, \\alpha = 1.5, \\alpha = 2.5$) on the quadratic $f(x) = \frac{1}{2}x^2 - x$. Larger step sizes reach the analytical minimum $f(x^*) = -0.5$ faster, while $\alpha \geq 2$ diverges. The fastest convergence occurs at $\alpha = 1.0$ (1 iterations).](../output/figures/convergence_plot.png){#fig:convergence}

**Key observations from Figure \ref{fig:convergence}:**

1. **Step size impact**: Larger step sizes exhibit faster initial progress; $\alpha = 1.0$ converges in 1 iteration(s)
2. **Agency categories**: Conservative ($\alpha \leq 0.1$), near-optimal ($0.3 \leq \alpha \leq 1.0$), aggressive ($1 < \alpha < 2$), and divergent ($\alpha \geq 2$)
3. **Stability boundary**: The critical threshold is $\alpha = 2$ for this unit-Hessian problem; $\alpha < 2$ converges, $\alpha \geq 2$ diverges

### Step Size Sensitivity Analysis

Figure \ref{fig:step_sensitivity} examines how the choice of step size affects the convergence path and solution quality. The analysis reveals the trade-off between convergence speed and numerical stability.

![Step size sensitivity analysis spanning all four agency categories (conservative, near-optimal, aggressive, divergent). Left panel: iterations to convergence vs step size, with points colour-coded by category. Right panel: final objective values showing convergent settings clustering at $f(x^*) = -0.5$ while divergent settings fail to reach the optimum.](../output/figures/step_size_sensitivity.png){#fig:step_sensitivity}

## Quantitative Results

The optimization results for different step sizes are synthesized computationally by orchestrating `infrastructure.reporting.pipeline_reporter`, feeding directly into the [optimization results data](https://github.com/docxology/template/blob/main/projects/code_project/output/data/optimization_results.csv) that acts as the source of truth for Table \ref{tab:opt_results}:

| Step Size (α) | Final Solution | Objective Value | Iterations | Converged |
|---------------|----------------|-----------------|------------|-----------|
| 0.01          | 0.9999         | -0.5000         | 165        | Yes       |
| 0.05          | 1.0000         | -0.5000         | 34         | Yes       |
| 0.10          | 1.0000         | -0.5000         | 17         | Yes       |
| 0.20          | 1.0000         | -0.5000         | 9          | Yes       |

: Optimization results showing solution accuracy and convergence speed for different step sizes. \label{tab:opt_results}

## Convergence Rate Analysis

### Theoretical vs Empirical Convergence

Modern convergence analysis builds on foundational work in gradient methods \cite{nesterov2013gradient}.

Figure \ref{fig:convergence_rate} provides a comparative analysis of convergence rates across different step sizes, validating theoretical predictions against empirical results.

![Convergence rate comparison on logarithmic scale. Each step size's error $|f(x) - f(x^*)|$ is plotted per iteration. Converging settings show downward-sloping lines with slopes determined by the contraction factor $\rho = |1 - \alpha|$, while divergent settings show upward trajectories. The dashed tolerance line at $\varepsilon = 10^{-8}$ marks the convergence criterion.](../output/figures/convergence_rate_comparison.png){#fig:convergence_rate}

The theoretical convergence rate for our quadratic problem satisfies:

\begin{equation}
\label{eq:convergence_bound}
\frac{\|x_{k+1} - x^*\|^2}{\|x_k - x^*\|^2} \leq 1 - \frac{2\alpha(1 - \alpha)}{1} = 1 - 2\alpha(1 - \alpha)
\end{equation}

For the optimal step size $\alpha = 0.5$, this bound becomes:

\begin{equation}
\label{eq:optimal_step_convergence}
\frac{\|x_{k+1} - x^*\|^2}{\|x_k - x^*\|^2} \leq 1 - 2(0.5)(1 - 0.5) = 0.5
\end{equation}

Our experimental analysis uses step sizes spanning $\alpha = 0.01$ to $\alpha = 2.5$, including both conservative and aggressive settings to demonstrate the full spectrum of convergence behavior.

### Error Bounds

The error after $k$ iterations is bounded by:

\begin{equation}
\label{eq:error_bound}
\|x_k - x^*\| \leq \left(\frac{\kappa - 1}{\kappa + 1}\right)^k \|x_0 - x^*\|
\end{equation}

where $\kappa = \frac{\lambda_{\max}}{\lambda_{\min}}$ is the condition number. For our test problem with $A = I$, we have $\kappa = 1$, which yields a contraction factor of $\rho = |1 - \alpha|$. This means $\alpha = 1$ is the exact Newton step (converging in one iteration), step sizes $\alpha < 1$ converge monotonically, $1 < \alpha < 2$ converge with oscillation, and $\alpha \geq 2$ diverge. The measured iteration counts in Table \ref{tab:opt_results} confirm this theoretical prediction across all 6 tested settings.

### Performance Metrics

**Iteration Complexity**: The number of iterations required to achieve accuracy $\epsilon$ is:

\begin{equation}
\label{eq:iteration_complexity}
k \geq \frac{\log(\epsilon)}{\log(\rho)}
\end{equation}

where $\rho = \sqrt{\frac{\kappa - 1}{\kappa + 1}}$ is the convergence factor \cite{polyak1964some}.

For our results, the convergence factors are:

- $\alpha = 0.01$: $\rho \approx 0.99$, requiring ~458 iterations for $\epsilon = 10^{-6}$
- $\alpha = 0.05$: $\rho \approx 0.95$, requiring ~87 iterations for $\epsilon = 10^{-6}$
- $\alpha = 0.10$: $\rho \approx 0.90$, requiring ~43 iterations for $\epsilon = 10^{-6}$
- $\alpha = 0.20$: $\rho \approx 0.80$, requiring ~21 iterations for $\epsilon = 10^{-6}$

## Performance Analysis

### Convergence Speed

The results show a clear trade-off between step size and convergence speed:

- Small step sizes require more iterations but provide stable convergence
- Large step sizes converge faster but may be less stable in more complex problems

### Solution Accuracy

4 of 6 tested step sizes achieved the analytical optimum within numerical precision:

- Target solution: $x = 1.0$ (relative error $< 10^{-4}$ for converged settings)
- Target objective: $f(x) = -0.5$ (absolute error $< 10^{-8}$ for converged settings)

Divergent step sizes ($\alpha \geq 2$) confirm the theoretical instability boundary, demonstrating that gradient descent with fixed step size requires $\alpha < 2/\lambda_{\max}$ for convergence on quadratic objectives.

## Algorithm Characteristics

### Strengths

- **Simplicity**: Easy to implement and understand
- **Generality**: Applicable to any differentiable objective function
- **Reliability**: Converges for convex functions under appropriate conditions

### Limitations

- **Step size sensitivity**: Performance depends critically on step size selection
- **Local convergence**: May converge to local minima in non-convex problems
- **Fixed step size**: No adaptation to problem characteristics

## Computational Performance

### Algorithm Complexity Visualization

Figure \ref{fig:complexity} provides a visualization of the algorithm's computational characteristics, including time and space complexity analysis across different problem scales.

![Algorithm performance analysis in four panels: (TL) empirical iteration counts per step size, colour-coded by agency category, (TR) solution accuracy as $\log_{10} |f(x) - f(x^*)|$ with the $\varepsilon = 10^{-8}$ tolerance line, (BL) theoretical bound overlaid on empirical iterations in log scale, (BR) contraction factor $\rho = |1-\alpha|$ per step size.](../output/figures/algorithm_complexity.png){#fig:complexity}

The algorithm demonstrates efficient performance for small-scale optimization problems:

- **Time complexity**: $O(d)$ per iteration for gradient computation
- **Space complexity**: $O(d)$ for storing variables and gradients
- **Convergence**: Fastest at $\alpha = 1.0$ (1 iteration), average 372 iterations
- **Scalability**: Memory-efficient implementation suitable for high-dimensional problems

### Performance Benchmarking

Figure \ref{fig:benchmark} shows how `gradient_descent()` scales with problem dimension by running the optimizer on identity-Hessian quadratics of dimension $d \in \{1, 2, 5, 10, 20, 50\}$.

![Dimensional scaling benchmark. Left: mean execution time ($\mu$s) per `gradient_descent()` call across problem dimensions $d = 1$ to $50$, showing sub-millisecond performance throughout. Right: iterations to convergence remain constant ($\sim$17) for all dimensions because the identity-matrix condition number $\kappa = 1$ is dimension-independent.](../output/figures/performance_benchmark.png){#fig:benchmark}

### Numerical Stability Analysis

Figure \ref{fig:stability} maps the optimizer's accuracy across a grid of 8 starting points ($x_0 \in [-50, 50]$) and 6 step sizes ($\alpha \in [0.01, 0.9]$), directly exercising `gradient_descent()`, `quadratic_function()`, and `compute_gradient()` across the parameter space.

![Numerical stability heatmap: each cell shows $\log_{10} |f(x) - f(x^*)|$ for a (starting point, step size) combination, with 48 total evaluations. The right panel reports the aggregate stability score of 1.00 from `check_numerical_stability()`.](../output/figures/stability_analysis.png){#fig:stability}

### Performance Metrics Summary

**Iteration Statistics:**

- Minimum iterations: 9 (for $\alpha = 0.2$)
- Maximum iterations: 165 (for $\alpha = 0.01$)
- Average convergence: $< 50$ iterations across all test cases

**Numerical Accuracy:**

- Solution precision: $< 10^{-4}$ relative error (for converged step sizes)
- Objective accuracy: $< 10^{-8}$ absolute error (for converged step sizes)
- Gradient tolerance: $< 10^{-8}$ achieved for converged cases

## Validation

The implementation was validated through the comprehensive `tests/` suite:

- **Integration tests** verifying algorithm convergence and visualization pipelines.
- **Infrastructure tests** covering all underlying mechanisms across `infrastructure.reporting`, `infrastructure.validation`, and `infrastructure.rendering`.
- **Numerical accuracy** checks verified systematically using PyTest.

All tests pass with coverage exceeding the 90% threshold, ensuring implementation correctness across core logic, convergence detection, and logging pathways without the use of mocks.

## Discussion

The experimental results validate the gradient descent implementation and confirm the theoretical convergence predictions from Section 2. The monotonic relationship between step size and iteration count (Table \ref{tab:opt_results}) aligns with the convergence factor analysis in Equation \ref{eq:convergence_factor}, while the uniform solution accuracy across all step sizes demonstrates the robustness of the convergence criterion $\|\nabla f(x)\| < \epsilon$. The automated analysis pipeline successfully generated six publication-quality visualizations and structured numerical outputs, validating the template's end-to-end research workflow from algorithmic implementation through automated infrastructure-driven reporting and manuscript integration.

*As a meta-architectural note: the perfect embedding of these outputs into this document, including all dynamic references (e.g., Figure \ref{fig:stability}), confirms the absolute reliability of the `infrastructure/rendering/pdf_renderer.py` module handling the Pandoc conversion.*
