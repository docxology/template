# Source Modules

Source code for the literature meta-analysis exemplar.

| Package | Purpose |
| --- | --- |
| `literature/` | Retrieval clients, canonical `Paper` records, corpus persistence, de-duplication, full-text assessment |
| `analysis/` | Descriptive stats, text processing, embeddings, topic modeling, temporal metrics, citation networks |
| `knowledge_graph/` | Optional assertion extraction, hypothesis scoring, nanopublications, RDF/TriG export |
| `visualization/` | Headless matplotlib figures and shared style config |
| `manuscript/` | Token computation and manuscript hydration helpers |

Run the project coverage gate from the repository root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
```
