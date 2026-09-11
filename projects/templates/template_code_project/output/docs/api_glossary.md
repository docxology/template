| Module | Name | Kind | Summary |
|---|---|---|---|
| `template_code_project.analysis` | `AlgorithmComparison` | class | Ranked cross-algorithm comparison for gradient-descent variants. |
| `template_code_project.analysis` | `AlgorithmVariant` | class | Descriptor for one gradient-descent configuration under comparison. |
| `template_code_project.analysis` | `MultiFactorReport` | class | Multi-factor analysis combining convergence, stability, and performance. |
| `template_code_project.analysis` | `compare_algorithms` | function | Compare gradient-descent variants across all configured step sizes. |
| `template_code_project.analysis` | `multi_factor_analysis` | function | Combine convergence, stability, and performance into a composite score. |
| `template_code_project.analysis.experiments` | `run_convergence_experiment` | function | Run gradient descent with different step sizes and track convergence. |
| `template_code_project.analysis.experiments` | `save_optimization_results` | function | Save optimization results to CSV file. |
| `template_code_project.analysis.publishing` | `extract_optimization_metadata` | function | Extract publication metadata from optimization results. |
| `template_code_project.analysis.publishing` | `generate_citations_from_metadata` | function | Generate citations from optimization metadata. |
| `template_code_project.analysis.publishing` | `save_publishing_materials` | function | Save publishing materials to output directory. |
| `template_code_project.analysis.scientific_reports` | `register_figure` | function | Register generated figures for manuscript reference. |
| `template_code_project.analysis.scientific_reports` | `run_performance_benchmarking` | function | Run timing diagnostics and write a deterministic benchmark contract. |
| `template_code_project.analysis.scientific_reports` | `run_stability_analysis` | function | Assess numerical stability of optimization algorithms. |
| `template_code_project.analysis.scientific_reports` | `save_validation_report` | function | Save validation report to file. |
| `template_code_project.analysis.scientific_reports` | `validate_generated_outputs` | function | Validate integrity of generated analysis outputs. |
| `template_code_project.analysis.workflow` | `main` | function | Run the full optimization analysis pipeline. |
| `template_code_project.analysis.workflow` | `run_analysis_pipeline` | function | Execute the full optimization analysis workflow. |
| `template_code_project.core.benchmark_support` | `BenchmarkRun` | class | Full benchmark run: measurements plus infra-scored rubric result. |
| `template_code_project.core.benchmark_support` | `TimingMeasurement` | class | One benchmark measurement; timing is a runtime-only diagnostic. |
| `template_code_project.core.benchmark_support` | `benchmark_payload` | function | Convert a run into a byte-stable, JSON-safe canonical payload. |
| `template_code_project.core.benchmark_support` | `run_quadratic_benchmark` | function | Evaluate the pure quadratic objective and score deterministic facts. |
| `template_code_project.core.benchmark_support` | `write_benchmark_report` | function | Write the benchmark payload as JSON and return the path. |
| `template_code_project.core.documentation` | `build_api_reference_markdown` | function | Return markdown API reference for the optimization exemplar. |
| `template_code_project.core.experiment_config` | `ExperimentConfig` | class | Frozen experiment parameters from ``config.yaml`` → ``experiment:``. |
| `template_code_project.core.experiment_config` | `load_experiment_config` | function | Load experiment parameters from ``manuscript/config.yaml``. |
| `template_code_project.core.invariants` | `InvariantResult` | class | Witness record for one numerical invariant. |
| `template_code_project.core.invariants` | `OptimizerSweepConfig` | class | Configurable knobs driving every optimization invariant. |
| `template_code_project.core.invariants` | `all_invariants` | function | Every invariant the dashboard / plaintext report should display. |
| `template_code_project.core.invariants` | `convergence_invariants` | function | For every step size α with ``α < 2/λ_max(A)``: gradient descent must converge to ``x* = A^{-1} b`` and the objective history must be monotone non-increasing. |
| `template_code_project.core.invariants` | `gradient_consistency_invariants` | function | Numerical-vs-analytical gradient agreement to floating tolerance. |
| `template_code_project.core.invariants` | `trajectory_invariants` | function | ``simulate_trajectory`` is monotone for every stable step size. |
| `template_code_project.core.manuscript_variables` | `generate_variables` | function | Generate all manuscript variables from config and analysis outputs. |
| `template_code_project.core.manuscript_variables` | `save_variables` | function | Persist *variables* as JSON for downstream rendering and debugging. |
| `template_code_project.core.optimizer` | `OptimizationResult` | class | Result container from :func:`gradient_descent`. |
| `template_code_project.core.optimizer` | `compute_gradient` | function | Compute ∇f(x) = A x - b for the quadratic objective. A defaults to identity, b to ones. |
| `template_code_project.core.optimizer` | `gradient_descent` | function | Run gradient descent: x_{k+1} = x_k - α ∇f(x_k) until convergence or max_iterations. |
| `template_code_project.core.optimizer` | `make_quadratic_problem` | function | Create paired (objective, gradient) callables for a quadratic problem. |
| `template_code_project.core.optimizer` | `quadratic_function` | function | Evaluate f(x) = (1/2) x^T A x - b^T x. A defaults to identity, b to ones. |
| `template_code_project.core.optimizer` | `quadratic_optimum` | function | Return (x*, f*) for f(x) = ½ xᵀ A x − bᵀ x. |
| `template_code_project.core.optimizer` | `simulate_trajectory` | function | Run gradient descent and return iteration/objective history. |
| `template_code_project.core.project_paths` | `project_output_dirs` | function | Return common output directories for the code exemplar. |
| `template_code_project.core.project_paths` | `project_root_context` | function | Temporarily route all exemplar output helpers to ``project_root``. |
| `template_code_project.core.project_paths` | `resolve_project_root` | function | Process resolve project root. |
| `template_code_project.core.sweeps` | `AlphaSweepConfig` | class | Knobs for :func:`run_alpha_sweep`. |
| `template_code_project.core.sweeps` | `AlphaSweepResult` | class | Numerical payload for an α sweep. |
| `template_code_project.core.sweeps` | `run_alpha_sweep` | function | Run gradient descent for each α and collect convergence diagnostics. |
| `template_code_project.core.sweeps` | `sensitivity_sweep` | function | α sweep for the step-size sensitivity figure (fixed stable α grid). |
| `template_code_project.core.sweeps` | `stability_error_matrix` | function | Build log₁₀|f(x) − f(x*)| matrix (rows=starting points, cols=step sizes). |
| `template_code_project.dashboard.dashboard` | `build_dashboard_html` | function | Build the dashboard with config defaults and write HTML to ``output/web/``. |
| `template_code_project.dashboard.dashboard` | `cli_main` | function | Build dashboard artifacts from CLI arguments. |
| `template_code_project.dashboard.dashboard` | `parse_dashboard_args` | function | Parse CLI arguments for the dashboard builder. |
| `template_code_project.dashboard.dashboard_panels` | `build_dashboard` | function | Build dashboard. |
| `template_code_project.dashboard.dashboard_panels` | `to_dashboard_invariant` | function | Convert this object to dashboard invariant. |
| `template_code_project.dashboard.dashboard_payload` | `DashboardPayloadError` | class | Raised when a dashboard payload is structurally incomplete. |
| `template_code_project.dashboard.dashboard_payload` | `compute_payload` | function | Process compute payload. |
| `template_code_project.dashboard.dashboard_payload` | `load_yaml_defaults` | function | Load experiment defaults from ``manuscript/config.yaml``. |
| `template_code_project.dashboard.dashboard_payload` | `to_diagonal_A` | function | Convert this object to diagonal A. |
| `template_code_project.dashboard.dashboard_payload` | `validate_dashboard_payload` | function | Return schema findings for a dashboard payload. |
| `template_code_project.figures.convergence` | `generate_convergence_plot` | function | Generate convergence plot showing objective value vs iteration. |
| `template_code_project.figures.convergence` | `generate_convergence_rate_plot` | function | Generate convergence rate comparison plot. |
| `template_code_project.figures.scientific_complexity` | `BackendProfile` | class | Descriptor for a gradient-descent backend variant. |
| `template_code_project.figures.scientific_complexity` | `compare_profiles_at_alpha` | function | Compare all backend profiles at a single step size. |
| `template_code_project.figures.scientific_complexity` | `compute_complexity_profile` | function | Build per-step-size complexity metrics for one backend profile. |
| `template_code_project.figures.scientific_complexity` | `compute_contraction_factor` | function | Compute the per-step contraction factor ρ = |1 − α · L|. |
| `template_code_project.figures.scientific_complexity` | `compute_theoretical_complexity` | function | Estimate iteration count to reduce error by 1/e from the linear rate bound. |
| `template_code_project.figures.scientific_complexity` | `generate_complexity_visualization` | function | Generate algorithm performance analysis with six informative panels. |
| `template_code_project.figures.scientific_complexity` | `optimal_step_size` | function | Return the theoretically optimal step size ``α* = 1/L``. |
| `template_code_project.figures.scientific_complexity` | `profile_stable_region` | function | Return ``(alpha_min, alpha_max)`` of the strictly stable step-size interval. |
| `template_code_project.figures.scientific_stability` | `generate_benchmark_visualization` | function | Generate a deterministic dimensional-work benchmark figure. |
| `template_code_project.figures.scientific_stability` | `generate_stability_visualization` | function | Generate heatmap of optimizer accuracy across starting points and step sizes. |
| `template_code_project.figures.sensitivity` | `generate_step_size_sensitivity_plot` | function | Generate step size sensitivity analysis with expanded range. |
| `template_code_project.figures.viz_config` | `agency_category` | function | Classify step size α into agency category for H=I quadratic. |
| `template_code_project.figures.viz_config` | `apply_visualization_style` | function | Apply global matplotlib style for publication-quality, accessible figures. |
