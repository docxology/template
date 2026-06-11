# Test Coverage Gap Analysis

This document tracks infrastructure test coverage gaps. Numbers are
re-baselined from the live `pytest --cov` run; see "How this file is
generated" below.

**Last verified:** 2026-06-03 (backlog rebase: dag/registry/SIA hardening + the
sheaf-branch infrastructure wave)

**Post-baseline note (2026-06-09):** `validation/output/pipeline.py` was split
into smaller Stage 04 validation leaves. Re-run the command below before using
the exact statement and coverage figures for that package.

## Current Coverage Status

**Overall infrastructure coverage: 77.23 %** (gate: ≥ 60 %)
**Tests:** 5969 passing (non-LLM suite; LLM suite exercised separately)
**Total statements measured:** 37 296

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
| `project/drift/runner.py` | 18.64 % | 39 | Drift-check CLI runner; exercised via `check_template_drift` subprocess |
| `validation/security_gate.py` | 22.02 % | 148 | Opt-in security scan (not in default pipeline/CI); external-tool gated |
| `validation/plugin_export.py` | 27.12 % | 90 | Plugin-stage export surface; partial in-process coverage |
| `core/cli_handlers.py` | 33.50 % | 145 | Top-level CLI dispatch; subprocess-tested |
| `doctor/detectors/layout.py` | 34.85 % | 48 | Repo-layout detector; integration-tested |
| `sia/live_llm.py` | 35.48 % | 25 | Optional Ollama feedback; gated, offline-stubbed |
| `autoresearch/reports.py` | 36.67 % | 74 | Multi-project report builder; integration path |
| `project/workspace.py` | 38.89 % | 72 | Workspace management CLI; subprocess-tested |
| `rendering/_pdf_section_titles.py` | 38.89 % | 28 | LaTeX section-title helper; real-LaTeX gated |
| `project/working_render.py` | 42.07 % | 191 | Working-project render (non-default lifecycle path) |
| `core/runtime/env_deps.py` | 46.22 % | 89 | Environment-dep checks; mostly platform branches |
| `core/runtime/setup_checks.py` | 46.67 % | 79 | Setup checks; platform branches |
| `rendering/pipeline.py` | 47.48 % | 351 | Orchestration spine (↑ from 32.40 %); full render LaTeX-gated |
| `project/info.py` | 47.92 % | 64 | Project metadata resolution; branch-heavy |
| `benchmark/template_harness.py` | 51.88 % | 236 | Benchmark harness; partial integration coverage |
| `validation/docs/lint_runner.py` | 56.72 % | 139 | Docs-lint orchestration; subprocess/mmdc gated |
| `validation/output/pipeline.py` | 68.81 % | 397 | Output-validation spine; strict-zone + report paths partly gated |
| `validation/docs/mermaid_lint.py` | 71.92 % | 237 | Real-`mmdc`/chrome gated render paths |

### Real Improvement Targets

After excluding CLI subprocess shims (`*/cli.py`, `*/__main__.py`, the 0 %
`*_cli.py` entrypoints), optional-dep/tool-gated modules, and LLM-suite modules
(measured separately), the genuine gaps are:

1. **`infrastructure/rendering/pipeline.py` (47.48 %, 351 stmts)** — the PDF
   orchestration entry point, up from 32.40 % at the last baseline. Pure-logic
   helpers and the missing-project fast path are covered in
   `tests/infra_tests/rendering/test_pipeline.py`; full render paths remain
   LaTeX-gated.

2. **`infrastructure/validation/output/pipeline.py` (68.81 %, 397 stmts)** — the
   output-validation spine. The strict-zone fail-closed paths (incl. the new
   stale-fact handling) and the report-assembly branches are partially covered;
   full-render integration paths are LaTeX/pandoc gated.

3. **`infrastructure/project/working_render.py` (42.07 %, 191 stmts)** — the
   non-default working-project render path; lower priority as it is not on the
   shipped pipeline, but it is genuine first-party logic rather than a shim.

## Modules Previously Listed (Now Resolved)

The earlier baseline of this file flagged three modules at < 50 %; all
three are now well above the gate. Listed for historical context:

