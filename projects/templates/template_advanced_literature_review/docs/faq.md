# FAQ

## Is the default exoplanet-atmosphere corpus empirical evidence?

No. `output/data/combined_corpus.jsonl` and the per-phase corpora are a
tracked evidence snapshot that demonstrates the full multi-phase pipeline
offline. Live claims require running `scripts/01_multi_phase_search.py`
against live engines and regenerating all downstream artifacts.

## Why three phases instead of one search?

The bundled domain (exoplanet atmospheric composition) has three distinct
methodological eras — pre-2010 foundational work, the JWST-preparation era
(2010–2021), and the current high-precision molecular-detection period
(2022+) — that call for different temporal boundaries and filters. See
`ISA.md` → `## Problem` for the full rationale, and `architecture.md` for how
phases merge into one corpus.

## Where do I change the domain or the phase design?

Edit `manuscript/config.yaml` → `project_config.search_phases` (per-phase
queries, engines, temporal filters), `llm_filters`, `phase_integration`, and
`hypothesis_definitions`. See `forking_guide.md` for the full walkthrough.

## Why does this project have symlinked source directories?

`src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`,
`src/visualization/`, and `src/config_loader.py` are real filesystem symlinks
into `template_literature_meta_analysis/src/` (ISA.md decision ARL-7): the
advanced template reuses the single-term template's bibliometrics, LLM
extraction, reproducibility scoring, and figure generation rather than
reimplementing them. `STANDALONE.md` describes how a fork materializes them
as regular files.

## Why are mocks forbidden?

Same rationale as every exemplar in this repo: the important behavior is
data transformation — phase filtering, cross-phase deduplication, provenance
tracking, hypothesis scoring — and real fixtures test that behavior directly.
See `testing_philosophy.md`.

## How do I add a new phase?

Add an entry under `manuscript/config.yaml` → `project_config.search_phases`,
give it a `depends_on` list if it should cross-validate earlier phases, and
add a matching entry to `phase_integration.quality_gates`. See
`forking_guide.md` → "Designing your phases".

## How do I add a manuscript variable?

Add the value in `src/manuscript/variables/compute.py`, or a phase-aware
value in `extractors/multi_phase.py` / `extractors/hypotheses.py`, add or
update a test, then reference `{{TOKEN}}` in manuscript source and rerun
`scripts/05_inject_variables.py`. See `syntax_guide.md` for the token
families already in use.

## Which generated files can be committed?

The tracked evidence snapshot under `output/` (below the public output size
ceiling) is committed as public release evidence. Do not hand-edit it —
fix the producer and rerun the stage. See `output_conventions.md`.
