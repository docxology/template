# Rendering Pipeline: Configuration → Search → Manuscript → PDF

The configured core analysis reads the bundled `data/corpus.json`, writes generated
artifacts under `output/`, and hydrates authored manuscript copies for rendering.
The authored `manuscript/*.md` and curated `manuscript/*.bib` remain source inputs.
Live retrieval, optional synthesis, and deep composition have explicit commands
and separate evidence requirements.

## Configured core analysis

`manuscript/config.yaml` declares `analysis.scripts` in this order:

| Order | Script | Outputs and consumers |
|---|---|---|
| 1 | `run_search_pipeline.py` | Local search results, corpus, generated bibliography, reading report, and summary |
| 2 | `y_generate_search_figures.py` | Three diagnostic figures from `output/search/results.json` |
| 3 | `z_generate_manuscript_variables.py` | Variables, hydrated markdown/config/curated bibliography copies, and additional generated citations |
| 4 | `zz_generate_review_report.py` | Review-stage diagnostics and readable aggregation |
| 5 | `zzz_build_dashboard.py` | Coverage dashboard from the current generated corpus |

The allowlist excludes `run_deep_search.py`, `s_compose_literature_review.py`, and
`_run_unpaid_acceptance.py`. The default dashboard omits historical deep aggregates.
The normal config selects only the local backend, disables abstract/fulltext
retrieval and synthesis, and disables deep search.

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_search_project --mode core --stage analysis
```

| Generated file | Producer |
|---|---|
| `output/search/results.json` | Search CLI diagnostics |
| `output/corpus.json` | Standard literature pipeline |
| `output/bibliography/references.bib` | Standard generated citation database |
| `output/reading_report.md` | Reading-report assembly |
| `output/run_summary.json` | Search CLI summary |
| `output/figures/papers_per_source.png` | Per-source figure |
| `output/figures/year_histogram.png` | Year figure |
| `output/figures/score_distribution.png` | Score figure |
| `output/data/manuscript_variables.json` | Variable computation |
| `output/manuscript/*.md` | Hydrated authored copies |
| `output/manuscript/config.yaml` | Authored configuration copy |
| `output/manuscript/*.bib` | Curated copies plus `generated_search.bib` |
| `output/bibliography_projection.json` | Exact generated/curated/projected hashes and key origins |
| `output/web/dashboard.html` | Coverage dashboard |

Search and enrichment caches are runtime data. Their real cache timestamps are
not deterministic publication evidence. Project consumers nominate the lexical
project root for confined cache and artifact I/O; linked ancestors or leaves fail
instead of redirecting generated writes into authored sources.

## Explicit deep search and composition

Select the desired deep configuration and enable it explicitly. A local example
also requires a local corpus path and the same enabled configuration for composition:

```bash
uv run python projects/templates/template_search_project/scripts/run_deep_search.py \
  --enable --no-llm --corpus projects/templates/template_search_project/data/corpus.json
uv run python projects/templates/template_search_project/scripts/s_compose_literature_review.py \
  --enable --no-llm
```

The configured `project_config.deep_search.sources` must include the chosen
backend; the shipped disabled block has no selected deep sources. Change the
configuration deliberately before running these commands. Explicit CLI keyword
or model-disabling overrides must match between producer and composer.

| Deep artifact | Role |
|---|---|
| `output/deep_search/<slug>/papers.json` | Actual per-keyword records and backend errors |
| `output/deep_search/<slug>/reading_report.md` | Per-keyword reading report |
| `output/deep_search/<slug>/per_paper/<safe_id>.md` | Paper metadata, abstract, and optional model note |
| `output/deep_search/aggregate.json` | Deduplicated aggregate and citation keys |
| `output/deep_search/aggregate_report.md` | Aggregate report |
| `output/bibliography/references_deep.bib` | Full generated deep bibliography |
| `output/deep_search/producer_receipt.json` | Current configuration/source snapshot and exact artifact hashes |
| `output/manuscript/S02_generated_literature_review.md` | Generated supplement beside authored sections |
| `output/deep_search/composition_summary.json` | Exact producer receipt, consumed inputs, and supplement hash |

The producer dependency record is a disk-source snapshot. It establishes neither
live provider execution nor loaded-code or installed-wheel acceptance. Partial
backend, enrichment, or per-paper model failures retain diagnostics, mark the
producer failed, and produce a nonzero deep CLI exit. Composition refuses missing,
changed, failed, or differently configured producer dependencies. Absent deep
output returns exit 2; a disabled deep producer logs its intentional skip and returns 0.

Default composition writes the reserved generated S02 path. Explicit `--output`
is a direct authoring command and never mirrors into another manuscript file.
The authored `S01_literature_review.md` is preserved. Hydration can precede
composition when S02 is absent; a present S02 requires a matching composition
summary and exact current producer/input bytes. Disabled deep hydration removes
only the reserved generated S02 and projects only the standard generated database.

## Bibliography projection and hydration

The two authored reference databases remain curated inputs. Standard and deep
producers write their full databases under `output/bibliography/`. Hydration
projects additional keys into `output/manuscript/generated_search.bib` so the
renderer's bibliography union has one definition for each key. Equivalent
curated entries retain their annotations; conflicting title, author, year,
identifier, or common locator metadata fails visibly.

Variables come from `compute_variables` in
`src/template_search_project/publish/manuscript_variables.py`. Unresolved
`{{TOKEN}}` markers remain visible to the variables review. The explicit
`<deep-search not run>` sentinel records the disabled/unexecuted deep branch.

## Rendering and review

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_search_project --mode core --stage render_pdf
```

The actual renderer prefers populated `output/manuscript/`. It consumes the
hydrated markdown and the complete bibliography union in that selected directory,
including generated additional citations and S02 when admitted. PDF rendering
requires the configured Pandoc/LaTeX tools. Source checks or fixture receipts do
not substitute for a successful current rendering.

The working PDF is
`projects/templates/template_search_project/output/pdf/template_search_project_combined.pdf`.
Copy/promotion places final artifacts under
`output/templates/template_search_project/` when that stage succeeds. Runtime
logs, checkpoints, receipts, and build intermediates remain local diagnostics.

`scripts/review` reads `review_config.yaml`. Reviews cover bibliography and link
validation, variable resolution, output integrity, test health, declared
infrastructure usage, and inspection of determinism inputs. The determinism review
inspects cache/config/seed fields; it does not execute a second model run or prove
byte-identical model output.

## Troubleshooting

- Missing variables or figures: run the configured core analysis first and
  inspect the current results JSON and variables JSON.
- Missing deep citations: match producer/composer overrides, inspect the producer
  receipt and composition summary, then hydrate the generated bibliography union.
- Changed or missing dependency receipt: rerun the actual selected producer;
  historical files cannot establish a current composition.
- Model failures: distinguish skipped optional construction from a failed actual
  request. Required unpaid live acceptance uses `_run_unpaid_acceptance.py`, with
  actual source/model/transcript custody; cached or fixture text does not pass it.
- Cache misses or stale cache: query identity includes source selection, query,
  result cap, and year filters. `--no-cache` bypasses reads; writes still occur.
- Symlink refusal: choose the real project directory and real output parents.
  Removing a generated alias is a deliberate local repair, not an automatic
  deletion of an authored target.
