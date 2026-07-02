# Manuscript Syntax Reference (search_project)

Project-specific overlay on the canonical [`docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — read that file first; this file documents **search_project**-specific conventions.

The search exemplar is the only one of the three template projects that **auto-populates** its bibliography. Two `.bib` files coexist:

| File | Source | Pipeline |
|---|---|---|
| [`references.bib`](references.bib) | Hand-curated **plus** auto-populated by `scripts/run_search_pipeline.py` | Standard single-query workflow |
| [`references_deep.bib`](references_deep.bib) | Auto-populated only — overwritten on every `run_deep_search.py` invocation | Deep-search workflow ([@sec:deep_search]) |

The Pandoc invocation merges every `manuscript/*.bib` at render time, so citations resolve uniformly across the union of the two files.

## Citations

```markdown
[@peng2011reproducible]
[@boyd2004convex; @nocedal2006numerical]
@kingma2014adam introduce adaptive optimisation.
```

Citation keys for **auto-generated** entries follow the convention `<surname><year><titleword>`, e.g. `kingma2014adam`, `nesterov2013gradient`. Collisions are resolved deterministically by `paper_to_bibentry()` in `infrastructure/reference/citation/`. See [@sec:pipeline_internals] for the collision algorithm.

When you write a manual `[@key]` reference, the key must already exist in either `references.bib` or `references_deep.bib`. To verify before render:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_search_project/manuscript/references.bib --strict
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_search_project/manuscript/references_deep.bib --strict
```

## Section labels

| File | Section H1 | Label |
|---|---|---|
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `01_introduction.md` | Introduction | `{#sec:introduction}` |
| `02_methodology.md` | Methodology | `{#sec:methodology}` |
| `03_results.md` | Results | `{#sec:results}` |
| `04_conclusion.md` | Conclusion | `{#sec:conclusion}` |
| `05_pipeline_internals.md` | Pipeline Internals | `{#sec:pipeline_internals}` |
| `06_reproducibility.md` | Reproducibility | `{#sec:reproducibility}` |
| `07_deep_search.md` | Deep Search | `{#sec:deep_search}` |
| `S01_literature_review.md` | Supplemental S1 (auto-composed) | `{#sec:supplemental_s1}` |
| `99_references.md` | References | `{#sec:references}` |

`S01_*.md` files render after the `99_*.md` references list because lexicographic order treats `S` > `9`. Add a `\newpage` LaTeX directive before the supplemental H1 (already in the script) to push it onto a fresh page.

## Figure label registry

Three diagnostic figures are produced by `scripts/y_generate_search_figures.py` and embedded in [@sec:methodology]:

| Label | PNG filename | Generator |
|---|---|---|
| `{#fig:papers_per_source}` | `output/figures/papers_per_source.png` | `src/figures.py::plot_papers_per_source` |
| `{#fig:year_histogram}` | `output/figures/year_histogram.png` | `src/figures.py::plot_year_histogram` |
| `{#fig:score_distribution}` | `output/figures/score_distribution.png` | `src/figures.py::plot_score_distribution` |

Reference with `[@fig:papers_per_source]`, `[@fig:year_histogram]`, `[@fig:score_distribution]`. Always use **underscored** labels — pandoc-crossref accepts dashes but mixed conventions confuse downstream tooling.

## `{{TOKEN}}` substitution

`scripts/z_generate_manuscript_variables.py` (and the deep-search variant) replaces these tokens at render time. Defined in [`src/manuscript_variables.py`](../src/manuscript_variables.py):

| Token | Source |
|---|---|
| `reproducible research optimization` | `config.search.query` |
| `100` | `config.search.max_results` |
| `local` | `config.search.sources` (joined) |
| `6` | `len(SearchResult.papers)` after dedup |
| `1` | distinct backends in `per_source_counts` |
| `local=6` | `per_source_counts` rendered as `key=count, …` |
| `4` | papers carrying a non-empty `doi` |
| `6` | papers carrying a non-empty `abstract` |
| `—` | applied `year_min` filter (or `—`) |
| `—` | applied `year_max` filter (or `—`) |
| `none` | `SearchResult.errors` rendered as text |
| `3` | distinct keywords in the deep-search aggregate |
| `convex optimization; stochastic gradient descent; reproducible research` | keyword list rendered as `; `-joined string |
| `arxiv, crossref, paperclip` | `config.deep_search.sources` (joined) |
| `<deep-search not run>` | unique papers across all keywords (or `<deep-search not run>`) |
| `100` | `config.deep_search.max_results_per_keyword` |

When a token has no value (e.g. before any deep-search run), the resolver substitutes the placeholder string `<deep-search not run>` so the `grep` check in [@sec:deep_search] can detect missed substitutions.

## Preamble

[`preamble.md`](preamble.md) loads the LaTeX packages required for figures, tables, citations, listings (LLM prompt verbatim blocks), and cross-references. The search project does **not** load `algorithm2e` (no pseudocode) but **does** load `listings` for prompt formatting in [@sec:deep_search].

## See also

- [`../../../../docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — Repository-wide canonical semantics
- [`AGENTS.md`](AGENTS.md) — Substitution-marker registry
- [`../docs/output_conventions.md`](../docs/output_conventions.md) — What lands in `output/`
- [`../../../../infrastructure/search/literature/SKILL.md`](../../../../infrastructure/search/literature/SKILL.md) — Search backend API
- [`../../../../infrastructure/reference/citation/SKILL.md`](../../../../infrastructure/reference/citation/SKILL.md) — BibTeX read/write API