| Module | Old % | Current % | Change |
| ------ | ----- | --------- | ------ |
| `core/runtime/retry.py` | 22.22 % | 97.56 % | +75 pp |
| `core/runtime/checkpoint.py` | 39.24 % | 83.59 % | +44 pp |
| `core/progress.py` | 18.09 % | 93.37 % | +75 pp |
| `steganography/barcodes.py` | 11.39 % | 92.31 % | +81 pp |
| `steganography/barcode_generators.py` | 20.00 % | 86.36 % | +66 pp |

## Coverage Gates

- **Infrastructure**: ≥ 60 % (current **77.23 %**)
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

## Recently added module tests (2026-06-03)

| Module | Test file |
| --- | --- |
| `validation/xml_parser_policy.py` | `tests/infra_tests/validation/test_xml_parser_policy.py` |
| `publishing/release_workflow_zenodo.py` | `tests/infra_tests/publishing/test_release_workflow_zenodo.py` |
| `rendering/_pdf_title_page.py` | `tests/infra_tests/rendering/test_pdf_title_page.py` |
| `core/files/project_lock.py` | `tests/infra_tests/core/test_project_lock.py` |
| `core/pipeline/dag.py` (dropped-edge diagnostics) | `tests/infra_tests/core/test_dag.py` |
| `validation/evidence_registry.py` (stale-fail-closed) | `tests/infra_tests/validation/test_evidence_registry.py` |
| `validation/docs/mermaid_lint.py` (no-output fail-closed) | `tests/infra_tests/validation/docs/test_mermaid_lint.py` |
| `sia/cli.py` + loop fixture/live separation | `tests/infra_tests/sia/test_cli.py`, `test_loop_runner.py` |

## Recently added module tests (2026-05-24)

| Module | Test file |
| --- | --- |
| `reporting/pipeline_test_reporting.py` | `tests/infra_tests/reporting/test_pipeline_test_runner.py` |
| `reporting/pipeline_test_runner.py` (subprocess) | `tests/infra_tests/reporting/test_pipeline_test_runner_integration.py` |
| `validation/docs/consistency/*` | `tests/infra_tests/validation/docs/consistency/test_*.py` |
| `rendering/pipeline.py` (error paths) | `tests/infra_tests/rendering/test_pipeline.py` |
| `rendering/pdf_renderer.py` | `tests/infra_tests/rendering/test_pdf_renderer.py` |

## Supplement consolidation (2026-05-24, wave 3)

All legacy supplement tiers under `tests/infra_tests/` are removed:

- `*_expanded_coverage*`, `*_full_coverage*`, `*_coverage.py` (except modules
  whose subject is coverage reporting: `test_coverage_parser.py`,
  `test_coverage_history.py`, `test_coverage_analysis.py`,
  `test_coverage_json_parser.py`, `test_coverage_cleanup.py`,
  `test_cogant_coverage_table_check.py`)
- `*_full.py`, `*_comprehensive.py`, `*_edge_cases.py` companion files

One canonical `test_<module>.py` per production module; use
`scripts/merge_test_supplements.py` when consolidating future splits.

| Area | Canonical test files (examples) |
| --- | --- |
| validation integrity | `test_check_links.py`, `test_repo_scanner.py`, `test_validate_*_cli.py` |
| core progress / logging | `test_progress.py`, `test_logging_progress.py`, `test_pipeline_summary.py` |
| reporting stage-01 | `test_pipeline_test_runner.py`, `test_pipeline_test_runner_integration.py` |
| rendering | `test_web_renderer.py`, `test_pdf_combined_renderer.py`, `test_slides_renderer_core.py` |
| llm | `test_core.py`, `test_models.py`, `test_review_*.py` (no `*_coverage` suffix) |
| steganography | `test_encryption.py`, `test_metadata.py`, `test_overlays.py` |

## Supplement consolidation (2026-05-24, wave 2)

Wave 2 removed `*_expanded_coverage*` / `*_full_coverage*` tiers (see git history
at `f2471541`). Wave 3 completed the remaining `*_coverage.py` and `*_full.py`
merges listed above.

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
