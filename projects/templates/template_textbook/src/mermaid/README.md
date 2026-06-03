# `src/mermaid/` — diagram sources and renderer

Defines the Mermaid diagrams the book uses and renders them to PNG, with a
plain-text `.mmd` fallback when the Mermaid CLI is unavailable. All logic lives
here; `scripts/generate_diagrams.py` is a thin orchestrator that calls
`generate_all_diagrams` and prints output paths.

## Modules

| File | Responsibility |
| --- | --- |
| `diagram_specs.yaml` | Declarative spec for every diagram — its id, type, and Mermaid source. Edit this to add or change a diagram. |
| `diagrams.py` | `generate_all_diagrams()` — reads the specs and produces an output for each. |
| `renderer.py` | Turns a Mermaid source into a PNG when a renderer is present; otherwise writes the source as a `.mmd` file. |

## `.mmd` fallback

Rendering Mermaid to PNG needs an external CLI that may not be installed in every
environment (or in CI). When it is missing, `renderer.py` does **not** fail: it
writes the diagram source to a `.mmd` file instead. This keeps the pipeline
deterministic and dependency-light — the `.mmd` text is itself a valid,
reviewable artifact and can be rendered later.

Note that chapters also carry an inline ```` ```mermaid ```` block in their
markdown (per the authoring contract); this package is for the standalone diagram
assets, not the inline blocks.

## Generate

```bash
uv run python scripts/generate_diagrams.py
# default output: output/figures/mermaid/
```

To add a diagram: add an entry to `diagram_specs.yaml`, then regenerate. Add a
test in `../../tests/test_mermaid.py`. Do not put diagram logic in the script.

## Supported diagram kinds

`diagrams.py` builds Mermaid source from `diagram_specs.yaml` for: `flowchart`,
`sequence`, `state`, `class`, `er`, `gantt`, `pie`, `mindmap`, `timeline`,
`quadrant`, and `journey`. Each `kind` has a builder in `_BUILDERS`; add a new
kind by writing a `build_<kind>(spec) -> str` function and registering it. The
renderer emits PNG via `mmdc` when available and falls back to `.mmd` source
otherwise, so the build never hard-fails on a missing CLI.
