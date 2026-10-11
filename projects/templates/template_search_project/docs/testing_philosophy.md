# Testing Philosophy: The Zero-Mock Standard with an LLM Callable

The Generalized Research Template strictly forbids mocking in scientific and pipeline validation. The `search_project` exemplar honours this rule by structuring its `src/` so that every external dependency is either (a) substitutable with a real local backend or (b) injected as a callable.

## Real Dependency Boundaries

Use real local corpora, domain values, confined temporary files, controlled HTTP
services, and actual subprocesses. The exact generic adapter boundary lives in
`manuscript/layer_contract.yaml`; publication and search modules intentionally
perform mature confined I/O. A need to exercise that I/O is not a reason to
replace its semantics with a mock.

## The LLM-as-Callable Pattern

`src/template_search_project/pipeline/synthesis.py` is the textbook case. Its public functions take an `llm: Callable[[str], str]` argument:

```python
def synthesise_per_paper(
    paper: Paper,
    citation_key: str,
    *,
    llm: Callable[[str], str],
    prompt_template: str = PROMPT_PER_PAPER,
) -> SynthesisResult: ...
```

Tests pass a deterministic local function. Runtime callers pass the adapter built by `src/template_search_project/pipeline/llm_runtime.py::build_llm_callable`, which wraps `infrastructure.llm.LLMClient` (Ollama-backed). Controlled callable tests exercise synthesis independently of Ollama. Actual unpaid-provider acceptance separately executes the selected real model and binds its identity, transport, input/source custody, response, and budgets. The optional adapter emits no fabricated response when initialization is unavailable.

## The Validation Suite

| File | Targets |
|---|---|
| `tests/publish/test_config.py` | `src/template_search_project/publish/config.py` — YAML parsing, defaults, post-init validation |
| `tests/pipeline/test_pipeline.py` | `src/template_search_project/pipeline/pipeline.py` — `run_literature_pipeline` with `LocalBackend` |
| `tests/pipeline/test_pipeline_collisions.py` | `src/template_search_project/pipeline/pipeline.py::_disambiguate_citation_key` |
| `tests/pipeline/test_pipeline_integration.py` | End-to-end `run_search_pipeline.py` invocation via subprocess |
| `tests/search/test_deep_search.py` | `src/template_search_project/search/deep_search.py::run_deep_search` |
| `tests/pipeline/test_deep_improvements.py` | Deep-search edge cases (year filters, dedup, BibTeX merge) |
| `tests/pipeline/test_synthesis.py` | `src/template_search_project/pipeline/synthesis.py` prompt assembly + callable contract |
| `tests/publish/test_figures.py` | `src/template_search_project/publish/figures.py` — PNG production from `SearchResult` payloads |
| `tests/publish/test_manuscript_variables.py` | `src/template_search_project/publish/manuscript_variables.py::compute_variables` and `substitute_in_text` |
| `tests/publish/test_manuscript_integrity.py` | All manuscript markdown parses; figure refs resolve |
| `tests/analysis/test_report.py` | `src/template_search_project/analysis/report.py::write_reading_report` |
| `tests/analysis/test_analysis.py` | `src/template_search_project/analysis/analysis.py` — review-stage helpers, `validate_bibliography_completeness`, `validate_variables_resolved` |
| `tests/pipeline/test_dotenv.py` | `src/template_search_project/pipeline/dotenv.py` — stdlib `.env` loader |
| `tests/pipeline/test_llm_runtime.py` | `src/template_search_project/pipeline/llm_runtime.py` — current real adapter configuration and explicit unavailable-provider handling |
| `tests/pipeline/test_scripts.py` | `scripts/*.py` smoke runs |
| `tests/pipeline/test_script_order.py` | Explicit five-script core allowlist and opt-in deep producer/composer dependency order |
| `tests/pipeline/test_composition_script.py` | `scripts/s_compose_literature_review.py` end-to-end |
| `tests/search/test_search_invariants_and_dashboard.py` | `src/template_search_project/search/search_invariants.py` + dashboard payloads |
| `tests/publish/test_readme_config_consistency.py` | Project README claims match live `manuscript/config.yaml` |

Configuration: `projects/templates/template_search_project/pyproject.toml` (`fail_under = 90`).
Conftest: `projects/templates/template_search_project/tests/conftest.py` (sets `MPLBACKEND=Agg`, adds `src/` to `sys.path`).

Live test count and coverage are tracked in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); actual whole-selection execution must still establish the declared 90 percent floor for current source.

## Three Pillars

### 1. Infrastructure-Isolation Tests

Tests that exercise `src/template_search_project/pipeline/pipeline.py` and `src/template_search_project/search/deep_search.py` use `infrastructure.search.literature.LocalBackend` pointed at a temp-dir corpus written via `tests/conftest.py` helpers. The infrastructure suite (`tests/infra_tests/`, separate from this project) covers HTTP behaviour with `pytest-httpserver`; project tests do not need to repeat that work.

### 2. Explicit Producer Dependencies

`tests/pipeline/test_script_order.py` verifies the actual core allowlist: search,
figures, hydration, review report, and dashboard. Deep search and composition
remain explicit opt-in producers. Their tests bind current disk source/config,
actual input bytes, producer receipt, and S02 SHA before hydration. Authored
markdown and curated BibTeX must remain unchanged.

### 3. Subprocess Integration Tests

`tests/pipeline/test_pipeline_integration.py`, `tests/pipeline/test_composition_script.py`, and `tests/pipeline/test_scripts.py` invoke the orchestrator scripts via `subprocess.run` with explicit `--project-root` arguments pointing at temp directories. This exercises the real CLI surface without polluting the source tree.

## Coverage Mechanics

The current `pyproject.toml` declares branch coverage of the complete own-source
surface and a 90 percent floor. Use its actual settings rather than maintaining
an omit list in prose. Focused controls and stored counts are separate from
current whole-selection acceptance.

Run with full coverage report:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
    --cov=projects/templates/template_search_project/src \
    --cov-report=term-missing \
    --cov-fail-under=90
```

## Zero-Mock Checklist

Before submitting any test, verify all boxes:

- [ ] Test uses real JSON corpus / real `Paper` instances / real config dataclasses as inputs.
- [ ] Test calls `src/*` functions directly with that real data.
- [ ] Test asserts structural properties of the output (file written, dataclass populated, deterministic citation key) — not call counts on a fake.
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or `monkeypatch` used as a mock factory.
- [ ] LLM-touching tests pass a plain Python function as the `llm=` kwarg, never a `MagicMock`.
- [ ] Subprocess tests use `tmp_path` for `--project-root` so runs are hermetic.

## Required Negative Controls

Exercise meaningful citation collisions, unsafe output/cache ancestry, stale
source/configuration/artifacts, manual supplement substitution, and partial or
failed required producers. Preserve diagnostics and nonzero failure status.
Actual renderer tests must consume the hydrated bibliography and generated
supplement. Controlled HTTP/callable evidence does not establish fresh unpaid
retrieval or model execution; required missing live tooling is blocked.
