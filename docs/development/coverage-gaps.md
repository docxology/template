# Test Coverage Gap Analysis

This document tracks infrastructure test coverage gaps by Layer-1 module. The
global infrastructure gate remains 60%; the rows below are targets and notes,
not new CI gates.

**Last verified:** 2026-06-16

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
| `rendering/_combined_exports.py` | 15.70% | Add fixture-driven branches for existing/missing PDF, HTML, DOCX, EPUB, and no-output export decisions without invoking real renderers. |
| `project/drift/runner.py` | 18.64% | Add subprocess smoke for `check_template_drift` plus branch coverage for `--strict`, `--project`, and missing-project paths. |
| `doctor/detectors/layout.py` | 31.08% | Add positive and negative repository-layout fixtures, including misplaced generated files and missing expected docs. |
| `core/install_commands.py` | 38.89% | Cover supported-tool, unsupported-tool, and platform-specific command recommendations. |
| `rendering/pipeline.py` | 39.37% | Cover missing project, missing manuscript, invalid config, and summary branches; keep full render paths LaTeX/Pandoc gated. |
| `core/runtime/env_deps.py` | 46.22% | Cover present/missing dependency branches with temporary PATH fixtures. |
| `core/runtime/setup_checks.py` | 46.67% | Cover setup-check success, missing-tool, and remediation-message branches. |
| `project/working_render.py` | 46.67% | Cover working/archive lifecycle paths, no-project handling, failed stage propagation, and output-copy decisions. |
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
