# Rendering Pipeline: Configuration → Search → Manuscript → PDF

The `manuscript/` directory contains the narrative components of the search project. The full pipeline takes a `manuscript/config.yaml` and `data/corpus.json` (or live API responses) and produces a publication-ready combined PDF. This document describes every phase, what it produces, which scripts run it, and how to troubleshoot failures.

## The Five-Phase Flow

The pipeline has five phases. Each phase must complete before the next begins. The infrastructure pipeline runner discovers `scripts/*.py` in alphabetical order and runs them in that order; the file names enforce the sequence.

### Phase 1 — Search and Enrichment

**Scripts**:
- `scripts/run_deep_search.py` (alphabetically first when enabled)
- `scripts/run_search_pipeline.py`

**Commands**:
```bash
uv run python projects/templates/template_search_project/scripts/run_deep_search.py
uv run python projects/templates/template_search_project/scripts/run_search_pipeline.py
```

**Inputs**: `manuscript/config.yaml` (sections `search`, `enrichment`, `llm`, `deep_search`) plus `data/corpus.json` when `search.sources` includes `local`.

**`run_deep_search.py` outputs**:

| File | Location | Producer |
|---|---|---|
| `aggregate.json` | `output/deep_search/` | `src/deep_search.py::run_deep_search` |
| `aggregate_report.md` | `output/deep_search/` | same |
| `run_summary.json` | `output/deep_search/` | same |
| `<keyword_slug>/papers.json` | `output/deep_search/` | same |
| `<keyword_slug>/reading_report.md` | `output/deep_search/` | same |
| `<keyword_slug>/per_paper/<safe_id>.md` | `output/deep_search/` | LLM stage when enabled |
| `references_deep.bib` | `manuscript/` | `src/deep_search.py` |

**`run_search_pipeline.py` outputs**:

| File | Location | Producer |
|---|---|---|
| `results.json` | `output/search/` | `src/pipeline.py::run_literature_pipeline` |
| `cache/search_<hash>.json` | `output/search/` | `infrastructure.search.literature.SearchCache` |
| `corpus.json` | `output/` | `infrastructure.search.literature.write_corpus` |
| `enrichment_log.json` | `output/` | `src/pipeline.py` |
| `reading_report.md` | `output/` | `src/report.py::write_reading_report` |
| `run_summary.json` | `output/` | `src/pipeline.py` |
| `references.bib` | `manuscript/` | `src/pipeline.py` (via `infrastructure.reference.citation.paper_to_bibentry`) |
| `llm/synthesis.md`, `llm/per_paper/<safe_id>.md` | `output/` | `src/synthesis.py` (when `config.llm.enabled`) |

### Phase 2 — Compose the Literature Review

**Script**: `scripts/s_compose_literature_review.py`

**Command**:
```bash
uv run python projects/templates/template_search_project/scripts/s_compose_literature_review.py
```

**Inputs**: `output/deep_search/aggregate.json` + per-keyword `papers.json` + per-paper notes.

**Output**: `manuscript/S01_literature_review.md` — a multi-section narrative grouped by deep-search keyword, with citations into `references_deep.bib`. The composer also writes `output/deep_search/composition_summary.json` for downstream tooling.

The composer runs **between** the search runners (`run_*`) and the variable resolver (`z_*`) so the freshly composed S01 reaches the manuscript-mirroring stage. This ordering is enforced by `tests/test_script_order.py`.

### Phase 3 — Figures and Manuscript Variables

**Scripts**:
- `scripts/y_generate_search_figures.py`
- `scripts/z_generate_manuscript_variables.py`

**Commands**:
```bash
uv run python projects/templates/template_search_project/scripts/y_generate_search_figures.py
uv run python projects/templates/template_search_project/scripts/z_generate_manuscript_variables.py
```

**Inputs**: `output/search/results.json` (figures) + `manuscript/config.yaml` + `output/deep_search/aggregate.json` when present (variables).

**`y_generate_search_figures.py` outputs**:

| File | Generator (in `src/figures.py`) |
|---|---|
| `output/figures/papers_per_source.png` | `plot_papers_per_source` |
| `output/figures/year_histogram.png` | `plot_year_histogram` |
| `output/figures/score_distribution.png` | `plot_score_distribution` |

**`z_generate_manuscript_variables.py` outputs**:

