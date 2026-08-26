# EXECUTABLE-BUNDLE-MAJ-1/-2 offline-container verification receipt
as-of: 2026-08-26T20:02:59Z (host clock PDT)
image: template-bundle-vendored:2026-08-26 (id 58c35a2d1675), built from output/templates/template_code_project/executable_bundle regenerated 2026-08-26 with vendored infrastructure/ (commit 277f75f88 contract)

## Network: none
1.07s call     source/tests/test_invariants_and_dashboard.py::TestBuildDashboardCLI::test_rejects_non_positive_step_size
1.01s call     source/tests/test_analysis_coverage.py::TestMainErrors::test_main_reraises_file_not_found_error
1.01s call     source/tests/test_analysis_coverage.py::TestMainErrors::test_main_reraises_import_error
1.01s call     source/tests/test_analysis_coverage.py::TestMainErrors::test_main_reraises_template_error
242 passed, 4 deselected, 17 warnings in 19.40s <!-- noqa: drift-counts --> (dated historical receipt; live counts: docs/_generated/COUNTS.md)
PYTEST_EXIT=0
RUN1_EXIT=0

## Compose full-pipeline service (render): fail-closed receipt
EXECUTABLE-BUNDLE UNAVAILABLE-DEPENDENCY RECEIPT: this bundle payload is single-project; full-pipeline reproduction requires the template repository root (scripts/, run.sh, tests/regression/). Failing closed instead of raising ModuleNotFoundError.
RECEIPT_EXIT=3 (expected 3, structured receipt above — never a bare ModuleNotFoundError)
