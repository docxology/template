# API Symbols Glossary

This glossary is auto-generated from the public API in `src/`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `build_verifier` | `BuildVerificationReport` | class | Container for build verification results. |
| `build_verifier` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `build_verifier` | `create_build_validation_report` | function | Create a comprehensive build validation report. |
| `build_verifier` | `create_build_verification_script` | function | Create a comprehensive build verification script. |
| `build_verifier` | `create_comprehensive_build_report` | function | Create a comprehensive build report combining all verification results. |
| `build_verifier` | `create_integrity_manifest` | function | Create an integrity manifest for build verification. |
| `build_verifier` | `load_integrity_manifest` | function | Load integrity manifest from file. |
| `build_verifier` | `run_build_command` | function | Run a build command and capture output. |
| `build_verifier` | `save_integrity_manifest` | function | Save integrity manifest to file. |
| `build_verifier` | `validate_build_configuration` | function | Validate build configuration and settings. |
| `build_verifier` | `validate_build_process` | function | Validate that a build script is properly structured. |
| `build_verifier` | `verify_build_artifacts` | function | Verify that expected build artifacts are present and correct. |
| `build_verifier` | `verify_build_environment` | function | Verify that the build environment is properly configured. |
| `build_verifier` | `verify_build_integrity_against_baseline` | function | Verify build integrity against a baseline. |
| `build_verifier` | `verify_build_reproducibility` | function | Verify build reproducibility by running build multiple times. |
| `build_verifier` | `verify_dependency_consistency` | function | Verify consistency between dependency files. |
| `build_verifier` | `verify_integrity_against_manifest` | function | Verify integrity between two manifests. |
| `build_verifier` | `verify_output_directory_structure` | function | Verify that output directory has expected structure. |
| `example` | `add_numbers` | function | Add two numbers together. |
| `example` | `calculate_average` | function | Calculate the average of a list of numbers. |
| `example` | `find_maximum` | function | Find the maximum value in a list of numbers. |
| `example` | `find_minimum` | function | Find the minimum value in a list of numbers. |
| `example` | `is_even` | function | Check if a number is even. |
| `example` | `is_odd` | function | Check if a number is odd. |
| `example` | `multiply_numbers` | function | Multiply two numbers together. |
| `glossary_gen` | `ApiEntry` | class | Represents a public API entry from source code. |
| `glossary_gen` | `build_api_index` | function | Scan `src_dir` and collect public functions/classes with summaries. |
| `glossary_gen` | `generate_markdown_table` | function | Generate a Markdown table from API entries. |
| `glossary_gen` | `inject_between_markers` | function | Replace content between begin_marker and end_marker (inclusive markers preserved). |
| `integrity` | `IntegrityReport` | class | Container for integrity verification results. |
| `integrity` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `integrity` | `check_file_permissions` | function | Check file permissions and accessibility. |
| `integrity` | `create_integrity_manifest` | function | Create an integrity manifest for all output files. |
| `integrity` | `generate_integrity_report` | function | Generate a human-readable integrity report. |
| `integrity` | `load_integrity_manifest` | function | Load integrity manifest from file. |
| `integrity` | `save_integrity_manifest` | function | Save integrity manifest to file. |
| `integrity` | `validate_build_artifacts` | function | Validate that all expected build artifacts are present and correct. |
| `integrity` | `verify_academic_standards` | function | Verify compliance with academic writing standards. |
| `integrity` | `verify_cross_references` | function | Verify cross-reference integrity in markdown files. |
| `integrity` | `verify_data_consistency` | function | Verify data file consistency and integrity. |
| `integrity` | `verify_file_integrity` | function | Verify file integrity using hash comparison. |
| `integrity` | `verify_integrity_against_manifest` | function | Verify current integrity against a saved manifest. |
| `integrity` | `verify_output_completeness` | function | Verify that all expected outputs are present and complete. |
| `integrity` | `verify_output_integrity` | function | Perform comprehensive integrity verification of all outputs. |
| `pdf_validator` | `PDFValidationError` | class | Raised when PDF validation encounters an error. |
| `pdf_validator` | `extract_first_n_words` | function | Extract the first N words from text, preserving punctuation. |
| `pdf_validator` | `extract_text_from_pdf` | function | Extract all text content from a PDF file. |
| `pdf_validator` | `scan_for_issues` | function | Scan extracted text for common rendering issues. |
| `pdf_validator` | `validate_pdf_rendering` | function | Perform comprehensive validation of PDF rendering. |
| `publishing` | `CitationStyle` | class | Container for citation style configuration. |
| `publishing` | `PublicationMetadata` | class | Container for publication metadata. |
| `publishing` | `calculate_complexity_score` | function | Calculate a complexity score for the publication. |
| `publishing` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `publishing` | `create_academic_profile_data` | function | Create academic profile data for ORCID, ResearchGate, etc. |
| `publishing` | `create_publication_announcement` | function | Create a publication announcement for social media and blogs. |
| `publishing` | `create_publication_package` | function | Create a publication package with all necessary files. |
| `publishing` | `create_repository_metadata` | function | Create repository metadata for GitHub repository. |
| `publishing` | `create_submission_checklist` | function | Create a submission checklist for academic conferences/journals. |
| `publishing` | `extract_citations_from_markdown` | function | Extract all citations from markdown files. |
| `publishing` | `extract_publication_metadata` | function | Extract publication metadata from markdown files. |
| `publishing` | `format_authors_apa` | function | Format authors for APA style. |
| `publishing` | `format_authors_mla` | function | Format authors for MLA style. |
| `publishing` | `generate_citation_apa` | function | Generate APA citation format. |
| `publishing` | `generate_citation_bibtex` | function | Generate BibTeX citation format. |
| `publishing` | `generate_citation_mla` | function | Generate MLA citation format. |
| `publishing` | `generate_citations_markdown` | function | Generate markdown section with all citation formats. |
| `publishing` | `generate_doi_badge` | function | Generate DOI badge markdown. |
| `publishing` | `generate_publication_metrics` | function | Generate publication metrics for reporting. |
| `publishing` | `generate_publication_summary` | function | Generate a publication summary for repository README. |
| `publishing` | `validate_doi` | function | Validate DOI format and checksum. |
| `publishing` | `validate_publication_readiness` | function | Validate that the project is ready for publication. |
| `quality_checker` | `QualityMetrics` | class | Container for document quality metrics. |
| `quality_checker` | `analyze_academic_standards` | function | Analyze compliance with academic writing standards. |
| `quality_checker` | `analyze_document_metrics` | function | Analyze various document metrics for quality assessment. |
| `quality_checker` | `analyze_document_quality` | function | Perform comprehensive quality analysis of a research document. |
| `quality_checker` | `analyze_formatting_quality` | function | Analyze document formatting quality. |
| `quality_checker` | `analyze_readability` | function | Analyze text readability using multiple metrics. |
| `quality_checker` | `analyze_structural_integrity` | function | Analyze document structural integrity. |
| `quality_checker` | `calculate_overall_quality_score` | function | Calculate overall quality score from individual metrics. |
| `quality_checker` | `check_document_accessibility` | function | Check document accessibility features. |
| `quality_checker` | `count_syllables` | function | Count syllables in text using a simple heuristic. |
| `quality_checker` | `count_syllables_word` | function | Count syllables in a single word. |
| `quality_checker` | `extract_text_from_pdf_detailed` | function | Extract detailed text information from PDF for quality analysis. |
| `quality_checker` | `generate_quality_report` | function | Generate a human-readable quality report. |
| `quality_checker` | `validate_research_document_completeness` | function | Validate that a research document contains all expected sections. |
| `reproducibility` | `ReproducibilityReport` | class | Container for reproducibility analysis results. |
| `reproducibility` | `calculate_directory_hash` | function | Calculate hash of all files in a directory. |
| `reproducibility` | `calculate_file_hash` | function | Calculate hash of a file for integrity verification. |
| `reproducibility` | `capture_dependency_state` | function | Capture dependency information for reproducibility. |
| `reproducibility` | `capture_environment_state` | function | Capture the current environment state for reproducibility. |
| `reproducibility` | `compare_snapshots` | function | Compare two version snapshots for changes. |
| `reproducibility` | `create_reproducible_environment` | function | Create environment configuration for reproducible builds. |
| `reproducibility` | `create_reproducible_script_template` | function | Create a template for reproducible research scripts. |
| `reproducibility` | `create_version_snapshot` | function | Create a version snapshot of the current build for future comparison. |
| `reproducibility` | `generate_build_manifest` | function | Generate a comprehensive build manifest for reproducibility. |
| `reproducibility` | `generate_reproducibility_report` | function | Generate comprehensive reproducibility report. |
| `reproducibility` | `load_reproducibility_report` | function | Load reproducibility report from file. |
| `reproducibility` | `save_build_manifest` | function | Save build manifest to file. |
| `reproducibility` | `save_reproducibility_report` | function | Save reproducibility report to file. |
| `reproducibility` | `validate_experiment_reproducibility` | function | Validate that experiment results are reproducible within tolerance. |
| `reproducibility` | `verify_build_integrity` | function | Verify build integrity against a saved manifest. |
| `reproducibility` | `verify_reproducibility` | function | Verify reproducibility by comparing current and previous reports. |
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
