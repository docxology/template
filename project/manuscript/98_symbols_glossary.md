# API Symbols Glossary {#sec:glossary}

This glossary is auto-generated from the public API in `src/` modules.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `data_generator` | `generate_classification_dataset` | function | Generate classification dataset. |
| `data_generator` | `generate_correlated_data` | function | Generate correlated multivariate data. |
| `data_generator` | `generate_synthetic_data` | function | Generate synthetic data with specified distribution. |
| `data_generator` | `generate_time_series` | function | Generate time series data. |
| `data_generator` | `inject_noise` | function | Inject noise into data. |
| `data_generator` | `validate_data` | function | Validate data quality. |
| `data_processing` | `clean_data` | function | Clean data by removing or filling invalid values. |
| `data_processing` | `create_validation_pipeline` | function | Create a data validation pipeline. |
| `data_processing` | `detect_outliers` | function | Detect outliers in data. |
| `data_processing` | `extract_features` | function | Extract features from data. |
| `data_processing` | `normalize_data` | function | Normalize data using specified method. |
| `data_processing` | `remove_outliers` | function | Remove outliers from data. |
| `data_processing` | `standardize_data` | function | Standardize data to zero mean and unit variance. |
| `data_processing` | `transform_data` | function | Apply transformation to data. |
| `example` | `add_numbers` | function | Add two numbers together. |
| `example` | `calculate_average` | function | Calculate the average of a list of numbers. |
| `example` | `find_maximum` | function | Find the maximum value in a list of numbers. |
| `example` | `find_minimum` | function | Find the minimum value in a list of numbers. |
| `example` | `is_even` | function | Check if a number is even. |
| `example` | `is_odd` | function | Check if a number is odd. |
| `example` | `multiply_numbers` | function | Multiply two numbers together. |
| `metrics` | `CustomMetric` | class | Framework for custom metrics. |
| `metrics` | `calculate_accuracy` | function | Calculate accuracy for classification. |
| `metrics` | `calculate_all_metrics` | function | Calculate all applicable metrics. |
| `metrics` | `calculate_convergence_metrics` | function | Calculate convergence metrics. |
| `metrics` | `calculate_effect_size` | function | Calculate effect size (Cohen's d). |
| `metrics` | `calculate_p_value_approximation` | function | Approximate p-value from test statistic. |
| `metrics` | `calculate_precision_recall_f1` | function | Calculate precision, recall, and F1 score. |
| `metrics` | `calculate_psnr` | function | Calculate Peak Signal-to-Noise Ratio (PSNR). |
| `metrics` | `calculate_snr` | function | Calculate Signal-to-Noise Ratio (SNR). |
| `metrics` | `calculate_ssim` | function | Calculate Structural Similarity Index (SSIM). |
| `parameters` | `ParameterConstraint` | class | Constraint for parameter validation. |
| `parameters` | `ParameterSet` | class | A set of parameters with validation. |
| `parameters` | `ParameterSweep` | class | Configuration for parameter sweeps. |
| `performance` | `ConvergenceMetrics` | class | Metrics for convergence analysis. |
| `performance` | `ScalabilityMetrics` | class | Metrics for scalability analysis. |
| `performance` | `analyze_convergence` | function | Analyze convergence of a sequence. |
| `performance` | `analyze_scalability` | function | Analyze scalability of an algorithm. |
| `performance` | `benchmark_comparison` | function | Compare multiple methods on benchmarks. |
| `performance` | `calculate_efficiency` | function | Calculate efficiency (speedup / resource_ratio). |
| `performance` | `calculate_speedup` | function | Calculate speedup relative to baseline. |
| `performance` | `check_statistical_significance` | function | Test statistical significance between two groups. |
| `plots` | `plot_3d_surface` | function | Create a 3D surface plot. |
| `plots` | `plot_bar` | function | Create a bar chart. |
| `plots` | `plot_comparison` | function | Plot comparison of methods. |
| `plots` | `plot_contour` | function | Create a contour plot. |
| `plots` | `plot_convergence` | function | Plot convergence curve. |
| `plots` | `plot_heatmap` | function | Create a heatmap. |
| `plots` | `plot_line` | function | Create a line plot. |
| `plots` | `plot_scatter` | function | Create a scatter plot. |
| `reporting` | `ReportGenerator` | class | Generate reports from simulation and analysis results. |
| `simulation` | `SimpleSimulation` | class | Simple example simulation for testing. |
| `simulation` | `SimulationBase` | class | Base class for scientific simulations. |
| `simulation` | `SimulationState` | class | Represents the state of a simulation run. |
| `statistics` | `DescriptiveStats` | class | Descriptive statistics for a dataset. |
| `statistics` | `anova_test` | function | Perform one-way ANOVA test. |
| `statistics` | `calculate_confidence_interval` | function | Calculate confidence interval for mean. |
| `statistics` | `calculate_correlation` | function | Calculate correlation between two variables. |
| `statistics` | `calculate_descriptive_stats` | function | Calculate descriptive statistics. |
| `statistics` | `fit_distribution` | function | Fit a distribution to data. |
| `statistics` | `t_test` | function | Perform t-test. |
| `validation` | `ValidationFramework` | class | Framework for validating simulation and analysis results. |
| `validation` | `ValidationResult` | class | Result of a validation check. |
| `visualization` | `VisualizationEngine` | class | Engine for generating publication-quality figures. |
| `visualization` | `create_multi_panel_figure` | function | Create a multi-panel figure. |

### Ways-Specific Analysis Modules

| Module | Name | Kind | Summary |
|---|---|---|---|
| `database` | `WaysDatabase` | class | SQLAlchemy ORM for ways, rooms, questions database access. |
| `database` | `Way` | class | Data model for individual ways with metadata. |
| `database` | `Room` | class | Data model for House of Knowledge rooms. |
| `database` | `Question` | class | Data model for philosophical questions. |
| `sql_queries` | `WaysSQLQueries` | class | Pre-built SQL queries for ways analysis operations. |
| `ways_analysis` | `WaysAnalyzer` | class | Comprehensive ways characterization and statistical analysis. |
| `ways_analysis` | `WaysCharacterization` | class | Data class for ways analysis results. |
| `network_analysis` | `WaysNetworkAnalyzer` | class | Graph-based network analysis of way relationships. |
| `network_analysis` | `WaysNetwork` | class | Network representation of ways and their connections. |
| `house_of_knowledge` | `HouseOfKnowledgeAnalyzer` | class | Analysis of the 24-room House of Knowledge framework. |
| `house_of_knowledge` | `HouseStructure` | class | Complete structure of the House of Knowledge. |
| `statistics` | `analyze_way_distributions` | function | Statistical analysis of way distributions across categories. |
| `statistics` | `compute_way_correlations` | function | Correlation analysis between way characteristics. |
| `statistics` | `compute_way_diversity_metrics` | function | Diversity metrics for ways across dimensions. |
| `metrics` | `compute_way_coverage_metrics` | function | Coverage analysis of ways in framework. |
| `metrics` | `compute_way_interconnectedness` | function | Interconnectedness metrics for ways network. |
<!-- END: AUTO-API-GLOSSARY -->
