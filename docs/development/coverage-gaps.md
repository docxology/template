# Test Coverage Gap Analysis

This document tracks infrastructure test coverage gaps. Numbers are
re-baselined from the live `pytest --cov` run; see "How this file is
generated" below.

**Last verified:** 2026-05-24 (infrastructure thermo-nuclear quality review)

## Current Coverage Status

**Overall infrastructure coverage: 78.39 %** (gate: ≥ 60 %)
**Tests:** 5706+ passing (non-LLM suite; LLM suite exercised separately)
**Total statements measured:** 34 534

The numbers below come from:

```bash
uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-report=term --cov-fail-under=0 \
  -q --ignore=tests/infra_tests/llm --timeout=120
```

The `--ignore=tests/infra_tests/llm` flag is what the local fast suite uses;
the LLM suite is exercised separately and gates Ollama-bound paths. The
numbers in this file therefore describe the *non-LLM* surface — that's the
stable surface that ships in every CI matrix run.

## Lowest-Coverage Modules (non-LLM)

CLI `__main__` shims and `prose/cli.py` register at 0 % because they're
exercised by subprocess in integration tests rather than the in-process
suite. They are intentionally thin (≤ 60 stmts) and excluded from the
priority list below.

| Module | Coverage | Statements | Notes |
| ------ | -------- | ---------- | ----- |
| `steganography/barcodes.py` | 11.39 % | 73 | Optional barcode rendering; gated on `pyzbar`/`pillow` |
| `steganography/barcode_generators.py` | 20.00 % | 45 | Optional, same dependency gate |
| `rendering/pipeline.py` | 32.40 % → improved | 331 | Orchestration spine — `_render_individual_files` error path in `test_pipeline.py`; full render LaTeX-gated |
| `core/cli_handlers.py` | 38.07 % | 128 | Top-level CLI dispatch; subprocess-tested |
| `core/install_commands.py` | 40.54 % | 23 | Optional-dep install hints; tiny module |
| `publishing/publish_cli.py` | 41.18 % | 17 | CLI entry; subprocess-tested |
| `core/runtime/env_deps.py` | 46.22 % | 89 | Environment-dep checks; mostly platform branches |
| `reporting/pipeline_test_runner.py` | ~60 % | 137 | Stage-01 runner facade; reporting in `pipeline_test_reporting.py` (~89 %) |
| `core/pytest_orchestration.py` | ~80 % | 141 | Shared pytest subprocess policy |
| `core/config/cli.py` | 53.12 % | 26 | CLI entry; subprocess-tested |
| `validation/cli/main.py` | 58.83 % | 147 | CLI entry; partial subprocess coverage |
| `rendering/_pdf_latex_pipeline.py` | 60.65 % | 109 | Real-LaTeX gated paths skip when xelatex absent |
| `reporting/_dashboard_matplotlib.py` | 60.67 % | 81 | Optional matplotlib backend code |
| `rendering/core.py` | 65.22 % | 108 | Render tree builder — format-disable branches covered in `test_core.py` |
| `rendering/cli.py` | 61.73 % | 69 | CLI entry; subprocess-tested |

### Real Improvement Targets

After excluding CLI subprocess shims and optional-dep gated modules, the
genuine gaps are:

1. **`infrastructure/rendering/pipeline.py` (32.40 %, 331 stmts)** — the PDF
   orchestration entry point. Pure-logic helpers and the missing-project fast
   path are covered in `tests/infra_tests/rendering/test_pipeline.py`; full
   render paths remain LaTeX-gated.

2. **`infrastructure/reporting/pipeline_test_runner.py` + `pipeline_test_reporting.py`
   + `infrastructure/core/pytest_orchestration.py`** — Stage-01 orchestration
   split across three modules; subprocess integration tests in
   `test_pipeline_test_runner_integration.py`; reporting helpers in
   `test_pipeline_test_runner_coverage.py`.

3. **`infrastructure/rendering/core.py` (65.22 %, 108 stmts)** — the render
   tree builder. Format-disable and missing-source branches are covered in
   `tests/infra_tests/rendering/test_core.py`; Beamer/HTML success paths remain
   pandoc/LaTeX gated.

