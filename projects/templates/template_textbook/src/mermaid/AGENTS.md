# `src/mermaid/` — Agent Guide

Deterministic Mermaid diagram generation.

**Contents.** `diagram_specs.yaml` declares each diagram; `diagrams.py` builds specs; `renderer.py` renders to `output/figures/mermaid/` with a PNG/SVG fallback.

**Contract.** Diagrams are generated to `output/figures/mermaid/` and tracked
as public release artifacts when they stay below the size ceiling; reproduce
them with `scripts/generate_diagrams.py`.

See the project [`AGENTS.md`](../../AGENTS.md) and [`docs/`](../../docs/) for the full map.
