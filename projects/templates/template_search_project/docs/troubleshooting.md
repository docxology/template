# Troubleshooting

## Core analysis fails

The shipped core configuration searches `data/corpus.json` through `LocalBackend`
without enrichment, LLM synthesis, or deep search. Check the configured local
corpus and actual `output/search/results.json` diagnostics. Canonical analysis
uses the five-script allowlist in `manuscript/config.yaml`; it does not execute
every script alphabetically.

For explicitly selected remote sources, inspect actual response/error receipts.
A cached response is separate from a fresh retrieval. Runtime caches and raw
transcripts stay in ignored evidence; do not silently replace a failed provider
with local results or commit caches as publication proof.

## A citation is missing or conflicts

Standard search produces `output/bibliography/references.bib`, and explicit deep
search produces `output/bibliography/references_deep.bib`. Authored
`manuscript/*.bib` remains source input. Compare actual citation keys with those
databases and inspect `output/bibliography_projection.json` for origins/hashes.

Hydration copies curated databases and adds only new definitions to
`output/manuscript/generated_search.bib`. A collision with different title,
authors, year, or shared identifiers fails. Fix the source metadata rather than
relying on file order. Curated abstracts/keywords can remain different
annotations of the same work.

## Rendering reports undefined citations

Run hydration after its required producers. The renderer must select populated
`output/manuscript/` and its full bibliography union. Inspect actual bibliography
selection and citation-validation diagnostics. Authored references stay intact.

Explicit deep composition requires deep search, composition, then hydration
with matching configuration/overrides. Its generated section is
`output/manuscript/S02_generated_literature_review.md`; authored S01 remains
source content. Missing or stale producer/composition summaries refuse reuse.

## Deep composition or hydration rejects a dependency

`output/deep_search/producer_receipt.json` binds current disk source,
configuration, aggregate, bibliography, and consumed report/note bytes.
`composition_summary.json` additionally binds that receipt and S02's actual SHA.
Old output or a manually edited supplement cannot satisfy the checks. Rerun
explicit producers with matching configuration before hydration.

These records establish artifact dependencies. They do not establish successful
live-provider or installed-runtime acceptance.

## Output or cache paths are refused

Project consumers nominate the lexical project root for mature confined I/O.
Linked root, intermediate, and final output/cache components refuse before
external writes. Inspect actual path components and use a real confined tree.
Resolving a link away or using a one-time preflight does not repair the boundary.

## Figures are missing

`y_generate_search_figures.py` requires `output/search/results.json`; run standard
search first. Use `MPLBACKEND=Agg` for headless rendering and inspect the producer
exit/diagnostics. File existence alone does not establish current acceptance.

## Optional LLM synthesis has no output

Check `project_config.llm.enabled`, selected model/endpoint, and runtime warnings.
The optional adapter can return `None` when initialization is unavailable and
writes no placeholder synthesis. Per-paper failures remain diagnostic, and a
failed deep producer cannot qualify artifacts for composition.

Required `local-synthesis` acceptance is a separate explicit lane: unavailable
selected tooling is blocked and invalid/partial responses fail. Starting a
service or acquiring a model is an operator action, not an automatic core
prerequisite. A configured seed does not guarantee identical responses.

## Coverage or pytest imports fail

Run this project separately with the declared 90 percent branch-coverage floor.
Inspect missing branches and add real controls; do not omit source/delete tests.
Multiple exemplar `tests/` roots in one process can cause
`ImportPathMismatchError`. Use separate invocations or the strict public matrix.

See [`rendering_pipeline.md`](rendering_pipeline.md) for actual producer commands
and [`testing_philosophy.md`](testing_philosophy.md) for evidence boundaries.
