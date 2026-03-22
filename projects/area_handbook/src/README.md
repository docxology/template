# src/

Pure logic for corpus validation, handbook outline, synthesis, Markdown rendering, and metrics. No file I/O except via callers; no `infrastructure` imports.

## Modules

| File | Responsibility |
|------|----------------|
| `models.py` | Frozen dataclasses |
| `corpus_io.py` | YAML/JSON load + validation |
| `outline.py` | `HANDBOOK_TEMPLATE`, `build_handbook_outline` |
| `synthesis.py` | Evidence rollups, gap detection, scores |
| `handbook_md.py` | Deterministic Markdown strings |
| `metrics.py` | JSON-ready report dict |

Imports use package-relative form (`.models`) for use as `src.*` package.
