# API Symbols Glossary {#sec:glossary}

This glossary is auto-generated from the public API in `src/` by `repo_utilities/generate_glossary.py`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `infrastructure.build_verifier` | `BuildVerificationReport` | class | Container for build verification results. |
| `infrastructure.build_verifier` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `infrastructure.build_verifier` | `create_build_validation_report` | function | Create a comprehensive build validation report. |
| `infrastructure.build_verifier` | `create_build_verification_script` | function | Create a comprehensive build verification script. |
| `infrastructure.build_verifier` | `create_comprehensive_build_report` | function | Create a comprehensive build report combining all verification results. |
| `infrastructure.build_verifier` | `create_integrity_manifest` | function | Create an integrity manifest for build verification. |
| `infrastructure.build_verifier` | `load_integrity_manifest` | function | Load integrity manifest from file. |
| `infrastructure.build_verifier` | `run_build_command` | function | Run a build command and capture output. |
| `infrastructure.build_verifier` | `save_integrity_manifest` | function | Save integrity manifest to file. |
| `infrastructure.build_verifier` | `validate_build_configuration` | function | Validate build configuration and settings. |
| `infrastructure.build_verifier` | `validate_build_process` | function | Validate that a build script is properly structured. |
| `infrastructure.build_verifier` | `verify_build_artifacts` | function | Verify that expected build artifacts are present and correct. |
| `infrastructure.build_verifier` | `verify_build_environment` | function | Verify that the build environment is properly configured. |
| `infrastructure.build_verifier` | `verify_build_integrity_against_baseline` | function | Verify build integrity against a baseline. |
| `infrastructure.build_verifier` | `verify_build_reproducibility` | function | Verify build reproducibility by running build multiple times. |
| `infrastructure.build_verifier` | `verify_dependency_consistency` | function | Verify consistency between dependency files. |
| `infrastructure.build_verifier` | `verify_integrity_against_manifest` | function | Verify integrity between two manifests. |
| `infrastructure.build_verifier` | `verify_output_directory_structure` | function | Verify that output directory has expected structure. |
| `infrastructure.figure_manager` | `FigureManager` | class | Manages figures with automatic numbering and cross-referencing. |
| `infrastructure.figure_manager` | `FigureMetadata` | class | Metadata for a figure. |
| `infrastructure.glossary_gen` | `ApiEntry` | class | Represents a public API entry from source code. |
| `infrastructure.glossary_gen` | `build_api_index` | function | Scan `src_dir` and collect public functions/classes with summaries. |
| `infrastructure.glossary_gen` | `generate_markdown_table` | function | Generate a Markdown table from API entries. |
| `infrastructure.glossary_gen` | `inject_between_markers` | function | Replace content between begin_marker and end_marker (inclusive markers preserved). |
| `infrastructure.image_manager` | `ImageManager` | class | Manages image insertion and cross-referencing in markdown files. |
| `infrastructure.integrity` | `IntegrityReport` | class | Container for integrity verification results. |
| `infrastructure.integrity` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `infrastructure.integrity` | `check_file_permissions` | function | Check file permissions and accessibility. |
| `infrastructure.integrity` | `create_integrity_manifest` | function | Create an integrity manifest for all output files. |
| `infrastructure.integrity` | `generate_integrity_report` | function | Generate a human-readable integrity report. |
| `infrastructure.integrity` | `load_integrity_manifest` | function | Load integrity manifest from file. |
| `infrastructure.integrity` | `save_integrity_manifest` | function | Save integrity manifest to file. |
| `infrastructure.integrity` | `validate_build_artifacts` | function | Validate that all expected build artifacts are present and correct. |
| `infrastructure.integrity` | `verify_academic_standards` | function | Verify compliance with academic writing standards. |
| `infrastructure.integrity` | `verify_cross_references` | function | Verify cross-reference integrity in markdown files. |
| `infrastructure.integrity` | `verify_data_consistency` | function | Verify data file consistency and integrity. |
| `infrastructure.integrity` | `verify_file_integrity` | function | Verify file integrity using hash comparison. |
| `infrastructure.integrity` | `verify_integrity_against_manifest` | function | Verify current integrity against a saved manifest. |
| `infrastructure.integrity` | `verify_output_completeness` | function | Verify that all expected outputs are present and complete. |
| `infrastructure.integrity` | `verify_output_integrity` | function | Perform comprehensive integrity verification of all outputs. |
| `infrastructure.markdown_integration` | `MarkdownIntegration` | class | Integrates figures and references into markdown files. |
| `infrastructure.pdf_validator` | `PDFValidationError` | class | Raised when PDF validation encounters an error. |
| `infrastructure.pdf_validator` | `decode_pdf_hex_strings` | function | Decode PDF hex-encoded strings (e.g., /x45/x78 -> Ex) to readable text. |
| `infrastructure.pdf_validator` | `extract_first_n_words` | function | Extract the first N words from text, preserving punctuation. |
| `infrastructure.pdf_validator` | `extract_text_from_pdf` | function | Extract all text content from a PDF file. |
| `infrastructure.pdf_validator` | `scan_for_issues` | function | Scan extracted text for common rendering issues. |
| `infrastructure.pdf_validator` | `validate_pdf_rendering` | function | Perform comprehensive validation of PDF rendering. |
| `infrastructure.publishing` | `CitationStyle` | class | Container for citation style configuration. |
| `infrastructure.publishing` | `PublicationMetadata` | class | Container for publication metadata. |
| `infrastructure.publishing` | `calculate_complexity_score` | function | Calculate a complexity score for the publication. |
| `infrastructure.publishing` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `infrastructure.publishing` | `create_academic_profile_data` | function | Create academic profile data for ORCID, ResearchGate, etc. |
| `infrastructure.publishing` | `create_publication_announcement` | function | Create a publication announcement for social media and blogs. |
| `infrastructure.publishing` | `create_publication_package` | function | Create a publication package with all necessary files. |
| `infrastructure.publishing` | `create_repository_metadata` | function | Create repository metadata for GitHub repository. |
| `infrastructure.publishing` | `create_submission_checklist` | function | Create a submission checklist for academic conferences/journals. |
| `infrastructure.publishing` | `extract_citations_from_markdown` | function | Extract all citations from markdown files. |
| `infrastructure.publishing` | `extract_publication_metadata` | function | Extract publication metadata from markdown files. |
| `infrastructure.publishing` | `format_authors_apa` | function | Format authors for APA style. |
| `infrastructure.publishing` | `format_authors_mla` | function | Format authors for MLA style. |
| `infrastructure.publishing` | `generate_citation_apa` | function | Generate APA citation format. |
| `infrastructure.publishing` | `generate_citation_bibtex` | function | Generate BibTeX citation format. |
| `infrastructure.publishing` | `generate_citation_mla` | function | Generate MLA citation format. |
| `infrastructure.publishing` | `generate_citations_markdown` | function | Generate markdown section with all citation formats. |
| `infrastructure.publishing` | `generate_doi_badge` | function | Generate DOI badge markdown. |
| `infrastructure.publishing` | `generate_publication_metrics` | function | Generate publication metrics for reporting. |
| `infrastructure.publishing` | `generate_publication_summary` | function | Generate a publication summary for repository README. |
| `infrastructure.publishing` | `validate_doi` | function | Validate DOI format and checksum. |
| `infrastructure.publishing` | `validate_publication_readiness` | function | Validate that the project is ready for publication. |
| `infrastructure.quality_checker` | `QualityMetrics` | class | Container for document quality metrics. |
| `infrastructure.quality_checker` | `analyze_academic_standards` | function | Analyze compliance with academic writing standards. |
| `infrastructure.quality_checker` | `analyze_document_metrics` | function | Analyze various document metrics for quality assessment. |
| `infrastructure.quality_checker` | `analyze_document_quality` | function | Perform comprehensive quality analysis of a research document. |
| `infrastructure.quality_checker` | `analyze_formatting_quality` | function | Analyze document formatting quality. |
| `infrastructure.quality_checker` | `analyze_readability` | function | Analyze text readability using multiple metrics. |
| `infrastructure.quality_checker` | `analyze_structural_integrity` | function | Analyze document structural integrity. |
| `infrastructure.quality_checker` | `calculate_overall_quality_score` | function | Calculate overall quality score from individual metrics. |
| `infrastructure.quality_checker` | `check_document_accessibility` | function | Check document accessibility features. |
| `infrastructure.quality_checker` | `count_syllables` | function | Count syllables in text using a simple heuristic. |
| `infrastructure.quality_checker` | `count_syllables_word` | function | Count syllables in a single word. |
| `infrastructure.quality_checker` | `extract_text_from_pdf_detailed` | function | Extract detailed text information from PDF for quality analysis. |
| `infrastructure.quality_checker` | `generate_quality_report` | function | Generate a human-readable quality report. |
| `infrastructure.quality_checker` | `validate_research_document_completeness` | function | Validate that a research document contains all expected sections. |
| `infrastructure.reproducibility` | `ReproducibilityReport` | class | Container for reproducibility analysis results. |
| `infrastructure.reproducibility` | `calculate_directory_hash` | function | Calculate hash of all files in a directory. |
| `infrastructure.reproducibility` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `infrastructure.reproducibility` | `capture_dependency_state` | function | Capture dependency information for reproducibility. |
| `infrastructure.reproducibility` | `capture_environment_state` | function | Capture the current environment state for reproducibility. |
| `infrastructure.reproducibility` | `compare_snapshots` | function | Compare two version snapshots for changes. |
| `infrastructure.reproducibility` | `create_reproducible_environment` | function | Create environment configuration for reproducible builds. |
| `infrastructure.reproducibility` | `create_reproducible_script_template` | function | Create a template for reproducible research scripts. |
| `infrastructure.reproducibility` | `create_version_snapshot` | function | Create a version snapshot of the current build for future comparison. |
| `infrastructure.reproducibility` | `generate_build_manifest` | function | Generate a comprehensive build manifest for reproducibility. |
| `infrastructure.reproducibility` | `generate_reproducibility_report` | function | Generate comprehensive reproducibility report. |
| `infrastructure.reproducibility` | `load_reproducibility_report` | function | Load reproducibility report from file. |
| `infrastructure.reproducibility` | `save_build_manifest` | function | Save build manifest to file. |
| `infrastructure.reproducibility` | `save_reproducibility_report` | function | Save reproducibility report to file. |
| `infrastructure.reproducibility` | `validate_experiment_reproducibility` | function | Validate that experiment results are reproducible within tolerance. |
| `infrastructure.reproducibility` | `verify_build_integrity` | function | Verify build integrity against a saved manifest. |
| `infrastructure.reproducibility` | `verify_reproducibility` | function | Verify reproducibility by comparing current and previous reports. |
| `scientific.data_generator` | `generate_classification_dataset` | function | Generate classification dataset. |
| `scientific.data_generator` | `generate_correlated_data` | function | Generate correlated multivariate data. |
| `scientific.data_generator` | `generate_synthetic_data` | function | Generate synthetic data with specified distribution. |
| `scientific.data_generator` | `generate_time_series` | function | Generate time series data. |
| `scientific.data_generator` | `inject_noise` | function | Inject noise into data. |
| `scientific.data_generator` | `validate_data` | function | Validate data quality. |
| `scientific.data_processing` | `clean_data` | function | Clean data by removing or filling invalid values. |
| `scientific.data_processing` | `create_validation_pipeline` | function | Create a data validation pipeline. |
| `scientific.data_processing` | `detect_outliers` | function | Detect outliers in data. |
| `scientific.data_processing` | `extract_features` | function | Extract features from data. |
| `scientific.data_processing` | `normalize_data` | function | Normalize data using specified method. |
| `scientific.data_processing` | `remove_outliers` | function | Remove outliers from data. |
| `scientific.data_processing` | `standardize_data` | function | Standardize data to zero mean and unit variance. |
| `scientific.data_processing` | `transform_data` | function | Apply transformation to data. |
| `scientific.example` | `add_numbers` | function | Add two numbers together. |
| `scientific.example` | `calculate_average` | function | Calculate the average of a list of numbers. |
| `scientific.example` | `find_maximum` | function | Find the maximum value in a list of numbers. |
| `scientific.example` | `find_minimum` | function | Find the minimum value in a list of numbers. |
| `scientific.example` | `is_even` | function | Check if a number is even. |
| `scientific.example` | `is_odd` | function | Check if a number is odd. |
| `scientific.example` | `multiply_numbers` | function | Multiply two numbers together. |
| `scientific.metrics` | `CustomMetric` | class | Framework for custom metrics. |
| `scientific.metrics` | `calculate_accuracy` | function | Calculate accuracy for classification. |
| `scientific.metrics` | `calculate_all_metrics` | function | Calculate all applicable metrics. |
| `scientific.metrics` | `calculate_convergence_metrics` | function | Calculate convergence metrics. |
| `scientific.metrics` | `calculate_effect_size` | function | Calculate effect size (Cohen's d). |
| `scientific.metrics` | `calculate_p_value_approximation` | function | Approximate p-value from test statistic. |
| `scientific.metrics` | `calculate_precision_recall_f1` | function | Calculate precision, recall, and F1 score. |
| `scientific.metrics` | `calculate_psnr` | function | Calculate Peak Signal-to-Noise Ratio (PSNR). |
| `scientific.metrics` | `calculate_snr` | function | Calculate Signal-to-Noise Ratio (SNR). |
| `scientific.metrics` | `calculate_ssim` | function | Calculate Structural Similarity Index (SSIM). |
| `scientific.parameters` | `ParameterConstraint` | class | Constraint for parameter validation. |
| `scientific.parameters` | `ParameterSet` | class | A set of parameters with validation. |
| `scientific.parameters` | `ParameterSweep` | class | Configuration for parameter sweeps. |
| `scientific.performance` | `ConvergenceMetrics` | class | Metrics for convergence analysis. |
| `scientific.performance` | `ScalabilityMetrics` | class | Metrics for scalability analysis. |
| `scientific.performance` | `analyze_convergence` | function | Analyze convergence of a sequence. |
| `scientific.performance` | `analyze_scalability` | function | Analyze scalability of an algorithm. |
| `scientific.performance` | `benchmark_comparison` | function | Compare multiple methods on benchmarks. |
| `scientific.performance` | `calculate_efficiency` | function | Calculate efficiency (speedup / resource_ratio). |
| `scientific.performance` | `calculate_speedup` | function | Calculate speedup relative to baseline. |
| `scientific.performance` | `check_statistical_significance` | function | Test statistical significance between two groups. |
| `scientific.plots` | `plot_3d_surface` | function | Create a 3D surface plot. |
| `scientific.plots` | `plot_bar` | function | Create a bar chart. |
| `scientific.plots` | `plot_comparison` | function | Plot comparison of methods. |
| `scientific.plots` | `plot_contour` | function | Create a contour plot. |
| `scientific.plots` | `plot_convergence` | function | Plot convergence curve. |
| `scientific.plots` | `plot_heatmap` | function | Create a heatmap. |
| `scientific.plots` | `plot_line` | function | Create a line plot. |
| `scientific.plots` | `plot_scatter` | function | Create a scatter plot. |
| `scientific.reporting` | `ReportGenerator` | class | Generate reports from simulation and analysis results. |
| `scientific.simulation` | `SimpleSimulation` | class | Simple example simulation for testing. |
| `scientific.simulation` | `SimulationBase` | class | Base class for scientific simulations. |
| `scientific.simulation` | `SimulationState` | class | Represents the state of a simulation run. |
| `scientific.statistics` | `DescriptiveStats` | class | Descriptive statistics for a dataset. |
| `scientific.statistics` | `anova_test` | function | Perform one-way ANOVA test. |
| `scientific.statistics` | `calculate_confidence_interval` | function | Calculate confidence interval for mean. |
| `scientific.statistics` | `calculate_correlation` | function | Calculate correlation between two variables. |
| `scientific.statistics` | `calculate_descriptive_stats` | function | Calculate descriptive statistics. |
| `scientific.statistics` | `fit_distribution` | function | Fit a distribution to data. |
| `scientific.statistics` | `t_test` | function | Perform t-test. |
| `scientific.validation` | `ValidationFramework` | class | Framework for validating simulation and analysis results. |
| `scientific.validation` | `ValidationResult` | class | Result of a validation check. |
| `scientific.visualization` | `VisualizationEngine` | class | Engine for generating publication-quality figures. |
| `scientific.visualization` | `create_multi_panel_figure` | function | Create a multi-panel figure. |
| `scientific_dev` | `BenchmarkResult` | class | Container for benchmark results. |
| `scientific_dev` | `StabilityTest` | class | Container for numerical stability test results. |
| `scientific_dev` | `benchmark_function` | function | Benchmark function performance across multiple inputs. |
| `scientific_dev` | `check_numerical_stability` | function | Check numerical stability of a function across a range of inputs. |
| `scientific_dev` | `check_research_compliance` | function | Check function compliance with research software standards. |
| `scientific_dev` | `create_scientific_module_template` | function | Create a template for a new scientific module. |
| `scientific_dev` | `create_scientific_test_suite` | function | Create a comprehensive test suite for a scientific module. |
| `scientific_dev` | `create_scientific_workflow_template` | function | Create a template for scientific research workflows. |
| `scientific_dev` | `generate_api_documentation` | function | Generate comprehensive API documentation for a scientific module. |
| `scientific_dev` | `generate_performance_report` | function | Generate a performance analysis report. |
| `scientific_dev` | `generate_scientific_documentation` | function | Generate scientific documentation for a function. |
| `scientific_dev` | `validate_scientific_best_practices` | function | Validate that a module follows scientific computing best practices. |
| `scientific_dev` | `validate_scientific_implementation` | function | Validate scientific implementation against known test cases. |
<!-- END: AUTO-API-GLOSSARY -->
