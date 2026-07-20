| Module | Name | Kind | Summary |
|---|---|---|---|
| `analysis` | `AlgorithmComparison` | class | Ranked cross-algorithm comparison for gradient-descent variants. |
| `analysis` | `AlgorithmVariant` | class | Descriptor for one gradient-descent configuration under comparison. |
| `analysis` | `MultiFactorReport` | class | Multi-factor analysis combining convergence, stability, and performance. |
| `analysis` | `compare_algorithms` | function | Compare gradient-descent variants across all configured step sizes. |
| `analysis` | `multi_factor_analysis` | function | Combine convergence, stability, and performance into a composite score. |
| `analysis.experiments` | `run_convergence_experiment` | function | Run gradient descent with different step sizes and track convergence. |
| `analysis.experiments` | `save_optimization_results` | function | Save optimization results to CSV file. |
| `analysis.publishing` | `extract_optimization_metadata` | function | Extract publication metadata from optimization results. |
| `analysis.publishing` | `generate_citations_from_metadata` | function | Generate citations from optimization metadata. |
| `analysis.publishing` | `save_publishing_materials` | function | Save publishing materials to output directory. |
| `analysis.scientific_reports` | `register_figure` | function | Register generated figures for manuscript reference. |
| `analysis.scientific_reports` | `run_performance_benchmarking` | function | Run timing diagnostics and write a deterministic benchmark contract. |
| `analysis.scientific_reports` | `run_stability_analysis` | function | Assess numerical stability of optimization algorithms. |
| `analysis.scientific_reports` | `save_validation_report` | function | Save validation report to file. |
| `analysis.scientific_reports` | `validate_generated_outputs` | function | Validate integrity of generated analysis outputs. |
| `analysis.workflow` | `main` | function | Run the full optimization analysis pipeline. |
| `analysis.workflow` | `run_analysis_pipeline` | function | Execute the full optimization analysis workflow. |
| `benchmark_support` | `BenchmarkRun` | class | Full benchmark run: measurements plus infra-scored rubric result. |
| `benchmark_support` | `TimingMeasurement` | class | One benchmark measurement; timing is a runtime-only diagnostic. |
| `benchmark_support` | `benchmark_payload` | function | Convert a run into a byte-stable, JSON-safe canonical payload. |
| `benchmark_support` | `run_quadratic_benchmark` | function | Evaluate the pure quadratic objective and score deterministic facts. |
| `benchmark_support` | `write_benchmark_report` | function | Write the benchmark payload as JSON and return the path. |
| `dashboard` | `build_dashboard_html` | function | Build the dashboard with config defaults and write HTML to ``output/web/``. |
| `dashboard` | `cli_main` | function | Build dashboard artifacts from CLI arguments. |
| `dashboard` | `parse_dashboard_args` | function | Parse CLI arguments for the dashboard builder. |
| `dashboard_panels` | `build_dashboard` | function | Build dashboard. |
| `dashboard_panels` | `to_dashboard_invariant` | function | Convert this object to dashboard invariant. |
| `dashboard_payload` | `compute_payload` | function | Process compute payload. |
| `dashboard_payload` | `load_yaml_defaults` | function | Load experiment defaults from ``manuscript/config.yaml``. |
| `dashboard_payload` | `to_diagonal_A` | function | Convert this object to diagonal A. |
| `documentation` | `build_api_reference_markdown` | function | Return markdown API reference for the optimization exemplar. |
| `experiment_config` | `ExperimentConfig` | class | Frozen experiment parameters from ``config.yaml`` → ``experiment:``. |
| `experiment_config` | `load_experiment_config` | function | Load experiment parameters from ``manuscript/config.yaml``. |
| `figures.convergence` | `generate_convergence_plot` | function | Generate convergence plot showing objective value vs iteration. |
| `figures.convergence` | `generate_convergence_rate_plot` | function | Generate convergence rate comparison plot. |
| `figures.scientific_complexity` | `BackendProfile` | class | Descriptor for a gradient-descent backend variant. |
| `figures.scientific_complexity` | `compare_profiles_at_alpha` | function | Compare all backend profiles at a single step size. |
| `figures.scientific_complexity` | `compute_complexity_profile` | function | Build per-step-size complexity metrics for one backend profile. |
| `figures.scientific_complexity` | `compute_contraction_factor` | function | Compute the per-step contraction factor ρ = |1 − α · L|. |
| `figures.scientific_complexity` | `compute_theoretical_complexity` | function | Estimate iteration count to reduce error by 1/e from the linear rate bound. |
| `figures.scientific_complexity` | `generate_complexity_visualization` | function | Generate algorithm performance analysis with six informative panels. |
| `figures.scientific_complexity` | `optimal_step_size` | function | Return the theoretically optimal step size ``α* = 1/L``. |
| `figures.scientific_complexity` | `profile_stable_region` | function | Return ``(alpha_min, alpha_max)`` of the strictly stable step-size interval. |
| `figures.scientific_stability` | `generate_benchmark_visualization` | function | Generate a deterministic dimensional-work benchmark figure. |
| `figures.scientific_stability` | `generate_stability_visualization` | function | Generate heatmap of optimizer accuracy across starting points and step sizes. |
| `figures.sensitivity` | `generate_step_size_sensitivity_plot` | function | Generate step size sensitivity analysis with expanded range. |
| `invariants` | `InvariantResult` | class | Witness record for one numerical invariant. |
| `invariants` | `OptimizerSweepConfig` | class | Configurable knobs driving every optimization invariant. |
| `invariants` | `all_invariants` | function | Every invariant the dashboard / plaintext report should display. |
| `invariants` | `convergence_invariants` | function | For every step size α with ``α < 2/λ_max(A)``: gradient descent must converge to ``x* = A^{-1} b`` and the objective history must be monotone non-increasing. |
| `invariants` | `gradient_consistency_invariants` | function | Numerical-vs-analytical gradient agreement to floating tolerance. |
| `invariants` | `trajectory_invariants` | function | ``simulate_trajectory`` is monotone for every stable step size. |
| `manuscript_variables` | `generate_variables` | function | Generate all manuscript variables from config and analysis outputs. |
| `manuscript_variables` | `save_variables` | function | Persist *variables* as JSON for downstream rendering and debugging. |
| `optimizer` | `OptimizationResult` | class | Result container from :func:`gradient_descent`. |
| `optimizer` | `compute_gradient` | function | Compute ∇f(x) = A x - b for the quadratic objective. A defaults to identity, b to ones. |
| `optimizer` | `gradient_descent` | function | Run gradient descent: x_{k+1} = x_k - α ∇f(x_k) until convergence or max_iterations. |
| `optimizer` | `make_quadratic_problem` | function | Create paired (objective, gradient) callables for a quadratic problem. |
| `optimizer` | `quadratic_function` | function | Evaluate f(x) = (1/2) x^T A x - b^T x. A defaults to identity, b to ones. |
| `optimizer` | `quadratic_optimum` | function | Return (x*, f*) for f(x) = ½ xᵀ A x − bᵀ x. |
| `optimizer` | `simulate_trajectory` | function | Run gradient descent and return iteration/objective history. |
| `project_paths` | `project_output_dirs` | function | Return common output directories for the code exemplar. |
| `project_paths` | `project_root_context` | function | Temporarily route all exemplar output helpers to ``project_root``. |
| `project_paths` | `resolve_project_root` | function | Process resolve project root. |
| `sweeps` | `AlphaSweepConfig` | class | Knobs for :func:`run_alpha_sweep`. |
| `sweeps` | `AlphaSweepResult` | class | Numerical payload for an α sweep. |
| `sweeps` | `run_alpha_sweep` | function | Run gradient descent for each α and collect convergence diagnostics. |
| `sweeps` | `sensitivity_sweep` | function | α sweep for the step-size sensitivity figure (fixed stable α grid). |
| `sweeps` | `stability_error_matrix` | function | Build log₁₀|f(x) − f(x*)| matrix (rows=starting points, cols=step sizes). |
| `viz_config` | `agency_category` | function | Classify step size α into agency category for H=I quadratic. |
| `viz_config` | `apply_visualization_style` | function | Apply global matplotlib style for publication-quality, accessible figures. |