## Modules Previously Listed (Now Resolved)

The earlier baseline of this file flagged three modules at < 50 %; all
three are now well above the gate. Listed for historical context:

| Module | Old % | Current % | Change |
| ------ | ----- | --------- | ------ |
| `core/runtime/retry.py` | 22.22 % | 97.56 % | +75 pp |
| `core/runtime/checkpoint.py` | 39.24 % | 83.59 % | +44 pp |
| `core/progress.py` | 18.09 % | 93.37 % | +75 pp |

## Coverage Gates

- **Infrastructure**: ≥ 60 % (current **78.39 %**)
- **Projects**: ≥ 90 % per project (rotating-project exception possible per
  the `.github/workflows/ci.yml` matrix; see CLAUDE.md)
- **Per-project gates** are enforced separately in CI; they do not aggregate
  with the infrastructure number above.

## How This File Is Generated

These numbers should be re-baselined whenever `infrastructure/` gains a new
module or whenever a low-coverage module is closed out:

```bash
uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-report=term --cov-fail-under=0 \
  -q --ignore=tests/infra_tests/llm --timeout=120 \
  2>&1 | tail -80
```

Then sort the per-module rows by coverage percentage and update the
"Lowest-Coverage Modules" table above. Do not copy historical numbers
forward — re-measure each time.

## Recently added module tests (2026-05-24)

| Module | Test file |
| --- | --- |
| `reporting/pipeline_test_reporting.py` | `tests/infra_tests/reporting/test_pipeline_test_runner_coverage.py` |
| `reporting/pipeline_test_runner.py` (subprocess) | `tests/infra_tests/reporting/test_pipeline_test_runner_integration.py` |
| `validation/docs/consistency/*` | `tests/infra_tests/validation/docs/consistency/test_*.py` |
| `rendering/pipeline.py` (error paths) | `tests/infra_tests/rendering/test_pipeline.py` |
| `rendering/pdf_renderer.py` | `tests/infra_tests/rendering/test_pdf_renderer.py` |

## Recently added module tests (2026-05-23)

| Module | Test file |
| --- | --- |
| `core/runtime/setup_checks.py` | `tests/infra_tests/core/runtime/test_setup_checks.py` |
| `core/pipeline/single_stage.py` | `tests/infra_tests/core/pipeline/test_single_stage.py` |
| `core/pipeline/multi_project_cli.py` | `tests/infra_tests/core/test_multi_project.py` (existing) |
| `core/cache_gate.py` | `tests/infra_tests/core/test_cache_gate.py` |
| `project/git_guards.py` | `tests/infra_tests/project/test_git_guards.py` |
| `publishing/executable_bundle.py` | `tests/infra_tests/publishing/test_executable_bundle.py` |
| `validation/plugin_export.py` | `tests/infra_tests/validation/test_plugin_export.py` |
| `validation/security_gate.write_security_report` | `tests/infra_tests/validation/test_security_gate.py` |
| `core/pipeline/post_run_reporting.py` | `tests/infra_tests/core/pipeline/test_post_run_reporting.py` |

## Testing Standards

- **No mocks** — every test uses real data, real files, real subprocess
  calls. See `infrastructure/validation/output/no_mock_enforcer.py` for
  the CI gate.
- **Deterministic** — fixed RNG seeds, `MPLBACKEND=Agg`, hermetic env via
  `get_subprocess_env()`.
- **Real I/O** — `tmp_path` fixture for files, `pytest-httpserver` for
  HTTP, real subprocess invocations for CLIs.

## See Also

- [`testing-guide.md`](testing/testing-guide.md) — testing patterns and
  fixtures
- [`../core/architecture.md`](../core/architecture.md) — two-layer
  architecture and testing standards
- [`../../TO-DO.md`](../../TO-DO.md) — active backlog (MED3 covers the
  per-project pytest runner factor that would help close the
  `pipeline_test_runner.py` gap)
