## Quality Assurance

### Zero-Mock Testing Policy

All tests use real methods exclusively [@martin2008clean; @meszaros2007xunit]. No `unittest.mock`, no `MagicMock`, no `patch` decorators. Tests that require external services (Ollama, network) use `pytest.mark` markers for conditional execution. The philosophical motivation—analogizing mock objects to Simmons et al.'s *researcher degrees of freedom* [@simmons2011falsepositive] and the pre-registration remedy [@nosek2018preregistration]—is developed fully in the [Zero-Mock Tradeoff](05a_zeromock_tradeoff.md#the-zero-mock-tradeoff) discussion. To our knowledge, no prior research software engineering framework has formalized a zero-mock policy as an *architectural invariant enforced by pipeline gates*, where mock usage is not merely discouraged but structurally prevented from passing the build.

The following example, drawn from the infrastructure test suite, illustrates zero-mock compliance:

```python
def test_discover_infrastructure_modules_returns_nonempty(tmp_path):
    # Real filesystem, real YAML parsing — no MagicMock anywhere
    modules = discover_infrastructure_modules(REPO_ROOT)
    assert len(modules) >= 8           # actual subpackages on disk
    assert any(m.name == "core" for m in modules)
```

This test exercises the real `discover_infrastructure_modules` function against the real filesystem. There are no mock objects substituting for the directory walk, no patched YAML parsers, and no synthetic return values—the test passes only if the infrastructure modules genuinely exist and are discoverable at their expected paths.

### Coverage Thresholds

The pipeline enforces two coverage tiers:

| Tier | Scope | Minimum | Current | Rationale |
|------|-------|:-------:|:-------:|-----------|
| Project | `projects/*/src/` | 90% | 90%+ | Domain code must be thoroughly validated |
| Infrastructure | `infrastructure/` | 60% | 83%+ | Broader scope, some code unreachable in test |

These thresholds are enforced at Stage 01 of the pipeline. If project test coverage falls below 90%, the pipeline halts and refuses to produce a PDF—ensuring that no published artifact is backed by undertested source code.

### Test Suite Composition

The repository maintains three test suites:

- **Infrastructure tests** (`tests/`): ~3,083 tests validating the 12 infrastructure subpackages, covering logging, rendering, validation, steganography, reporting, and LLM integration.
- **Project tests** (`projects/*/tests/`): Per-project test suites validating domain-specific logic. Sizes vary from 39 tests (`code_project`) to 505 tests (`act_inf_metaanalysis`).
- **Integration tests**: Embedded within infrastructure tests, these exercise full pipeline stages against real manuscript inputs, validating end-to-end behavior from Markdown source to rendered PDF.

### Visualization Standards

All generated figures must meet accessibility requirements:

- Minimum 16pt font size for all text elements (the accessibility floor).
- Colorblind-safe palettes (IBM Design / Wong palette) with high-contrast fallbacks.
- 150–300 DPI rendering for publication quality.
- Descriptive axis labels and figure titles.
- No reliance on color alone to convey information—redundant encoding via shape, pattern, or annotation is used where applicable.

These standards are validated by the `test_architecture_viz.py` test suite, which verifies that generated figures exist, have non-zero file size, and conform to expected output specifications. The 16pt font floor ensures readability in both screen and print contexts, while the DPI range balances file size against reproduction fidelity.
