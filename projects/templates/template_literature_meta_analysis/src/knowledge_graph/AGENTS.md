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
- **RDF namespace stability**: `AIF_NAMESPACE = "http://activeinference.institute/ontology/"` is
  published in the nanopub.trig output. Never change it without a migration script that rewrites
  all existing nanopublications.
- **Score range**: `score_hypothesis()` returns a value in [−1, +1]. A return of `0.0` is
  ambiguous (no assertions OR balanced evidence). Always check assertion counts.
- **Hypothesis ID order**: `STANDARD_HYPOTHESES` list order determines H1–H8 aliases, computed
  automatically by `_config_key_to_id()` in `hypothesis.py` and consumed (not defined) by
  `src/manuscript/variables/extractors/hypotheses.py`. Do not reorder `STANDARD_HYPOTHESES`
  without checking downstream alias expectations.
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

1. Add a `Hypothesis` object to `STANDARD_HYPOTHESES` in `hypothesis.py`. The H9 alias is
   derived automatically from its ordinal position by `_config_key_to_id()` — no manual
   alias mapping to edit.
2. Add the corresponding URI to `HYPOTHESIS_CATEGORIES` in `schema.py`.
3. Add keyword/description definitions in `manuscript/config.yaml` under `project_config.hypothesis_definitions`.
4. Regenerate nanopublications via `--clear-assertions` (new hypothesis won't have assertions otherwise).
5. Update `manuscript/03_results_hypothesis.md` with a new row in the evidence table.

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
  `_parse_llm_response()` strips markdown fences but has no fallback tokenizer.
- **Assertion ID collision**: IDs use `f"llm_{paper_id}_{hypothesis_id}"`. Reprocessing the
  same paper creates a duplicate that `merge_nanopubs` deduplicates by overwrite.
