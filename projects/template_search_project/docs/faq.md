# Frequently Asked Questions

## Architecture

### Why does `src/` import from `infrastructure/` here, when `template_code_project/src/` doesn't?

The two exemplars sit at different points on the abstraction spectrum.

- `template_code_project` owns its **own algorithm** (`src/optimizer.py`); the algorithm has no upstream dependency, so `src/` can be infrastructure-free.
- `template_search_project` has **no algorithm of its own**. Its value is in being a thin orchestration layer over `infrastructure.search.literature`, `infrastructure.reference.citation`, and `infrastructure.llm`. Forbidding those imports in `src/` would force the orchestration into `scripts/` — which would push every contributor towards mocking the infrastructure, defeating the zero-mock policy.

The boundary is preserved differently here: `src/pipeline.py` and `src/deep_search.py` are the **only** modules that touch `infrastructure.search.*`; the rest of `src/` (figures, report, manuscript_variables, analysis, search_invariants) is pure.

### Why are `src/pipeline.py` and `src/deep_search.py` separate modules instead of one big file?

They have different fan-out semantics:

- `pipeline.py::run_literature_pipeline` runs **one** `SearchQuery` against the configured sources, deduplicates on `paper.id`, enriches every result, and produces `manuscript/references.bib`.
- `deep_search.py::run_deep_search` runs **N** queries (one per keyword), each capped at `max_results_per_keyword`, fully enriches every paper, and produces a per-keyword tree under `output/deep_search/` plus the unified `manuscript/references_deep.bib`.

Splitting them keeps each function's input and output shape coherent and lets `tests/test_pipeline.py` and `tests/test_deep_search.py` exercise the two contracts independently. They both delegate citation-key generation to the same `infrastructure.reference.citation.paper_to_bibentry` utility, and `_disambiguate_citation_key` (in `src/pipeline.py`) is reused.

### Why does `src/synthesis.py` take a callable instead of an `LLMClient`?

The duck-typed `llm: Callable[[str], str]` parameter is what makes the LLM testable without Ollama. Tests pass a deterministic local function:

```python
def deterministic_llm(prompt: str) -> str:
    return f"CONTRIBUTION: stub for {prompt[:40]}"

result = synthesise_per_paper(paper, "key2024", llm=deterministic_llm)
```

Runtime callers pass the adapter built by `src/llm_runtime.py::build_llm_callable`, which wraps `infrastructure.llm.LLMClient`. The same function shape works in both worlds — there is no test-only branch in `src/synthesis.py`.

## Testing

### How many tests, and what coverage?

The suite collects **266 tests** (265 passed, 1 skipped) and reports approximately **99.50% line coverage** on `projects/template_search_project/src/`. The gate is 90%. See [`testing_philosophy.md`](testing_philosophy.md) for the file-by-file breakdown.

### How is the LLM tested without Ollama?

`src/synthesis.py` accepts a callable, so `tests/test_synthesis.py` passes a Python function as the `llm=` kwarg. `tests/test_llm_runtime.py` exercises the adapter shape and asserts that `build_llm_callable` returns a deterministic stub when `infrastructure.llm` is unimportable. No Ollama dependency at any point.

### Why 90% coverage? Can I lower it?

The gate ensures `src/` orchestration is exercised. Lowering it weakens the exemplar's authority. If coverage drops, add tests — do not lower the gate.

### Do I need to test `scripts/`?

`scripts/` is exercised by integration tests (`tests/test_scripts.py`, `tests/test_pipeline_integration.py`, `tests/test_composition_script.py`) that invoke the real CLI surface via `subprocess.run` with `--project-root` pointing at temp directories. The scripts themselves are intentionally thin so the integration coverage is sufficient.

## Search

### Live versus offline mode — how do they differ?

| Concern | Offline default | Live |
|---|---|---|
| `config.search.sources` | `[local]` | `[arxiv, crossref]` (or `[paperclip]`, etc.) |
| Inputs | `data/corpus.json` | HTTP responses from the configured backends |
| Caches written | `output/search/cache/`, `output/cache/abs/`, `output/cache/pdf/` (mostly inert offline) | All three are populated by the first run |
| Reproducibility | Byte-stable | Byte-stable after the first run, because subsequent runs hit the cache |

Switching between modes is a config change only. The `infrastructure.search.literature.LocalBackend` is the offline backend used in tests and the default config.

### Why are `year_min` / `year_max` applied twice?

Once at the search backend (when supported) and again defensively in the aggregator. Some backends ignore year filters in certain query shapes; the second pass guarantees the user's filter is honoured regardless.

