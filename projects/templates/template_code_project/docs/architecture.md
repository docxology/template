# Architecture: The Thin Orchestrator Flow

The `template_code_project` exemplar is designed around a strict separation of concerns across three operational layers. Understanding this architecture before modifying any file prevents the most common errors: math appearing in scripts, reusable project logic remaining trapped in CLI files, and mocks appearing in tests.

## Layer Reference

| Layer | Primary Files | Public API | Invariants | Testability |
|---|---|---|---|---|
| **`src/` — Project Logic** | `src/optimizer.py`, `src/invariants.py`, `src/experiment_config.py`, `src/analysis/`, `src/figures/`, `src/dashboard.py`, `src/manuscript_variables.py` | Optimizer primitives plus importable analysis/figure/dashboard builders | Math primitives stay pure; `experiment_config.py` is the single loader for `manuscript/config.yaml` → `experiment:` | Direct unit tests for pure logic; integration tests for generated artifacts |
| **`scripts/` — Orchestrators** | `scripts/optimization_analysis.py`, `scripts/build_dashboard.py`, `scripts/z_generate_manuscript_variables.py`, `scripts/generate_api_docs.py`, `scripts/00_preflight.py` | CLI compatibility wrappers and script entry points | No experiment, plotting, dashboard, or manuscript-variable logic lives only in scripts; `00_preflight` and `generate_api_docs` are AESTHETIC | Subprocess/integration tests exercise real commands |
| **`infrastructure/` — Cross-Cutting** | `infrastructure/scientific/`, `infrastructure/reporting/`, `infrastructure/rendering/`, `infrastructure/core/`, `infrastructure/validation/` | Stability checks, benchmarking, PDF rendering, structured logging, progress bars | Generic reusable behavior only; no project-specific assumptions | Covered by separate `tests/infra_tests/` suite |

## Strict Dependency Direction

```
scripts/ ──→ src/            (imports and calls project behavior)
src/optimizer.py ──→ [stdlib + numpy only]
src/analysis/ ──→ infrastructure/ (project-specific generation via reusable services)
tests/   ──→ src/            (direct testing of importable project behavior)
tests/   ──→ scripts/        (CLI compatibility smoke tests)
```

No arrows go upward. Core mathematical code stays independent; project analysis modules may call infrastructure because they are the importable implementation behind the thin script wrappers.

```mermaid
graph TD
    YAML[manuscript/config.yaml] -->|experiment:| CFG[src/experiment_config.py]

    A[scripts/optimization_analysis.py] -->|delegates| A2[src/analysis/]
    A2 -->|reads| CFG
    A2 -->|pure math calls| B[src/optimizer.py]
    A2 -->|figures| FIG[src/figures/]
    FIG -->|reads| CFG
    FIG --> B

    DB[scripts/build_dashboard.py] --> DASH[src/dashboard.py]
    DASH -->|reads| CFG

    I[scripts/z_generate_manuscript_variables.py] -->|calls| I2[src/manuscript_variables.py]
    I2 -->|reads| CFG
    I2 -->|reads| J[output/data/]
    I2 -->|writes| K[output/manuscript/]

    L[tests/test_optimizer.py] -->|unit tests| B
    M[tests/test_analysis_integration.py] -->|integration| A2
    MAC[tests/test_analysis_coverage.py] -->|branch coverage| A2
    TSS[tests/test_scripts_smoke.py] -->|AESTHETIC CLI| PF[scripts/00_preflight.py]
    TSS --> GD[scripts/generate_api_docs.py]
    TDOC[tests/test_documentation.py] -->|unit tests| DOC[src/documentation.py]

    B --> N((No imports from this repo))
```

## Infrastructure Modules Used by This Project

| Module | Imported From | Used For |
|---|---|---|
| `infrastructure.scientific.stability` | `src/analysis/` | `check_numerical_stability()` across starting-point / step-size grid |
| `infrastructure.scientific.benchmarking` | `src/analysis/` | `benchmark_function()` across problem dimensions |
| `infrastructure.core.logging.utils` | `scripts/*.py` | `get_logger(__name__)` for structured log output |
| `infrastructure.core.progress` | `src/analysis/` | `PipelineProgress` progress bars for long-running loops |
| `infrastructure.reporting` | `src/analysis/`, `src/dashboard.py` | HTML dashboard generation, pipeline metrics |
| `infrastructure.validation` | `src/analysis/` | Output integrity checks on generated figures and CSV |

## Forbidden Patterns

| Pattern | Why It Is Forbidden | Correct Alternative |
|---|---|---|
| Math inside `scripts/` (e.g., gradient update step) | Cannot be unit-tested without running the full script | Move to `src/`, add a test in `TestGradientDescent` |
| `from infrastructure import ...` in `src/optimizer.py` | Breaks mathematical-layer purity | Keep optimizer primitives pure; call infrastructure from `src/analysis/` or `src/dashboard.py` |
| `print()` inside `scripts/` | Bypasses structured logging; lost in CI output | Use `get_logger(__name__).info(...)` |
| Hardcoded absolute output paths in pure math modules | Makes copied projects brittle | Keep paths relative to the project root and isolated to analysis/dashboard/manuscript-variable modules |
| `unittest.mock`, `MagicMock`, `@patch` in `tests/` | Zero-mock policy | Compute real results with real numpy arrays |
| Hardcoded step-size constants in `scripts/` or duplicate YAML parsing in `src/` | Configuration drift vs `manuscript/config.yaml` | Use `load_experiment_config()` from `src/experiment_config.py` |

## How to Add a New Algorithm

Follow these five steps in order:

1. **Add the function to `src/optimizer.py`** — Pure math only; no I/O; add type hints and a Google-style docstring; export from `__init__.py`.

2. **Write a test class in `tests/test_optimizer.py`** — Follow the zero-mock pattern; use fixed numpy arrays; assert mathematical properties; run `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`.

3. **Add the analysis call in `src/analysis/`** — Import the new function from `src/optimizer.py`; run it inside the existing experiment loop or add a new loop; write results to `projects/templates/template_code_project/output/data/` or `output/figures/`.

4. **Update output conventions** — Document the new output file in `docs/output_conventions.md`; generated `output/` files stay untracked.

5. **Update manuscript section** — Edit `manuscript/02_methodology.md` with the algorithm description using concrete file paths (e.g., `projects/templates/template_code_project/src/optimizer.py::new_function()`); add any result variables to `src/manuscript_variables.py::generate_variables()`; reference figures with `\ref{fig:label}`.
