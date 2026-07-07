# AGENTS: `tests/` — Template Project Test Suite

Technical specification for the template project test infrastructure.

## Test Inventory

| File | Test Count | Coverage Target |
|------|-----------:|-----------------|
| `test_meta.py` | 63 tests | 90%+ on `introspection.py`, `inject_metrics.py` |
| `test_metrics.py` | 13 tests | `metrics.py` helpers and integration sanity |
| `test_architecture_viz.py` | 6 tests | `architecture_viz.py` matrix/data and PNG generation |
| `test_confidentiality.py` | 9 tests | Public/private project discovery boundary |
| `test_edge_cases.py` | 39 tests | Edge cases, error branches, sibling fallback, YAML errors |
| **Total** | **130 tests** | **≥90% (see [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md))** |

## Test Classes (`test_meta.py`)

| Class | Tests | What It Validates |
|-------|------:|-------------------|
| `TestDiscoverInfrastructureModules` | 8 | Module discovery, sorting, `__init__.py` presence |
| `TestDiscoverProjects` | 7 | Project workspace detection, config loading |
| `TestCountPipelineStages` | 7 | Stage enumeration, sequential numbering |
| `TestLoadPipelineStagesFromYaml` | 4 | YAML stage parsing, tags/method/failure_mode fields |
| `TestResolveTemplateRepoRoot` | 1 | Layer-1 repo root resolution from a project path |
| `TestEnumerateNumberedScripts` | 2 | `scripts/NN_*.py` enumeration |
| `TestAnalyzeCoverageConfig` | 5 | Config parsing, threshold extraction |
| `TestBuildInfrastructureReport` | 10 | Aggregated report, computed properties |
| `TestInjectMetrics` | 17 | `load_metrics`, `render_chapter`, `render_all_chapters`, round-trip |
| `TestSelfDescriptionPins` | 2 | Self-introspection pins (this project appears in its own report) |

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
- `test_confidentiality.py`: negative-control tests proving private project names never reach public metrics or manuscript.

## Known Unreachable Branches

Three branches in `introspection.py` are structurally unreachable without
patching `sys.modules` (violates the zero-mock policy):

| Line | Branch | Why Unreachable |
|------|--------|-----------------|
| ~161 | `dir()` fallback for modules without `__all__` | All real infrastructure modules define `__all__` |
| ~198 | `if manuscript_dir.is_dir():` False branch | Logically impossible: `config.yaml` exists only inside `manuscript/` |
| ~418–419 | ImportError for `infrastructure.__version__` | `infrastructure` is always installed and importable in this repo |

(Line numbers drift as `introspection.py` grows; re-check with `grep -n` before citing exact numbers.)

## Patterns

- **Zero-Mock**: All tests run against the real repository filesystem
- **`REPO_ROOT`**: Resolved by `helpers.resolve_template_repo_root()` — walks parents of `tests/` until `infrastructure/` + `pyproject.toml` are found (typically 4 levels up), falling back to a `template` sibling
- **`PROJECT_DIR`**: Template project root (`Path(__file__).parent.parent`)
- **Assertions**: Minimum-count checks (≥8 modules, ≥2 projects, ≥5 stages) for forward compatibility
- **Negative controls**: `test_confidentiality.py` and `test_edge_cases.py` both include
  negative-control tests (private names stay out; errors are handled gracefully)
