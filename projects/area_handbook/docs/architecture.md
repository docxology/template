# Architecture: area_handbook

## Data flow

```text
data/fixtures/*.yaml
       │ load_corpus (corpus_io)
       ▼
   AreaCorpus
       │ synthesize (outline + rollups)
       ▼
 SynthesisResult  ──► build_metrics_report
       │              handbook_md builders
       ▼
output/data/*.json|.md   output/figures/*.png
       │
       └────► manuscript/*.md ──► PDF / HTML / slides (infrastructure.rendering)
```

## Layers

| Layer | Location | Rule |
|-------|----------|------|
| Domain logic | `src/*.py` | Pure functions and dataclasses; testable without pipeline |
| I/O orchestration | `scripts/*.py` | Paths, logging, writes; imports `src.*` after `sys.path` fixup |
| Narrative | `manuscript/` | Prose and citations; figures reference `../output/figures/` |

## Package imports

Tests and tooling use `from src.module import ...` with the project root on `sys.path`. Analysis scripts insert `PROJECT_DIR` at the front of `sys.path` for the same pattern. The pipeline subprocess also adds `projects/area_handbook/src`, but relative imports inside `corpus_io` require the full `src` package, hence the script preamble.

## Extension points

- **New chapters**: add `HandbookSection` rows to `HANDBOOK_TEMPLATE` in `outline.py`, add matching `themes` and manuscript `NN_*.md`, extend tests for ordering if needed.
- **Stricter corpus rules**: extend `_parse_evidence` / `_parse_theme` in `corpus_io.py` with new tests.
- **Alternate thresholds**: call `synthesize(corpus, gap_threshold=…)`; metrics and gap lists follow automatically.
