# docs/ — template_pools_rules_tools

## What this repo is

A meta-project demonstrating integration of the three top-level resource
directories — **fonds** (passive data pools: bibliography, contacts, datasets),
**rules** (governance rule sets: soft guidelines + strong schemas), and
**tools** (executable tool entry points). Resource directories are read-only
from this project's perspective. Ground truth for integration and figure
counts lives in `output/data/manuscript_variables.json`; configuration is
owned by `manuscript/config.yaml`. See the repo [`README.md`](../README.md)
and [`../AGENTS.md`](../AGENTS.md).

## Directory map

| Path | Role |
| --- | --- |
| `src/` | Readers/appliers/evaluators: `fonds_reader.py`, `rules_applier.py`, `strong_rule_evaluator.py`, `tools_invoker.py`, `integration.py`, typed return shapes in `type_defs.py` |
| `src/` (figures) | `figure_support.py`, `figures.py`, `cover_figure.py`, `rule_hierarchy_figure.py` |
| `scripts/` | Thin orchestrators: validate sources → integration → manuscript vars → strong rules → figures |
| `tests/` | Zero-mock tests incl. property-based and fail-closed validator negatives |
| `manuscript/` | Section sources, config, references; `figures/` PNG assets + registry |
| `output/` | Integration reports, manuscript variables, figures (never hand-edited) |

## How to run / test

From the template monorepo root (per repo `AGENTS.md`):

```bash
uv run pytest projects/templates/template_pools_rules_tools/tests/ -v \
    --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90

uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
uv run python projects/templates/template_pools_rules_tools/scripts/03_generate_manuscript.py
uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py
```

## Documentation in this tree

- [`AGENTS.md`](AGENTS.md) — agent-facing layout and conventions.
- Resource-pool conventions: `fonds/AGENTS.md`, `rules/AGENTS.md`,
  `tools/AGENTS.md` at the monorepo root (linked from the repo AGENTS.md).

## Status

Publication-track exemplar: `manuscript/` is complete and gate-guarded; this
docs/ tree was added by the docs-audit pass of 2026-08-29.
