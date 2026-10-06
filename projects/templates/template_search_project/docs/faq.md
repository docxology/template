# Frequently Asked Questions

## Architecture

### Why does this project import the platform?

The project owns literature workflow policy, citation projection, composition,
and variables. It calls mature platform retrieval, citation, logging, reporting,
configuration-byte, and confined I/O APIs through the exact paths declared in
`manuscript/layer_contract.yaml`. Pure transformations stay independently testable.

### Why are standard and deep search separate?

`pipeline/pipeline.py::run_literature_pipeline` runs one query. The explicit
`search/deep_search.py::run_deep_search` fans out across keywords and retains
per-keyword diagnostics before deduplication. Both reuse the citation-key utility;
results remain generated outputs rather than edits to curated authoring files.

### Why does synthesis accept a callable?

The callable parameter lets controlled tests exercise actual prompt assembly and
response handling. Runtime callers use the platform LLM adapter. A controlled
Python response proves that contract only; it is separate from a real model call
and the audited unpaid acceptance receipt.

## Testing

### Where are the test and coverage requirements?

The project declares a 90% own-source coverage gate in `pyproject.toml`. Measured
repository snapshots live in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).
Run the isolated project suite for current evidence; a stored count is not a new run.

### How are scripts tested?

Project integration tests execute the real scripts against disposable project
roots. The scripts load configuration and call the project modules. Real
controlled HTTP responses, local corpora, generated citations, and renderer
inputs exercise the underlying behavior without replacing dependencies.

## Search and models

### What does the core default do?

It reads `data/corpus.json` with the local backend, disables abstract/fulltext
network enrichment and synthesis, and runs five declared producers. Deep search,
composition, and unpaid live acceptance require explicit commands. Paid
Paperclip/deep-research capabilities are optional and are outside this program's
acceptance.

### Does a cache hit prove current live retrieval?

No. It replays stored query results. The cache identity includes normalized query,
result cap, year filters, and source selection. Actual unpaid acceptance separately
binds current source, admitted configuration, provider responses, licensed content,
and selected model identity. Runtime cache timestamps remain operational metadata.

### When does synthesis run?

The standard config must enable it and the optional adapter must construct. An
unavailable constructor returns no callable and the optional branch is skipped;
an actual request can still fail. Deep per-paper request errors retain diagnostics
and fail producer admission. The separate required live lane fails closed when its
provider or model cannot perform the declared capability.

### Do seed and temperature guarantee identical model output?

They record generation settings. Their presence does not prove byte-identical
output, general improvement, or successful model execution. The review's
determinism check inspects configured inputs; live receipts record actual model
identity, requests, responses, and bounded execution.

## Manuscript and bibliography

### Which reference files are authored?

`manuscript/references.bib` and `manuscript/references_deep.bib` are curated inputs.
The standard and deep producers write full databases under `output/bibliography/`.
Hydration copies curated databases and projects only additional keys into
`output/manuscript/generated_search.bib`. Meaningful key collisions fail, and
curated annotations remain intact.

### Where is the generated deep review?

`output/manuscript/S02_generated_literature_review.md`. The authored S01 remains
unchanged. Composition requires a current producer dependency; hydration verifies
the composition's producer receipt, input hashes, and exact supplement bytes.
An older S02 cannot accompany a different current producer unnoticed.

### How do I add a deep keyword?

1. Select the desired sources and keywords under `project_config.deep_search`.
2. Run the deep producer explicitly with matching configuration/CLI overrides.
3. Compose with the same overrides, then hydrate before rendering.

The shipped deep branch is disabled. Core discovery does not automatically execute
these optional scripts or replay historical deep output.

### What determines script order?

The explicit `analysis.scripts` list selects standard search, figures, variables,
review, and dashboard in order. `tests/pipeline/test_script_order.py` verifies this
selection. `scripts/review` is an out-of-band CLI used by the review producer.
The default dashboard reads the current generated corpus and omits old deep
aggregates; `--aggregate` is an explicit direct input.

### Where does the PDF live?

The working combined PDF is under the project's `output/pdf/`. Successful copy
promotion places artifacts under repository `output/templates/template_search_project/`.
A stored PDF or source-only test is not a fresh render or release acceptance.

### What if a generated path aliases an authored file?

Nominated project cache and artifact I/O refuses symlink ancestors and leaves.
The unsafe operation fails; authored bytes are preserved. Inspect the alias and
repair that local generated path deliberately. The producer does not delete or
replace the authored target.

## See Also

- [`quickstart.md`](quickstart.md) — commands.
- [`architecture.md`](architecture.md) — module boundaries.
- [`output_conventions.md`](output_conventions.md) — artifact mapping.
- [`rendering_pipeline.md`](rendering_pipeline.md) — current core and explicit deep flow.
- [`syntax_guide.md`](syntax_guide.md) — citation and variable rules.
- [`testing_philosophy.md`](testing_philosophy.md) — independent test evidence.
