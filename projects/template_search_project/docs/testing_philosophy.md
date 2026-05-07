# Testing Philosophy: The Zero-Mock Standard with an LLM Callable

The Generalized Research Template strictly forbids mocking in scientific and pipeline validation. The `search_project` exemplar honours this rule by structuring its `src/` so that every external dependency is either (a) substitutable with a real local backend or (b) injected as a callable.

## Why Zero Mocks?

The architectural insight: if a test requires a mock, the function under test is doing something that belongs in `scripts/` (orchestration) or in `infrastructure/` (cross-cutting I/O), not in `src/`. The purity of `src/synthesis.py`, `src/figures.py`, `src/manuscript_variables.py`, `src/report.py`, `src/analysis.py`, and `src/search_invariants.py` makes zero-mock testing achievable. The only modules that talk to the outside world — `src/pipeline.py` and `src/deep_search.py` — are exercised through `infrastructure.search.literature.LocalBackend` against a temp-dir corpus.

If you ever feel the urge to mock something in a test for `src/`, treat it as a signal: either use `LocalBackend` against a real corpus, or pass a deterministic callable, or move the I/O up into `scripts/`.

## The LLM-as-Callable Pattern

`src/synthesis.py` is the textbook case. Its public functions take an `llm: Callable[[str], str]` argument:

```python
def synthesise_per_paper(
    paper: Paper,
    citation_key: str,
    *,
    llm: Callable[[str], str],
    prompt_template: str = PROMPT_PER_PAPER,
) -> SynthesisResult: ...
```

Tests pass a deterministic local function. Runtime callers pass the adapter built by `src/llm_runtime.py::build_llm_callable`, which wraps `infrastructure.llm.LLMClient` (Ollama-backed). Tests therefore never depend on Ollama or on a network — and the production path uses the same function shape, so there is no test-only branch in `src/synthesis.py`.

## The Validation Suite

| File | Targets |
|---|---|
| `tests/test_config.py` | `src/config.py` — YAML parsing, defaults, post-init validation |
| `tests/test_pipeline.py` | `src/pipeline.py` — `run_literature_pipeline` with `LocalBackend` |
| `tests/test_pipeline_collisions.py` | `src/pipeline.py::_disambiguate_citation_key` |
| `tests/test_pipeline_integration.py` | End-to-end `run_search_pipeline.py` invocation via subprocess |
| `tests/test_deep_search.py` | `src/deep_search.py::run_deep_search` |
| `tests/test_deep_improvements.py` | Deep-search edge cases (year filters, dedup, BibTeX merge) |
| `tests/test_synthesis.py` | `src/synthesis.py` prompt assembly + callable contract |
| `tests/test_figures.py` | `src/figures.py` — PNG production from `SearchResult` payloads |
| `tests/test_manuscript_variables.py` | `src/manuscript_variables.py::compute_variables` and `substitute_in_text` |
| `tests/test_manuscript_integrity.py` | All manuscript markdown parses; figure refs resolve |
| `tests/test_report.py` | `src/report.py::write_reading_report` |
| `tests/test_analysis.py` | `src/analysis.py` — review-stage helpers, `validate_bibliography_completeness`, `validate_variables_resolved` |
| `tests/test_dotenv.py` | `src/dotenv.py` — stdlib `.env` loader |
| `tests/test_llm_runtime.py` | `src/llm_runtime.py` — adapter shape (deterministic stub when offline) |
| `tests/test_scripts.py` | `scripts/*.py` smoke runs |
| `tests/test_script_order.py` | Alphabetical convention: `run_*` < `s_*` < `y_*` < `z_*` < `zz_*` |
| `tests/test_composition_script.py` | `scripts/s_compose_literature_review.py` end-to-end |
| `tests/test_search_invariants_and_dashboard.py` | `src/search_invariants.py` + dashboard payloads |
| `tests/test_readme_config_consistency.py` | Project README claims match live `manuscript/config.yaml` |

Configuration: `projects/template_search_project/pyproject.toml` (`fail_under = 90`).
Conftest: `projects/template_search_project/tests/conftest.py` (sets `MPLBACKEND=Agg`, adds `src/` to `sys.path`).

The suite currently collects **266 tests** (265 passed, 1 skipped). Line coverage on `src/` typically lands at **~99.50%**, well above the 90% gate.

## Three Pillars

### 1. Infrastructure-Isolation Tests

Tests that exercise `src/pipeline.py` and `src/deep_search.py` use `infrastructure.search.literature.LocalBackend` pointed at a temp-dir corpus written via `tests/conftest.py` helpers. The infrastructure suite (`tests/infra_tests/`, separate from this project) covers HTTP behaviour with `pytest-httpserver`; project tests do not need to repeat that work.

### 2. Script-Order Test

`tests/test_script_order.py` codifies the alphabetical contract `run_* < s_* < y_* < z_* < zz_*`. The composer (`s_compose_literature_review.py`) **must** run between the search runners and the variable resolver; the test fails if a contributor adds a script with a name that breaks the order.

### 3. Subprocess Integration Tests

`tests/test_pipeline_integration.py`, `tests/test_composition_script.py`, and `tests/test_scripts.py` invoke the orchestrator scripts via `subprocess.run` with explicit `--project-root` arguments pointing at temp directories. This exercises the real CLI surface without polluting the source tree.

## Coverage Mechanics

`pyproject.toml` settings relevant to coverage:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "*/__init__.py", "*/test_*.py"]

[tool.coverage.report]
fail_under = 90
precision = 2
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

Run with full coverage report:

```bash
uv run pytest projects/template_search_project/tests/ \
    --cov=projects/template_search_project/src \
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

## Structural Rule: If You Need a Mock, Move the Code

The zero-mock constraint is self-enforcing when the architecture is correct:

- **Pure modules** (`config.py`, `synthesis.py`, `figures.py`, `manuscript_variables.py`, `report.py`, `analysis.py`, `search_invariants.py`) — testable with real data, no infrastructure.
- **Orchestration modules** (`pipeline.py`, `deep_search.py`) — testable via `LocalBackend` against a temp corpus.
- **Adapter modules** (`llm_runtime.py`) — testable for shape; the deterministic-stub path is exercised when Ollama is absent.
- **Scripts** — testable via subprocess.

If you find yourself wanting to mock `urllib`, `httpx`, or an `infrastructure.*` module inside a test for `src/`, stop. That call belongs behind a parameter or in a script. Test the contract from the project side.
