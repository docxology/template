# Knowledge Graph Module — Agent Directives

## Overview

The core evidence synthesis layer. Orchestration: `knowledge_graph/kg_runner.py`
(`scripts/03_build_knowledge_graph.py`). The LLM extraction sub-system is the most expensive
operation in the pipeline — use incremental mode (the default) whenever possible.

## Invariants Agents Must Preserve

- **Incremental extraction**: `llm_extraction.py` skips papers already in `nanopublications.jsonl`.
  Never delete this file without the `--clear-assertions` flag unless explicitly asked to restart.
  Deleting it triggers full LLM re-extraction (~hours on local Ollama).
- **Confidence floor**: `min_confidence: 0.6` is the validated extraction threshold. Do not lower
  it without re-running the calibration study (`κ > 0.70` requirement).
- **RDF namespace stability**: `ONTOLOGY_NAMESPACE = "http://example.org/litmeta/ontology/"` is
  published in the nanopub.trig output. Never change it without a migration script that rewrites
  all existing nanopublications.
- **Score range**: `score_hypothesis()` returns a value in [−1, +1]. A return of `0.0` is
  ambiguous (no assertions OR balanced evidence). Always check assertion counts.
- **Stable hypothesis IDs**: Each configured definition requires a unique nonempty `id`.
  Scoring, manuscript tables and figure labels read that declared identity. Row keys,
  order and names do not derive IDs. Retain an ID while changing its display label;
  changing the scientific hypothesis requires a new identity and newly generated evidence.
- **No mock policy**: Tests must use real `Assertion` objects and real score computations.

## LLM Extraction Workflow

```bash
# Incremental (default) — skips already-processed papers
python scripts/03_build_knowledge_graph.py

# Full re-extraction (WARNING: overwrites existing assertions)
python scripts/03_build_knowledge_graph.py --clear-assertions

# Score-only mode — reload from existing nanopubs, no LLM calls
python scripts/03_build_knowledge_graph.py --max-papers 0
```

Ollama must be running at `http://localhost:11434` with `gemma3:4b` pulled.

## RDF Graph Structure (per nanopublication)

```
<base>/<id>#head       — links nanopub to its three component graphs
<base>/<id>#assertion  — the claim: paper aif:asserts assertion; assertion aif:supports hypothesis
<base>/<id>#provenance — prov:wasGeneratedBy, prov:generatedAtTime, prov:wasAttributedTo
<base>/<id>#pubinfo    — dc:created, dc:creator, dc:license
```

## Adding a New Hypothesis

1. Add an explicit stable `id`, name, description and scope under
   `project_config.hypothesis_definitions` in `manuscript/config.yaml`.
2. Load the configuration with `configure_hypotheses()`; it updates the active
   scoring hypotheses and RDF categories from the declared IDs.
3. Generate evidence for the added hypothesis using the selected extraction workflow.
   Preserve existing assertion files unless deliberately requesting full re-extraction.
4. Regenerate manuscript variables so the configured evidence table includes the new row.

`STANDARD_HYPOTHESES` remains the domain-neutral set for callers without a configuration.
It does not assign IDs to configured rows.

## Known Limitations

- **Abstract-only extraction**: LLM sees only title + abstract, not full text. Claims in
  methods/results sections are missed. See manuscript Step 2 (full-text extraction) roadmap.
  The `reproducibility/` module (`src/reproducibility/`) is the concrete fix for this specific
  gap: it operates on downloaded full-text (via `literature.fulltext_download`), not the
  abstract, and decomposes methods/results claims into a scored source/method/experiment/sink
  workflow graph rather than a single hypothesis-support assertion. It is a separate module
  with its own extraction/scoring pipeline (`scripts/10_reproducibility_assessment.py`), not a
  patch to `llm_extraction.py` — this module's own abstract-only limitation is unchanged.
- **JSON parsing fragility**: LLM responses with nested JSON or escaped quotes may fail parsing.
  `parse_llm_response()` strips markdown fences but has no fallback tokenizer.
- **Assertion ID collision**: IDs use `f"llm_{paper_id}_{hypothesis_id}"`. Reprocessing the
  same paper creates a duplicate that `merge_nanopubs` deduplicates by overwrite.
