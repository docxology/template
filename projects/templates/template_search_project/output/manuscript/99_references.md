# References {#sec:references}

This project can produce **two** BibTeX files; the template combined-PDF
path uses Pandoc `--natbib` plus BibTeX and merges every `manuscript/*.bib`
for citation resolution:

* [`manuscript/references.bib`](references.bib) — single-query pipeline
  output (`scripts/run_search_pipeline.py`).
* [`manuscript/references_deep.bib`](references_deep.bib) — deduplicated
  multi-keyword deep-search output (`scripts/run_deep_search.py`). Every
  citation in [@sec:supplemental_s1] resolves against this file. The supplemental section is auto-composed
  by `scripts/s_compose_literature_review.py`; do not edit by hand.

To regenerate the standard bibliography:

```bash
uv run python projects/templates/template_search_project/scripts/run_search_pipeline.py
```

To regenerate the deep-search bibliography (10 papers per keyword,
fully enriched, LLM-summarised):

```bash
uv run python projects/templates/template_search_project/scripts/run_deep_search.py
uv run python projects/templates/template_search_project/scripts/s_compose_literature_review.py
```

To validate that either `.bib` is syntactically clean and contains the
required fields per entry type:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_search_project/manuscript/references.bib --strict
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_search_project/manuscript/references_deep.bib --strict
```
