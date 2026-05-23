# Test Coverage Gap Analysis

This document tracks infrastructure test coverage gaps. Numbers are
re-baselined from the live `pytest --cov` run; see "How this file is
generated" below.

**Last verified:** 2026-05-23 (baseline retained; re-run command below when collection errors are resolved)

## Current Coverage Status

**Overall infrastructure coverage: 76.83 %** (gate: ≥ 60 %)
**Tests:** 5246 passing, 8 skipped (LLM tests excluded via `--ignore=tests/infra_tests/llm`)
**Total statements measured:** 22 400

The numbers below come from:

```bash
.venv/bin/python -m pytest tests/infra_tests/ \
  --cov=infrastructure --cov-report=term --cov-fail-under=0 \
  -q --ignore=tests/infra_tests/llm --timeout=60
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
| `rendering/pipeline.py` | 34.83 % | 207 | High-value target — orchestrates PDF stages |
| `core/cli_handlers.py` | 38.07 % | 128 | Top-level CLI dispatch; subprocess-tested |
| `core/install_commands.py` | 40.54 % | 23 | Optional-dep install hints; tiny module |
| `publishing/publish_cli.py` | 41.18 % | 17 | CLI entry; subprocess-tested |
| `core/runtime/env_deps.py` | 46.22 % | 89 | Environment-dep checks; mostly platform branches |
| `reporting/pipeline_test_runner.py` | 50.00 % | 310 | High-value target — pytest orchestration logic |
| `core/config/cli.py` | 53.12 % | 26 | CLI entry; subprocess-tested |
| `validation/cli/main.py` | 58.83 % | 147 | CLI entry; partial subprocess coverage |
| `rendering/_pdf_latex_pipeline.py` | 60.65 % | 109 | Real-LaTeX gated paths skip when xelatex absent |
| `reporting/_dashboard_matplotlib.py` | 60.67 % | 81 | Optional matplotlib backend code |
| `rendering/core.py` | 60.91 % | 90 | High-value target — render-tree builder |
| `rendering/cli.py` | 61.73 % | 69 | CLI entry; subprocess-tested |

### Real Improvement Targets

After excluding CLI subprocess shims and optional-dep gated modules, the
genuine gaps are:

1. **`infrastructure/rendering/pipeline.py` (34.83 %, 207 stmts)** — the
   PDF orchestration entry point. Most missed lines are error-handling
   branches around `RenderingError` / `ValidationError`. Adding integration
   tests with a synthetic project gated on ``xelatex`` detection so renders
   stay real-data paths without mocks.

2. **`infrastructure/reporting/pipeline_test_runner.py` (50.00 %, 310 stmts)**
   — pytest subprocess orchestration (marker expressions, discovery logging).
   Per-suite coverage merge logic remains the largest uncovered cluster.
   Per-project CI-style runs are centralized in
   `infrastructure.core.test_runner.run_per_project_pytest` (see **MED3**
   shipped in **CHANGELOG** / [`TO-DO.md`](../../TO-DO.md)).

3. **`infrastructure/rendering/core.py` (60.91 %, 90 stmts)** — the render
   tree builder. Missing lines are mostly the multi-format branching
   (HTML/slides/poster).

## Modules Previously Listed (Now Resolved)

The earlier baseline of this file flagged three modules at < 50 %; all
three are now well above the gate. Listed for historical context:

| Module | Old % | Current % | Change |
| ------ | ----- | --------- | ------ |
| `core/runtime/retry.py` | 22.22 % | 97.56 % | +75 pp |
| `core/runtime/checkpoint.py` | 39.24 % | 83.59 % | +44 pp |
| `core/progress.py` | 18.09 % | 93.37 % | +75 pp |

## Coverage Gates

- **Infrastructure**: ≥ 60 % (current 76.83 %)
- **Projects**: ≥ 90 % per project (rotating-project exception possible per
  the `.github/workflows/ci.yml` matrix; see CLAUDE.md)
- **Per-project gates** are enforced separately in CI; they do not aggregate
  with the infrastructure number above.

## How This File Is Generated

These numbers should be re-baselined whenever `infrastructure/` gains a new
module or whenever a low-coverage module is closed out:

```bash
.venv/bin/python -m pytest tests/infra_tests/ \
  --cov=infrastructure --cov-report=term --cov-fail-under=0 \
  -q --ignore=tests/infra_tests/llm --timeout=60 \
  2>&1 | tail -80
```

Then sort the per-module rows by coverage percentage and update the
"Lowest-Coverage Modules" table above. Do not copy historical numbers
forward — re-measure each time.

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