| File | Content |
|---|---|
| `output/data/manuscript_variables.json` | `{ field: value }` mapping from `ManuscriptVariables` |
| `output/manuscript/*.md` | Resolved copies of `manuscript/*.md` (every `{{TOKEN}}` substituted) |
| `output/manuscript/config.yaml` | Copy of `manuscript/config.yaml` |
| `output/manuscript/*.bib` | Copies of every `manuscript/*.bib` (sorted) |

**Critical**: every `{{TOKEN}}` defined in the field set of `src/manuscript_variables.py::ManuscriptVariables` must resolve before Phase 4. If a token is unresolved, the literal `{{TOKEN_NAME}}` will appear in the rendered PDF. The `variables_resolved` review stage detects this; the `<deep-search not run>` sentinel is the exception (it is intentionally written when no aggregate exists).

### Phase 4 — Render the Combined PDF

**Script**: `scripts/pipeline/stage_03_render.py` at the **repository root** (not inside `projects/`).

**Command**:
```bash
uv run python scripts/pipeline/stage_03_render.py --project templates/template_search_project
```

**Inputs**: `output/manuscript/*.md` (resolved) + `manuscript/config.yaml` + `manuscript/preamble.md` + every `manuscript/*.bib`.

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → pdflatex |
| `infrastructure/rendering/pipeline.py` | Resolves the manuscript root (prefers `output/manuscript/`) |
| `infrastructure/rendering/manuscript_discovery.py` | Orders `*.md` files lexically (`S01_*` lands after `99_*`) |
| `infrastructure/core/config/loader.py` | Reads `config.yaml` for title, authors, metadata |

`PDFRenderer.render_combined` invokes Pandoc with `--natbib`, emits one LaTeX document, and runs BibTeX over `\bibliography{stem1,stem2,...}` built from every `manuscript/*.bib` (sorted). Citations resolve uniformly across `references.bib` ∪ `references_deep.bib`.

**Outputs**:
- `output/pdf/template_search_project_combined.pdf` — final publication PDF
- `output/tex/` — LaTeX intermediates (`.tex`, `.aux`, `.log`)
- `output/slides/` — per-section Beamer PDFs
- `output/web/` — HTML versions

### Phase 5 — Promote, Review, and Report

**Scripts** (root-level): `scripts/pipeline/stage_05_copy.py`. Project-local: `scripts/zz_generate_review_report.py` and the `scripts/review` CLI directory.

**Commands**:
```bash
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_search_project
uv run python projects/templates/template_search_project/scripts/zz_generate_review_report.py
```

**Outputs**:
- `output/templates/template_search_project/template_search_project_combined.pdf` — the promoted artifact (used by CI artifact upload and the multi-project executive report).
- `output/review/stage_*.json`, `output/review/summary.json` — per-stage review outputs from `scripts/review`.
- `output/review/REVIEW_REPORT.md` — human-readable aggregation written by `zz_generate_review_report.py`.

The review CLI (`scripts/review`) reads `review_config.yaml` to enable / disable stages. Available stages:

| Stage | Backend |
|---|---|
| `prerender_validation` | `infrastructure.validation.cli prerender` |
| `markdown_links` | `infrastructure.validation.cli links` |
| `bibtex_validation` | `infrastructure.reference.citation.cli validate` |
| `bibliography_completeness` | `src/analysis.py::validate_bibliography_completeness` |
| `variables_resolved` | `src/analysis.py::validate_variables_resolved` |
| `output_integrity` | `infrastructure.validation.cli integrity` |
| `test_suite_health` | pytest + coverage subprocess |
| `infrastructure_usage` | `src/analysis.py::audit_infrastructure_imports` (subprocess) |
| `determinism_check` | `src/analysis.py::check_determinism_artifacts` — inspects cache/run_summary/seed/temperature (no re-run) |

