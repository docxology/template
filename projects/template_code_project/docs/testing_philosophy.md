# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in scientific/mathematical validation.

## Why Zero Mocks?

The core insight is architectural: if a function requires a mock to be tested, it is doing I/O, calling external systems, or producing side-effects — which means it belongs in `scripts/` (as a thin orchestrator), not in `src/` (as pure logic). The purity of `src/optimizer.py` is what makes zero-mock testing achievable. Every function in `src/optimizer.py` is deterministic and side-effect-free, so tests simply call functions with real numpy arrays and verify real mathematical outputs.

If you ever feel the urge to mock something in a test for `src/`, treat it as a signal: move that code to `scripts/` and test the `src/` boundary directly.

## The Validation Suite

| File | Role |
| --- | --- |
| `test_optimizer.py` | Pure math: `quadratic_function`, `gradient_descent`, `make_quadratic_problem`, `simulate_trajectory` |
| `test_experiment_config.py` | `load_experiment_config()` and `ExperimentConfig` defaults |
| `test_analysis_integration.py` | Convergence runs, stability/benchmark reports, publishing, validation, `main()` smoke |
| `test_analysis_coverage.py` | Analysis orchestration branches: validation errors/issues, `main()` paths, citations, publishing, register_figure |
| `test_figures_orchestration.py` | Matplotlib figure generators |
| `test_scripts_smoke.py` | Auxiliary script smoke (`generate_api_docs.py`, `00_preflight.py`) |
| `test_documentation.py` | `documentation.py` API reference helpers |
| `test_dashboard_config.py` | Dashboard `_parse_args` validation, payload divergent α-sweep, config parity with YAML |
| `test_invariants.py` | `src/invariants.py` builders and schema |
| `test_invariants_and_dashboard.py` | `scripts/build_dashboard.py` end-to-end |
| `test_manuscript_variables.py` | `{{TOKEN}}` map + live manuscript cross-reference |

Configuration: `projects/template_code_project/pyproject.toml` (`fail_under = 90`, matching the root pipeline gate)

Conftest: `projects/template_code_project/tests/conftest.py` (sets `MPLBACKEND=Agg`, adds `src/` to `sys.path`)

Live test count and coverage percentage: [`docs/_generated/canonical_facts.md`](../../../docs/_generated/canonical_facts.md) (or `uv run pytest tests/ --collect-only -q` from the project directory).

## Test Class Inventory (core math — `test_optimizer.py`)

| Class | Covers |
| --- | --- |
| `TestQuadraticFunction` | `quadratic_function()` evaluation, dimension mismatch errors |
| `TestComputeGradient` | `compute_gradient()` accuracy at 1D and nD |
| `TestGradientDescent` | Convergence, iteration cap, multidimensional cases, divergent step size |
| `TestOptimizationResult` | Dataclass construction; `objective_history` |
| `TestPerformanceBenchmarks` | Real timing across dimensions |
| `TestMakeQuadraticProblem` | Factory callables usable with `gradient_descent` |
| `TestSimulateTrajectory` | Trajectory structure and monotonic improvement |

## Integration inventory (`test_analysis_integration.py`)

| Class / area | Covers |
| --- | --- |
| `TestRunConvergenceExperiment` | All configured step sizes; `on_step` callback |
| `TestScientificAnalysis` | Stability and benchmark report writers (tmp project root) |
| `TestStabilityAnalysis` | Full stability run + visualization PNG (skipped if figures unavailable) |
| `TestPerformanceBenchmarking` | Full benchmark run + visualization PNG |
| `TestPublishingHelpers` | Citation metadata and save paths |
| `TestValidationAndRegistration` | Output validation and figure registry |
| `TestMainPipelineSmoke` | `analysis.main()` writes core artifacts |

## Coverage Mechanics

`pyproject.toml` settings relevant to coverage:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "*/__init__.py", "*/test_*.py"]

[tool.coverage.report]
fail_under = 90
```

Authoritative gate (measures all of `src/`, including orchestration modules):

```bash
cd projects/template_code_project
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

## Zero-Mock Checklist

Before submitting any test, verify all boxes are checked:

- [ ] Test uses real `numpy` arrays as inputs
- [ ] Test calls `src/` functions directly with real data
- [ ] Test asserts mathematical properties (convergence, gradient accuracy, dimension shapes), not call counts
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or mock factories
- [ ] Infrastructure-dependent tests use `@pytest.mark.skipif` — real infrastructure or graceful skip, never a fake
- [ ] Timing assertions use bounds (`< 5.0`) not exact values

## Infrastructure-Dependent Test Pattern

`TestStabilityAnalysis` and `TestPerformanceBenchmarking` in `test_analysis_integration.py` call `src/analysis.py` and `src/figures.py` directly. When figure modules import cleanly, tests run real stability/benchmark paths and validate PNG output. When imports fail, tests skip cleanly — this is not a mock.

## Coverage inventory (`test_analysis_coverage.py`)

Branch and error-path tests for `src/analysis.py`: `TestFallbackLogging`, `TestValidateOutputs`, `TestSaveValidationReport`, `TestStabilityScoreBranches`, `TestScientificInfraPaths`, `TestExtractMetadataExtended`, `TestCitationsExtended`, `TestPublishingExtended`, `TestMainBranches`, `TestMainErrors`, `TestRegisterFigure`, `TestImportFallback`.

## Orchestration Branch Testing

Orchestration modules (`analysis.py`, `dashboard.py`, `figures.py`, `manuscript_variables.py`) may use **`pytest.MonkeyPatch`** on module attributes and **subprocess import isolation** to hit error paths and infrastructure fallbacks. That is not the same as mocking algorithm output: real code runs with redirected boundaries. See [`../tests/PATTERNS.md`](../tests/PATTERNS.md) and [`test_analysis_coverage.py`](../tests/test_analysis_coverage.py).

## Structural Rule: If You Need a Mock, Move the Code

- **`src/optimizer.py`, `src/invariants.py`, `src/experiment_config.py`** — Pure or config-only; no infrastructure imports
- **`src/analysis.py`, `src/figures.py`, `src/dashboard.py`, `src/manuscript_variables.py`** — Orchestration; may import `infrastructure.*` behind try/except
- **`scripts/*.py`** — CLI wrappers only

## Running the Gate

A green exit code is **not** proof the suite ran. Confirm **N collected > 0 AND coverage ≥ 90%**.

```bash
cd projects/template_code_project
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

See [`troubleshooting.md`](troubleshooting.md#tests-report-passed-but-ran-0-tests--00-coverage).
