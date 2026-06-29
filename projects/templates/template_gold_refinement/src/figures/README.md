# `template_gold_refinement/src/figures/`

Figure builders for the gold-refinement exemplar.

This package generates the publication-quality, deterministic Matplotlib
figures (PNG + SVG pairs) used by the project manuscript and scripts. It
replaces the former single-file `figures.py` module while preserving the exact
public API. Keep figure-specific data shaping and rendering here; keep refinery,
purity, composition, evidence, and integrity math in their own `src/` modules.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Facade exposing the public figure API (specs, builders, generators, registry). |
| `_common.py` | Matplotlib headless setup, `FigureSpec`, `FIGURE_SPECS`, palettes, stage labels, and shared draw/IO helpers. |
| `graphs.py` | Pure NetworkX directed-graph builders (provenance, formalism, circuit, claim-evidence). |
| `charts.py` | Bar/line chart generators (purity progression, karat grading, token density). |
| `diagrams.py` | Graph and matrix diagram generators (sankey, scatter, heatmap, gate/risk matrices, ladder). |
| `registry.py` | Figure registry, quality report, and the `generate_all_figures` orchestrator. |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
