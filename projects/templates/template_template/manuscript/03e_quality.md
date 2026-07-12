## Quality Assurance

### Zero-Mock Testing Policy

The repository policy prohibits mock frameworks such as `unittest.mock`, `MagicMock`, and `patch` decorators [@martin2008clean; @meszaros2007xunit]. A static gate rejects those imports, and a separate inventory surfaces semantic dependency-replacement patterns for review. Tests that require external services (Ollama or public networks) use explicit `pytest.mark` markers for conditional execution; deterministic network tests use real local HTTP servers. The philosophical motivation—analogizing excessive interaction mocking to Simmons et al.'s *researcher degrees of freedom* [@simmons2011falsepositive] and the preregistration remedy [@nosek2018preregistration]—is developed fully in the [Zero-Mock Tradeoff](05a_zeromock_tradeoff.md#the-zero-mock-tradeoff) discussion.

The following example, drawn from the infrastructure test suite, illustrates zero-mock compliance:

```python
def test_discover_infrastructure_modules_returns_nonempty(tmp_path):
    # Real filesystem, real YAML parsing — no MagicMock anywhere
    modules = discover_infrastructure_modules(REPO_ROOT)
    assert modules                     # actual subpackages on disk
    assert any(m.name == "core" for m in modules)
```

This test exercises the real `discover_infrastructure_modules` function against the real filesystem. There are no mock objects substituting for the directory walk, no patched YAML parsers, and no synthetic return values—the test passes only if the infrastructure modules genuinely exist and are discoverable at their expected paths.

### Coverage Thresholds

The pipeline enforces two coverage tiers:

| Tier | Scope | Minimum | Current | Rationale |
|------|-------|:-------:|:-------:|-----------|
| Project | `projects/*/src/` | ${coverage_floor_project}% | Reported by the current test artifact | Domain code must be thoroughly validated |
| Infrastructure | `infrastructure/` | ${coverage_floor_infrastructure}% | Reported by the current test artifact | Broader shared surface |

These thresholds are enforced at Stage 01 of the pipeline. A project test run below its declared ${coverage_floor_project}% floor fails before downstream publication stages. This manuscript deliberately does not quote an achieved coverage percentage unless a fresh coverage artifact supplies it.

### Test Suite Composition

The repository maintains three test suites:

- **Infrastructure tests** (`tests/`): ~${infra_test_count_approx} tests validating the ${module_count} infrastructure subdirectories, covering logging, rendering, validation, steganography, reporting, and LLM integration.
- **Project tests** (`projects/*/tests/`): Per-project suites whose sizes scale with each exemplar's surface area — for example ${project_template_autoresearch_project_test_count} tests in `template_autoresearch_project` and ${project_template_code_project_test_count} in `template_code_project`, with several exemplars larger still. (A true min/max span would require dedicated `project_test_count_min`/`project_test_count_max` tokens in `build_manuscript_metrics_dict`; see the meta-template's generator backlog.)
- **Integration tests**: Embedded within infrastructure tests, these exercise full pipeline stages against real manuscript inputs, validating end-to-end behavior from Markdown source to rendered PDF.

### Visualization Standards

All generated figures must meet accessibility requirements:

- Shared ${figure_font_floor_pt}pt font constant for primary text elements, with compact annotations derived from that constant.
- Colorblind-safe palettes (IBM Design / Wong palette) with high-contrast fallbacks.
- ${figure_dpi} DPI PNG rendering, sourced from the same constant used by every figure writer.
- Descriptive axis labels and figure titles.
- No reliance on color alone to convey information—redundant encoding via shape, pattern, or annotation is used where applicable.

The `test_architecture_viz.py` suite verifies that each real figure generator writes a non-empty PNG and that the comparative matrix has its declared shape and value domain. The font and render-resolution values above are injected from `viz_palette.py`, preventing prose and implementation from drifting even though visual accessibility still requires human inspection of rendered figures.
