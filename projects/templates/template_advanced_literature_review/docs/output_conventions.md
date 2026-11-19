# Output Directory Conventions

`projects/templates/template_advanced_literature_review/output/` is generated
by the multi-phase literature-review pipeline and tracked as the current
public evidence snapshot when files stay below the public output ceiling. Do
not hand-edit output files; fix the producer and rerun the stage.

## Producer Sequence

The [canonical corpus/replay recipe](../STANDALONE.md#multi-phase-corpus) owns
preparation. The following commands run from the prepared project directory:

```bash
# Default synthetic fixture replay; never a live retrieval claim.
.venv/bin/python scripts/01b_fixture_phase_replay.py
.venv/bin/python scripts/02_meta_analysis_pipeline.py
.venv/bin/python scripts/03_build_knowledge_graph.py --max-papers 0

# figures, including the hypothesis dashboard
.venv/bin/python scripts/04_generate_figures.py --dpi 300

# token-hydrated manuscript copies (phase-aware tokens included)
.venv/bin/python scripts/05_inject_variables.py

# full-text availability report
.venv/bin/python scripts/06_fulltext_assessment.py

# literature evaluation harness
.venv/bin/python scripts/07_literature_evaluation.py

# deterministic offline deep-research replay (or live dispatch, opt-in)
.venv/bin/python scripts/08_deep_research_dispatch.py

# unified bibliography export
.venv/bin/python scripts/09_export_bibliography.py

# Optional, separately authorized network/full-text and reproducibility enrichment:
.venv/bin/python scripts/11_fulltext_download.py
.venv/bin/python scripts/10_reproducibility_assessment.py
# Rehydrate only after that actual enrichment:
.venv/bin/python scripts/05_inject_variables.py

# deterministic evidence/artifact validation report
.venv/bin/python scripts/11_validate_outputs.py
```

Two scripts share the `11_` prefix (`11_fulltext_download.py`,
`11_validate_outputs.py`) — they are independent, non-conflicting stages, not
a numbering error; see `agent_instructions.md` Rule 2 for the declared
dependency order.

## Layout

| Path | Meaning |
| --- | --- |
| `output/data/phase_1_foundation_corpus.jsonl`, `phase_2_jwst_corpus.jsonl`, `phase_3_molecules_corpus.jsonl` | Per-phase `Paper` records, before cross-phase merge |
| `output/data/combined_corpus.jsonl` | Cross-phase deduplicated corpus (also mirrored at `output/data/corpus.jsonl` for sibling-contract compatibility) |
| `output/data/phase_metadata.json` | Per-phase provenance: which papers came from which phase, cross-phase overlap |
| `output/data/*analysis*.json`, `topics.json`, `tfidf_data.json`, `citation_network.json`, `citation_graph.gml` | Computed analysis inputs for manuscript and figures from the declared Meta provider |
| `output/data/nanopublications.*`, `hypothesis_scores.json`, `hypothesis_trends.json`, `assertion_summary.json` | Optional knowledge-graph outputs, phase-scoped via `hypothesis_definitions.*.relevant_phases` |
| `output/data/reproducibility_scores.json`, `reproducibility_summary.json`, `workflow_graphs.jsonl` | Optional reproducibility-assessment outputs |
| `output/data/deep_research_replay.json` | Deterministic offline deep-research replay fixture output |
| `output/data/fulltext_assessment.json` | Full-text availability report |
| `output/data/literature_evaluation.json` | Literature evaluation harness output |
| `output/data/bibliography.bib` | Unified bibliography export |
| `output/figures/*.png` | Headless matplotlib figures, including `hypothesis_dashboard.png` |
| `output/figures/figure_registry.json` | Figure registry emitted by the figure runner |
| `output/manuscript/*.md` | Token-resolved manuscript sections used by renderers |
| `output/fulltext/` | Optional downloaded/assessed full-text artifacts |

## Version-Control Policy

- Commit source, config, fixtures, tests, and docs.
- Commit public template `output/` artifacts that stay under the size ceiling.
- Do not commit `.pytest_cache/`, `.venv/`, `.codegraph/`, `__pycache__/`, or egg-info.
- If a generated file is wrong, fix the producer and rerun the stage — never
  hand-edit a per-phase corpus, `phase_metadata.json`, or an injected
  manuscript file.
