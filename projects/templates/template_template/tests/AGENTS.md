# AGENTS: `tests/` — Template Project Test Suite

Technical specification for the template project test infrastructure.

## Test Inventory

| File | Contract |
|------|----------|
| `test_meta.py` | Introspection, injection, and real-manuscript integration |
| `test_metrics.py` | Metric helpers and live-repository integration |
| `test_architecture_viz.py` | Matrix invariants and real PNG generation |
| `test_confidentiality.py` | Public/private project discovery boundary |
| `test_edge_cases.py` | Error branches, sibling fallback, and malformed-input handling |
| `test_evidence_contract.py` | Executable policy binding, evidence completeness, and an invented-result negative control |
| `test_script_entrypoints.py` | Sandboxed subprocess execution of the manuscript-metrics orchestrator |

Do not hand-maintain counts here. Re-derive live test and coverage values through
the commands above and the repository's generated counts report.

## Test Classes (`test_meta.py`)

| Class | What It Validates |
|-------|-------------------|
| `TestDiscoverInfrastructureModules` | Module discovery, sorting, `__init__.py` presence |
| `TestDiscoverProjects` | Project workspace detection and config loading |
| `TestCountPipelineStages` | Stage enumeration and numbering |
| `TestLoadPipelineStagesFromYaml` | YAML stage parsing, tags, methods, and failure modes |
| `TestResolveTemplateRepoRoot` | Layer-1 repo-root resolution from a project path |
| `TestEnumerateNumberedScripts` | `scripts/NN_*.py` enumeration |
| `TestAnalyzeCoverageConfig` | Config parsing and threshold extraction |
| `TestBuildInfrastructureReport` | Aggregated report and computed properties |
| `TestInjectMetrics` | Metrics loading, chapter rendering, and round trips |
| `TestSelfDescriptionPins` | This project appears in its own public report |

## Test Classes (`test_edge_cases.py`)

| Class | Tests | What It Validates |
|-------|------:|-------------------|
| `TestCountTestFunctionsOSError` | 1 | OSError branch in `count_test_functions` (chmod 000) |
| `TestCountDocsMissingDir` | 2 | Missing `docs/` directory returns 0 for both counters |
| `TestSaveMetricsJson` | 3 | `save_metrics_json` writes content, creates parents, returns path |
| `TestResolveTemplateRepoRootEdgeCases` | 3 | FileNotFoundError + sibling `template/` path fallback |
| `TestDiscoverInfrastructureModulesImportError` | 2 | ImportError branch + `__all__` contract verification |
| `TestProjectAnalysisFromWorkspaceEdgeCases` | 3 | Missing config, non-numbered chapters, malformed YAML |
| `TestDiscoverProjectsPublicOnlyFalse` | 2 | `public_only=False` + workspace-without-config skip |
| `TestCandidateWorkspacesFlatChild` | 3 | Flat (non-typed-subfolder) workspace children under `projects/` |
| `TestAnalyzeTestCoverageConfigYAMLError` | 2 | YAML parse error returns None; no-testing-key defaults |
| `TestBuildInfrastructureReportVersionFallback` | 2 | Version populated; minimal-repo produces valid report |
| `TestRenderChapterOSError` | 1 | OSError propagates from `render_chapter` |
| `TestRenderAllChaptersEdgeCases` | 2 | Missing manuscript dir; subdirectory skip |
| `TestValidateAllResolvedOSError` | 1 | Unreadable rendered file reported as issue |
| `TestPipelineStageLongNameWrapping` | 2 | Long names (>14 chars) wrapped; tags rendered |
| `TestLocateRepoRootEdgeCases` | 4 | FileNotFoundError + sibling fallback in `paths.locate_repo_root` |
| `TestStageColorFallback` | 3 | Unrecognized tag → default pipeline color |
| `TestModuleMetricSlug` | 3 | Dot and hyphen normalization in metric key slugs |

## Additional Test Modules

- `test_metrics.py`: verifies count helpers (`count_test_functions`, `count_docs_markdown_files`), `format_count`, `build_module_inventory_table`, and real-repo metric dictionary shape.
- `test_architecture_viz.py`: verifies comparative matrix invariants (shape, value range, label count) and PNG file generation for all 4 figures.
- `test_confidentiality.py`: negative controls proving private project names never reach public metrics or manuscript.
- `test_evidence_contract.py`: binds coverage and figure-policy tokens to executable sources, validates the full manuscript registry, and proves an unregistered result is rejected.
- `test_script_entrypoints.py`: executes the metrics script from the repository root against a temporary project tree, preventing output-side effects.

## Known Unreachable Branches

Three branches in `introspection.py` are structurally unreachable without
patching `sys.modules` (violates the zero-mock policy):

| Line | Branch | Why Unreachable |
|------|--------|-----------------|
| 161 | `dir()` fallback for modules without `__all__` | All real infrastructure modules define `__all__` |
| 198→206 | `if manuscript_dir.is_dir():` False branch | Logically impossible: `config.yaml` exists only inside `manuscript/` |
| 419–420 | ImportError for `infrastructure.__version__` | `infrastructure` is always installed and importable in this repo |

(Verified against `uv run pytest ... --cov-report=term-missing` coverage "Missing" lines
on 2026-07-07; line numbers drift as `introspection.py` grows — re-check before citing.)

## Patterns

- **Zero-Mock**: All tests run against the real repository filesystem
- **`REPO_ROOT`**: Resolved by `helpers.resolve_template_repo_root()` — walks parents of `tests/` until `infrastructure/` + `pyproject.toml` are found (typically 4 levels up), falling back to a `template` sibling
- **`PROJECT_DIR`**: Template project root (`Path(__file__).parent.parent`)
- **Assertions**: Minimum-count checks (≥8 modules, ≥2 projects, ≥5 stages) for forward compatibility
- **Negative controls**: `test_confidentiality.py` and `test_edge_cases.py` both include
  negative-control tests (private names stay out; errors are handled gracefully)
