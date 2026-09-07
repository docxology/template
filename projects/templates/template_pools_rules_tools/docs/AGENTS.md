# AGENTS.md — docs/ for template_pools_rules_tools

Agent-facing notes for this documentation tree. The nearest authoritative
contracts are [`../AGENTS.md`](../AGENTS.md), [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md),
[`../src/AGENTS.md`](../src/AGENTS.md), and [`../scripts/AGENTS.md`](../scripts/AGENTS.md) —
each wins over this file.

## Layout

- `src/` — pure readers and validators; no `infrastructure` imports.
  Single source of truth for return shapes: `type_defs.py` (TypedDicts).
- `scripts/` — thin orchestrators importing from `src/` only. Source
  validation fails closed: non-compliant sources stop the run before any
  figures generate (negative control:
  `tests/test_strong_rule_evaluator.py::test_section_schema_flags_missing_section`).
- `tests/` — real file paths; skip via `pytest.mark.skipif` when files absent.
- `manuscript/` — counts inject from `output/data/manuscript_variables.json`
  at render time. Never hand-author total/content/cover figure counts: the
  generator derives them from the content figure registry
  (`src/figure_support.py::INTEGRATION_FIGURE_SPECS`) and the separately
  declared cover-asset contract (`COVER_FIGURE_FILENAMES`).

## Conventions observed in this repo

- Resilience policy: all `src/` functions return `None`/empty collections and
  log a warning (never raise) when resource paths are absent, because parallel
  agents may still be populating the pools.
- Resource directories `fonds/`, `rules/`, `tools/` are read-only from this
  project — never write back to them from project code.
- Cover art is an unreferenced extra and must not be misrepresented as
  manuscript evidence.
- Keep level-two headings in manuscript sections plain-text and concise (the
  Beamer frame splitter cannot safely reuse multi-line titles).

## How docs here are maintained

- Keep this tree short and factual; one file per concern.
- Measured counts belong in `output/data/manuscript_variables.json` and the
  monorepo's generated `docs/_generated/COUNTS.md`, not here.