### `SearchCache` collisions — when do they happen?

`SearchCache` keys on canonical query identity (sources + query string + year filters). Two distinct `SearchQuery` instances that canonicalise to the same key share a cache entry. If you change `config.search.max_results` without invalidating the cache, the cached result count is what you'll see — pass `--no-cache` or delete the cache directory to force a fresh fetch.

## LLM

### When does synthesis actually run?

Only when `config.llm.enabled: true` **and** the runtime can import `infrastructure.llm` **and** `infrastructure.llm.LLMClient` constructs successfully. All three conditions must hold. Otherwise `scripts/run_search_pipeline.py` and `scripts/run_deep_search.py` log a warning and skip the stage.

### What happens if Ollama is down?

The synthesis stage is skipped entirely. No `output/llm/synthesis.md` is written, no `output/llm/per_paper/*.md` files are written, and the reading report has no per-paper-notes / cross-corpus sections. There is **no fake placeholder**. The absence of those files is the only signal — by design — so that downstream readers cannot mistake stub output for real synthesis. See [`troubleshooting.md`](troubleshooting.md#llm-stage-produced-no-output).

### Why pin `seed=42` and `temperature=0.0`?

Ollama threads the seed through the sampler, so a pinned model + seed + zero-temperature configuration produces byte-stable text on a given hardware/model combination. The pinning lets the `determinism_check` review stage diff two consecutive runs and flag drift.

## Manuscript

### Why two `.bib` files?

`manuscript/references.bib` is produced by the single-query pipeline; `manuscript/references_deep.bib` is produced by the deep-search fan-out. They coexist because Pandoc's `--natbib` mode merges every `manuscript/*.bib` (sorted) into one bibliography at render time. Splitting the files keeps each pipeline's output isolated and reviewable independently. See [`syntax_guide.md`](syntax_guide.md#8-two-bibliography-citation-rule).

### How do I add a tracked keyword to the deep-search?

1. Edit `manuscript/config.yaml` → `deep_search.keywords:` and add the new entry.
2. Re-run `scripts/run_deep_search.py`.
3. The composer (`scripts/s_compose_literature_review.py`) will pick up the new keyword's `output/deep_search/<keyword_slug>/` tree and include it in `manuscript/S01_literature_review.md` on the next pipeline run.

No code changes required. `tests/test_readme_config_consistency.py` ensures the README's documented keyword list stays aligned with `config.yaml`.

### What is the alphabetical script-order convention?

`scripts/*.py` are discovered in lexical order. The names encode the dependency graph: `run_*` (search) < `s_*` (composer) < `y_*` (figures) < `z_*` (resolver) < `zz_*` (review). Adding a new stage means picking a name that sorts at the right point. See [`style_guide.md`](style_guide.md#alphabetical-script-order-convention).

### Where does the rendered PDF live?

Working copy:
```
projects/template_search_project/output/pdf/template_search_project_combined.pdf
```

Promoted copy (used by CI artifact upload and the multi-project executive report):
```
output/template_search_project/template_search_project_combined.pdf
```

## Common Pitfalls

### The composer ran after the resolver — why are deep citations failing?

Because `output/manuscript/references_deep.bib` is the copy the renderer reads, and it was copied **before** the composer regenerated `S01_literature_review.md`. Run them in alphabetical order (`./run.sh --pipeline` does this automatically) or manually re-run `z_generate_manuscript_variables.py` after the composer.

### My LLM call timed out

`config.llm.review_timeout` (default `600.0` seconds) bounds individual LLM requests. Long fulltext + large context can exceed this. Either raise the timeout, lower `enrichment.max_fulltext_chars`, or use `config.deep_search.llm_review_timeout` to override per stage.

### A run mutated `manuscript/references.bib` even though I didn't touch the corpus

The BibTeX writer is a deterministic function of `(corpus, citation-key generator)`. If the file mutated, one of those changed: check `git diff data/corpus.json` and the per-citation-key disambiguation suffixes in `output/run_summary.json::citation_keys`.

## See Also

- [`quickstart.md`](quickstart.md) — basic commands.
- [`architecture.md`](architecture.md) — module boundaries and data flow.
- [`output_conventions.md`](output_conventions.md) — producer / consumer mapping.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven recipes.
- [`syntax_guide.md`](syntax_guide.md) — Pandoc-crossref labels and the `{{TOKEN}}` registry.
- [`testing_philosophy.md`](testing_philosophy.md) — zero-mock and LLM-as-callable patterns.
- [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md) — manuscript-side syntax conventions.
