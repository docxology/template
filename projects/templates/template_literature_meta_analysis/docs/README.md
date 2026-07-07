# Literature Meta-Analysis Docs

Project-local rulebook for `template_literature_meta_analysis`, a retargetable literature review and bibliometrics exemplar.

## Start Here

| Need | Read |
| --- | --- |
| Modify source or scripts | `agent_instructions.md`, then `architecture.md` |
| Add or change tests | `testing_philosophy.md` |
| Change manuscript tokens or PDF output | `rendering_pipeline.md` and `syntax_guide.md` |
| Add generated artifacts | `output_inventory.md` and `output_conventions.md` |
| Fork to a new review topic | `forking_guide.md` |
| Diagnose a failure | `troubleshooting.md` |

## Canonical Commands

```bash
uv sync --group scientific --group llm
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90 -q
uv run python projects/templates/template_literature_meta_analysis/scripts/02_meta_analysis_pipeline.py
uv run python projects/templates/template_literature_meta_analysis/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_literature_meta_analysis/scripts/05_inject_variables.py
```

Live test counts and coverage snapshots belong in `../../../../docs/_generated/COUNTS.md`; do not duplicate them here.

## Boundary Summary

- `manuscript/config.yaml` owns the review topic, search engines, relevance keywords, hypotheses, and subfield taxonomy.
- `src/literature/` owns retrieval, canonical records, corpus persistence, and de-duplication.
- `src/analysis/` owns bibliometrics, TF-IDF, topics, embeddings, entities, and temporal metrics.
- `src/knowledge_graph/` owns optional LLM extraction, hypothesis scoring, and nanopublications.
- `src/visualization/` owns headless matplotlib figure generation.
- `src/manuscript/variables/` owns `{{TOKEN}}` values.
- `scripts/` are thin stage orchestrators.

Generated `output/` files are tracked as public release artifacts when they
stay below the 50 MB public output ceiling; regenerate them from source rather
than editing them by hand.
