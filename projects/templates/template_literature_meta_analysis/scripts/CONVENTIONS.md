# Script Conventions

Scripts in this exemplar are stage wrappers for the literature meta-analysis pipeline. They coordinate paths, CLI arguments, logging, and file I/O; computation stays in `src/`.

## Correct Pattern

```python
from literature.search_runner import run_literature_search

result = run_literature_search(config_path=config_path, output_path=corpus_path)
logger.info("wrote %s papers", result.total_records)
```

## Wrong Pattern

```python
# Bad: de-duplication logic belongs in src/literature/corpus.py
seen = set()
for paper in papers:
    key = paper.title.lower().strip()
    if key not in seen:
        seen.add(key)
```

## Standard Outputs

| Directory | Contents |
| --- | --- |
| `output/data/` | Corpus, analysis JSON, topics, citation graph, optional KG outputs |
| `output/figures/` | PNG figures and `figure_registry.json` |
| `output/manuscript/` | Token-resolved manuscript markdown |
| `output/fulltext/` | Optional full-text availability/download reports |
| `output/logs/` | Stage logs when run through the root pipeline |

## Checklist

- Scripts import from `src/` modules and do not duplicate analysis logic.
- CLI flags have deterministic defaults and actionable help text.
- Errors name the missing input and the stage that produces it.
- Long-running live/network work has resume or skip semantics.
- Any new output is documented in `docs/output_inventory.md`.
