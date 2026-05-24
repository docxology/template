| Module | Name | Kind | Summary |
|---|---|---|---|
| `analysis` | `extract_optimization_metadata` | function | Extract publication metadata from optimization results. |
| `analysis` | `generate_citations_from_metadata` | function | Generate citations from optimization metadata. |
| `analysis` | `main` | function | Main analysis function. |
| `analysis` | `register_figure` | function | Register the generated figures for manuscript reference. |
| `analysis` | `run_convergence_experiment` | function | Run gradient descent with different step sizes and track convergence. |
| `analysis` | `run_performance_benchmarking` | function | Benchmark gradient descent performance. |
| `analysis` | `run_stability_analysis` | function | Assess numerical stability of optimization algorithms. |
| `analysis` | `save_optimization_results` | function | Save optimization results to CSV file. |
| `analysis` | `save_publishing_materials` | function | Save publishing materials to output directory. |
| `analysis` | `save_validation_report` | function | Save validation report to file. |
| `analysis` | `validate_generated_outputs` | function | Validate integrity of generated analysis outputs. |
| `dashboard` | `main` | function |  |
| `documentation` | `build_api_reference_markdown` | function | Return markdown API reference for the optimization exemplar. |
| `documentation` | `run_api_doc_generation` | function | Generate glossary-style API index and static API reference markdown. |
| `experiment_config` | `ExperimentConfig` | class | Frozen experiment parameters from ``config.yaml`` → ``experiment:``. |
| `experiment_config` | `load_experiment_config` | function | Load experiment parameters from ``manuscript/config.yaml``. |
| `figures` | `apply_visualization_style` | function | Apply global matplotlib style for publication-quality, accessible figures. |
| `figures` | `generate_benchmark_visualization` | function | Generate dimensional scaling benchmark by running gradient_descent at d=1..50. |
| `figures` | `generate_complexity_visualization` | function | Generate algorithm performance analysis with 4 informative panels. |
| `figures` | `generate_convergence_plot` | function | Generate convergence plot showing objective value vs iteration. |
| `figures` | `generate_convergence_rate_plot` | function | Generate convergence rate comparison plot. |
| `figures` | `generate_stability_visualization` | function | Generate heatmap of optimizer accuracy across starting points and step sizes. |
| `figures` | `generate_step_size_sensitivity_plot` | function | Generate step size sensitivity analysis with expanded range. |
| `invariants` | `InvariantResult` | class | Witness record for one numerical invariant. |
| `invariants` | `OptimizerSweepConfig` | class | Configurable knobs driving every optimization invariant. |
| `invariants` | `all_invariants` | function | Every invariant the dashboard / plaintext report should display. |
| `invariants` | `convergence_invariants` | function | For every step size α with ``α < 2/λ_max(A)``: gradient descent must converge to ``x* = A^{-1} b`` and the objective history must be monotone non-increasing. |
| `invariants` | `gradient_consistency_invariants` | function | Numerical-vs-analytical gradient agreement to floating tolerance. |
| `invariants` | `trajectory_invariants` | function | ``simulate_trajectory`` is monotone for every stable step size. |
| `manuscript_variables` | `generate_variables` | function | Generate all manuscript variables from config and analysis outputs. |
| `manuscript_variables` | `save_variables` | function | Persist *variables* as JSON for downstream rendering and debugging. |
| `optimizer` | `OptimizationResult` | class | Result container from gradient_descent. |
| `optimizer` | `compute_gradient` | function | Compute ∇f(x) = A x - b for the quadratic objective. A defaults to identity, b to ones. |
| `optimizer` | `gradient_descent` | function | Run gradient descent: x_{k+1} = x_k - α ∇f(x_k) until convergence or max_iterations. |
| `optimizer` | `make_quadratic_problem` | function | Create paired (objective, gradient) callables for a quadratic problem. |
| `optimizer` | `quadratic_function` | function | Evaluate f(x) = (1/2) x^T A x - b^T x. A defaults to identity, b to ones. |
| `optimizer` | `quadratic_optimum` | function | Return (x*, f*) for f(x) = ½ xᵀ A x − bᵀ x. |
| `optimizer` | `simulate_trajectory` | function | Run gradient descent and return iteration/objective history. |
