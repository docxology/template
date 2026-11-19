# AGENTS.md — docs/ for template_pools_rules_tools

Agent-facing notes for this documentation tree. The nearest authoritative
contracts are [`../AGENTS.md`](../AGENTS.md), [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md),
[`../src/AGENTS.md`](../src/template_pools_rules_tools/AGENTS.md), and [`../scripts/AGENTS.md`](../scripts/AGENTS.md) —
each wins over this file.

## Layout

- `src/` — pure readers and validators; no `infrastructure` imports.
  Single source of truth for return shapes: `tools/type_defs.py` (TypedDicts).
- `scripts/` — thin orchestrators calling pure domain APIs plus the declared
  installed SDK publication/hydration adapters. Source validation fails closed:
  non-compliant sources stop the run before figures generate (negative control:
  `tests/rules/test_strong_rule_evaluator.py::test_section_schema_flags_missing_section`).
- `tests/` — real file paths; skip via `pytest.mark.skipif` when files absent.
- `manuscript/` — counts inject from `output/data/manuscript_variables.json`
  at render time. Never hand-author total/content/cover figure counts: the
  generator derives them from the content figure registry
  (`src/template_pools_rules_tools/figures/figure_support.py::INTEGRATION_FIGURE_SPECS`) and the separately
  declared cover-asset contract (`COVER_FIGURE_FILENAMES`).

## Conventions observed in this repo

- Readers may report structured absence warnings for exploratory resource
  inputs. Required public-resource, provenance, and installed acceptance gates
  fail closed on missing or unbound resources; absence is not a successful gate.
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
