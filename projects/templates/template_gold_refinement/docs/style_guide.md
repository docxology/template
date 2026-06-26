# Style Guide

## Python conventions

- Type hints on all public functions
- `from __future__ import annotations` at module top
- Frozen dataclasses for immutable config objects
- `logging.getLogger(__name__)` not `print()` in library code
- Headless-safe matplotlib: `matplotlib.use("Agg")` before `pyplot` import

## Naming

- Modules: lowercase (`refinery.py`, `purity.py`)
- Classes: PascalCase (`RefineryResult`, `TokenPlan`)
- Constants: UPPER_SNAKE (`CANONICAL_STAGES`, `NINE_NINES_PURITY`)
- Tokens: `{{UPPERCASE_TOKEN}}` in manuscript source

## Manuscript conventions

- One `#` heading per file (the section title)
- `{{TOKEN}}` for all config-derived or computation-derived values
- `[@fig:label]` for figure cross-references
- `[@sec:label]` for section cross-references
- `$...$` for inline math, `$$...$$` for display math
