# Testing Expansion Plan

This plan outlines targeted additions to strengthen regression, property-based, and performance coverage for the scientific layer and scripts.

## Goals
- Guard against silent regressions in data generation/processing, metrics, and plotting utilities.
- Add pipeline-level checks that ensure figure/data artifacts remain valid for manuscript builds.
- Keep tests deterministic and fast; mark heavier cases to allow opt-in.

## Proposed Additions
- **Property tests (Hypothesis-style)** for:
  - `data_generator.generate_synthetic_data` and `generate_correlated_data` (shape/finite checks, covariance match tolerance).
  - `data_processing.normalize_data` / `standardize_data` (idempotence, mean/std expectations).
  - `metrics.calculate_convergence_metrics` (monotone sequences converge; constant sequences yield zero residual).
- **Regression fixtures**:
  - Small golden datasets for `statistics.calculate_descriptive_stats` and `performance.analyze_convergence`.
  - Tiny matplotlib output hash (PNG byte-length + simple checksum) for `plots.plot_convergence` to detect formatting regressions without heavy image diffs.
- **Performance smoke tests** (marked `@pytest.mark.slow`):
  - Bound execution time of `performance.analyze_scalability` on synthetic inputs.
  - Ensure `simulation.SimulationBase.run` completes under a short iteration limit.
- **Script smoke tests**:
  - CLI entry tests for `analysis_pipeline.py` and `generate_scientific_figures.py` with `--dry-run` to ensure argument parsing stays stable.
  - Preflight script (see `project/scripts/manuscript_preflight.py`) invoked in tests to validate figure references exist in a temporary fixture tree.

## Test Structure
- Add property tests under `project/tests/property/` to keep them organized and optional.
- Extend existing script tests with CLI invocations using `subprocess.run(..., check=True)`.
- Add `slow` marker in `pytest.ini` (or keep inline marks) to allow selective runs.

## Tooling
- Prefer `hypothesis` for property tests; skip if not installed by marking with `pytest.importorskip("hypothesis")` to avoid new hard deps until locked.
- Use `freezegun` or `time` patching for timestamp stability in reporting tests.
- Add a minimal helper for checksuming figure outputs to avoid brittle pixel-level comparisons.

## Expected Outcomes
- Faster detection of breaking changes during refactors.
- Higher confidence in pipeline scripts via CLI smoke coverage.
- Reduced flakiness through deterministic seeds and explicit RNG handling.












