# `template_gold_refinement/src/figures/` - agent guide

## Purpose

Importable figure-generation package for the gold-refinement exemplar. Renders
the deterministic PNG + SVG figure set and writes the figure registry and
quality report.

## Rules

- Keep figure assembly in this package; scripts stay thin wrappers.
- Do not move refinery, purity, composition, evidence, or integrity math into
  figure modules.
- Use real project outputs or typed config inputs in tests; avoid mocks.
- Write generated files only from explicit orchestration paths.

## See Also

- [`README.md`](README.md) - quick reference
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
