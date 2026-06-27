# Test Coverage Gap Analysis

This document tracks infrastructure test coverage gaps by Layer-1 module. The
global infrastructure gate remains 60%; the rows below are targets and notes,
not new CI gates.

**Last verified:** 2026-06-27

**Coverage oracle:** full infrastructure gate:

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60
```

**Overall infrastructure coverage:** 83.54% (gate: >= 60%)
**Tests:** 7385 passed; 1 existing NumPy overflow warning in the scientific
stability edge-case test.
**Total statements measured:** 41,264

The sorted module rows were taken from:

```bash
uv run coverage report --sort=cover -m
```

## Module Documentation Inventory

All top-level code packages under `infrastructure/` have the expected
`README.md`, `AGENTS.md`, and `SKILL.md` files. The only top-level
documentation exception is `infrastructure/logrotate.d/`, which is a config
directory and carries `README.md` plus `AGENTS.md` but no skill-routing surface.
Ignored/generated directories such as `infrastructure/.benchmarks/` and
`infrastructure/__pycache__/` are not module packages.

No `SKILL.md` files changed in this pass, so no skill-manifest regeneration was
required.

## Target Categories

| Category | Coverage expectation | Action |
| --- | --- | --- |
| First-party logic below 60% | Add meaningful branch coverage when the branch can be driven with real files, real subprocesses, or deterministic fixtures. | Document the next concrete branch gap until tested. |
| CLI/subprocess shims | Require smoke or subprocess tests for command behavior. | Do not treat in-process 0% as a defect by itself for thin `__main__.py` or dispatch shims. |
| Optional-tool or LLM-gated modules | Exercise missing-tool, offline, and fallback behavior in the default suite. | Keep live-tool paths behind their explicit gates unless CI installs the tool. |
| Publish/security/release paths | Prefer dry-run, fake executable, or local fixture coverage. | Do not require credentials, network publication, or destructive release actions in default tests. |

## Current Low Rows

### CLI And Subprocess Shim Rows

These rows are low because coverage is collected in-process while the behavior
is intentionally command-oriented. The target is subprocess smoke coverage for
user-visible command behavior, not line-chasing through dispatch glue.

| Module | Coverage | Reason / next target |
| --- | ---: | --- |
| `autoresearch/cli.py` | 0.00% | CLI dispatch shim; add subprocess smoke when flags change. |
| `core/pipeline/multi_project_cli.py` | 0.00% | Multi-project command wrapper; keep behavior covered through orchestration and subprocess command tests. |
| `doctor/__main__.py` and other `__main__.py` files | 0.00% | Entry-point wrappers; no separate unit tests needed unless import behavior changes. |
| `documentation/active_projects_doc.py` | 0.00% | Generated-doc command shim; validate through the active-projects doc generator and docs consistency gates. |
| `methods/cli.py` | 0.00% | Methods CLI shim; add subprocess smoke for changed commands. |
| `prose/cli.py` | 0.00% | Prose CLI behavior is subprocess-tested; 0% in-process is not itself a defect. |
| `publishing/pypi_release.py` | 0.00% | Release helper; default tests should stay on dry-run/local-fixture paths. |
| `sia/cli.py` | 0.00% | SIA command shim; command behavior belongs in subprocess CLI tests. |

### First-Party Logic Below 60%

| Module | Coverage | Target note |
| --- | ---: | --- |
| `project/workspace.py` | 51.11% | Added malformed pyproject, no-table, and missing-`uv` tests; next target is subprocess coverage for init/repair flows. |
| `publishing/transmission_page_check.py` | 58.04% | Add negative fixtures for incomplete transmission pages and malformed publication metadata. |
| `rendering/docx_renderer.py` | 58.43% | Cover missing Pandoc, missing manuscript, and output-path branches without requiring DOCX generation. |
| `rendering/epub_renderer.py` | 58.43% | Cover missing Pandoc, missing manuscript, and output-path branches without requiring EPUB generation. |
| `rendering/_pipeline_summary.py` | 59.36% | Add branch coverage for warning aggregation, skipped outputs, and empty-stage summaries. |
| `documentation/publication_records.py` | 59.87% | Add fixtures for incomplete records, DOI/repository label variants, and malformed YAML. |

### Optional-Tool And Gated Rows

| Module | Coverage | Gate / fallback target |
| --- | ---: | --- |
| `llm/review/pipeline_runner.py` | 12.88% | LLM review orchestration; default suite should cover offline/fallback summaries, live LLM remains gated. |
| `sia/live_llm.py` | 35.48% | Optional Ollama feedback path; keep offline stub/failure handling in default tests. |
| `llm/review/ollama_setup.py` | 50.94% | Ollama setup path; cover missing binary/server and actionable install-message branches. |
| `search/deep_research/gemini.py` | 51.02% | External API backend; default target is config validation and missing-credential behavior. |
| `validation/security_gate.py` | 53.85% | Added missing-tool and severity aggregation tests; next target is parser coverage for each configured scanner output. |
| `llm/utils/server.py` | 55.69% | Server lifecycle path; default target is unavailable-server diagnostics and timeout handling. |
| `validation/docs/lint_runner.py` | 56.93% | Subprocess/tool-gated docs runner; cover missing `mmdc`/Chrome fallbacks and failed-tool aggregation. |
| `search/deep_research/openai.py` | 56.99% | External API backend; default target is missing-key, timeout, and malformed-response handling. |

## Recently Added Module Tests (2026-06-27)

Eight modules promoted out of the "First-Party Logic Below 60%" table. All now exceed
the 60% gate; branch coverage was driven with real files, subprocess fixtures, and
deterministic local paths — no mocks introduced.

| Module | Previous | Current | Tests added | Test file |
| --- | ---: | ---: | ---: | --- |
| `rendering/_combined_exports.py` | 15.70% | 83.43% | +24 | `tests/infra_tests/rendering/test_combined_exports.py` |
| `project/drift/runner.py` | 18.64% | 100.00% | +17 | `tests/infra_tests/project/test_thin_orchestrator_drift.py` |
| `doctor/detectors/layout.py` | 31.08% | 95.95% | +11 | `tests/infra_tests/doctor/test_detectors.py` |
| `core/install_commands.py` | 38.89% | 100.00% | +8 | `tests/infra_tests/core/test_install_commands.py` |
| `rendering/pipeline.py` | 39.37% | 96.85% | +11 | `tests/infra_tests/rendering/test_pipeline.py` |
| `core/runtime/env_deps.py` | 46.22% | 84.03% | +8 | `tests/infra_tests/core/test_env_deps.py` |
| `core/runtime/setup_checks.py` | 46.67% | 85.71% | +15 | `tests/infra_tests/core/test_setup_checks.py` |
| `project/working_render.py` | 46.67% | 90.33% | +25 | `tests/infra_tests/project/test_working_render.py` |

Scripts audit (43/49 clean thin orchestrators): six violations identified — two embed
non-trivial algorithms in scripts (`generate_api_reference_doc.py` package discovery,
`06_llm_review.py` stage-label resolution); two inline data-shaping logic that belongs
in infrastructure (`audit_filepaths.py` statistics formatting, `verify_no_mocks.py`
scan-root resolution); one embeds a mini-test-runner loop duplicating infrastructure
aggregation (`00_setup_environment.py`); one hardcodes a canonical configuration list
(`generate_stage_table_doc.py`). No hardcoded external URLs found.

Parity notes: `infrastructure/docker/` has partial coverage via
`tests/infra_tests/rendering/test_dockerfile_gen.py` (no dedicated `tests/infra_tests/docker/`
needed — not a Python package). `infrastructure/logrotate.d/` is a config directory with
zero test coverage by design; `tests/infra_tests/gates/` and `tests/infra_tests/git_hook_smoke/`
are legitimate test locations for non-infrastructure code (gate scripts and git hooks).

## Recently Added Module Tests (2026-06-26)

New subpackages from PUB-PLATFORM-1. Coverage measured via dry-run / local-fixture
paths; live network and credential-gated paths are excluded from the default suite.

| Module | Current coverage | Test file |
| --- | ---: | --- |
| `publishing/pypi/adapter.py` | dry-run paths only | `tests/infra_tests/publishing/test_pypi.py` (11 tests) |
| `publishing/static_site/registry.py` | 100% (pure factory) | `tests/infra_tests/publishing/test_static_site.py` (22 tests) |
| `publishing/archival/orchestrate.py` | dry-run paths only | `tests/infra_tests/publishing/test_archival_module.py` (57 tests) |
| `publishing/registry.py` | 100% (pure registry) | `tests/infra_tests/publishing/test_registry.py` (47 tests) |

Next targets: `orchestrate.load_credentials` fallback for missing credentials file and
`_missing_credential_receipt` return paths in providers — both driveable with `tmp_path`.

## Recently Added Module Tests (2026-06-16)

Canonical tests were added or extended in the existing module test locations;
no `*_coverage.py`, `*_full.py`, or duplicate supplement files were introduced.

| Module | Current coverage | Test file |
| --- | ---: | --- |
| `project/info.py` | 87.25% | `tests/infra_tests/project/test_info.py` |
| `project/workspace.py` | 51.11% | `tests/infra_tests/project/test_workspace.py` |
| `rendering/_pdf_section_titles.py` | 94.44% | `tests/infra_tests/rendering/test_pdf_section_titles.py` |
| `rendering/pdf_renderer.py` | 68.70% | `tests/infra_tests/rendering/test_pdf_renderer.py` |
| `validation/security_gate.py` | 53.85% | `tests/infra_tests/validation/test_security_gate.py` |
| `validation/plugin_export.py` | 68.64% | `tests/infra_tests/validation/test_plugin_export.py` |
| `autoresearch/reports.py` | 86.67% | `tests/infra_tests/autoresearch/test_autoresearch.py` |
| `benchmark/template_harness.py` | 61.25% | `tests/infra_tests/benchmark/test_template_benchmark_harness.py` |
| `reporting/executive_outputs.py` | 80.36% | `tests/infra_tests/reporting/test_executive_outputs.py` |

## Coverage Gates

- **Infrastructure:** >= 60% (current 83.54%).
- **Projects:** >= 90% per project, with rotating-project exceptions documented
  in CI and project-local `AGENTS.md` files.
- **Per-module targets:** documented here only; they are not CI gates.

## Testing Standards

- **No mocks:** every test uses real data, real files, real subprocess calls, or
  deterministic local fixtures. See
  `infrastructure/validation/output/no_mock_enforcer.py`.
- **Deterministic:** fixed RNG seeds, `MPLBACKEND=Agg`, and hermetic subprocess
  environments through repository helpers.
- **Canonical test files:** keep module tests under `tests/infra_tests/<module>/`
  and avoid new supplement tiers such as `*_coverage.py`, `*_full.py`, or
  `*_comprehensive.py` unless the production subject is coverage reporting
  itself.

## See Also

- [`testing/testing-guide.md`](testing/testing-guide.md) - testing patterns and
  fixtures.
- [`../core/architecture.md`](../core/architecture.md) - two-layer architecture
  and testing standards.
- [`../../TO-DO.md`](../../TO-DO.md) - active backlog and longer-range coverage
  follow-ups.