## `config.yaml` Controls

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page and headers | `infrastructure/core/config/loader.py` → `pdf_renderer.py` |
| `paper.version` | Title page metadata | same |
| `authors[*]` | Author list | same |
| `search.query` | Single-query search string; bound to `{{CONFIG_QUERY}}` | `src/pipeline.py`, `src/manuscript_variables.py` |
| `search.sources` | Backends invoked (`arxiv`, `crossref`, `paperclip`, `local`); bound to `{{CONFIG_SOURCES}}` | same |
| `search.year_min` / `year_max` | Defensive year filtering at search and aggregation | `src/pipeline.py` |
| `search.max_results` | Cap on returned papers | `src/pipeline.py` |
| `search.local_corpus` | Path to JSON corpus when `sources` includes `local` | `src/pipeline.py` |
| `search.cache_dir`, `search.cache_ttl_seconds` | `SearchCache` location and TTL | `infrastructure.search.literature.SearchCache` |
| `enrichment.fetch_abstracts`, `fetch_fulltext` | Per-paper enrichment toggles | `src/pipeline.py` |
| `enrichment.abstract_cache_dir`, `fulltext_cache_dir`, `max_fulltext_chars` | Cache locations and truncation | `AbstractFetcher`, `FulltextFetcher` |
| `llm.enabled` | Whether `synthesise_per_paper` and `synthesise_corpus` run | `scripts/run_search_pipeline.py` |
| `llm.model`, `seed`, `temperature` | LLM determinism knobs | `src/llm_runtime.py::build_llm_callable` |
| `llm.context_window`, `long_max_tokens`, `max_input_length`, `review_timeout` | Ollama runtime budgets | same |
| `report.output_path`, `include_per_paper`, `include_corpus_synthesis` | Reading-report assembly | `src/report.py::write_reading_report` |
| `deep_search.enabled` | Whether `run_deep_search.py` performs work (exits 2 when disabled) | `scripts/run_deep_search.py` |
| `deep_search.keywords`, `max_results_per_keyword`, `sources` | Fan-out parameters | `src/deep_search.py` |
| `deep_search.write_unified_bibtex`, `unified_bibtex_path` | `references_deep.bib` controls | same |
| `references_path` | Override the standard BibTeX output path | `src/pipeline.py` |

## Troubleshooting

### Unresolved `{{TOKEN}}` appears in PDF

**Symptom**: literal `{{TOKEN_NAME}}` in the PDF.

**Cause**: Phase 3 did not run, the token is not declared in `src/manuscript_variables.py::ManuscriptVariables`, or `output/manuscript/` is stale.

**Fix**:
```bash
ls projects/templates/template_search_project/output/data/manuscript_variables.json
uv run python projects/templates/template_search_project/scripts/z_generate_manuscript_variables.py
grep -rn "{{[A-Z_]*}}" projects/templates/template_search_project/output/manuscript/
```

### Undefined citation key, but the key is in `references_deep.bib`

**Symptom**: `BIBTEX.UNDEFINED_KEY` errors during `prerender_validation`, even though `references_deep.bib` contains the key.

**Cause**: `s_compose_literature_review.py` ran *after* `z_generate_manuscript_variables.py`, so `output/manuscript/references_deep.bib` is stale.

**Fix**: Re-run the composer **before** the resolver, or run them in alphabetical script order via `./run.sh --project templates/template_search_project --pipeline`. The pre-render gate unions every `manuscript/*.bib`; a missing or stale second file means deep-only keys fail.

### LLM stage produced no output

**Symptom**: `output/llm/` is missing or empty, even though `config.llm.enabled: true`.

**Cause / fix**: `infrastructure.llm` could not be imported, or Ollama is unreachable. Both `run_search_pipeline.py` and `run_deep_search.py` log a warning and skip the synthesis stage entirely — they do **not** write a fake placeholder. Verify with `ollama list`, `ollama pull gemma3:4b`, and `uv sync --group llm`. See [`troubleshooting.md`](troubleshooting.md#llm-stage-produced-no-output).

### `SearchCache` returns stale results

**Symptom**: a config change to `search.year_min` / `year_max` / `query` has no effect.

**Cause**: cache is keyed on canonical query identity; two callers with the same key share the cache.

**Fix**: pass `--no-cache` to the script, or delete `output/search/cache/`, or set `config.search.cache_ttl_seconds` to expire entries.

### Missing figure in PDF

**Symptom**: broken image or missing figure reference.

**Cause / fix**: Phase 3 did not run, or `output/search/results.json` is absent (`y_generate_search_figures.py` exits 2 when there is no input). Run `run_search_pipeline.py` first.

```bash
ls projects/templates/template_search_project/output/figures/*.png
```
