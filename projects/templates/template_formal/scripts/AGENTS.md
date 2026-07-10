# `scripts/` — Agent Guide

Three thin orchestrators: [`00_setup_environment.py`](00_setup_environment.py),
[`02_run_analysis.py`](02_run_analysis.py),
[`check_formal_specs.sh`](check_formal_specs.sh). See
[`README.md`](README.md) for what each one wires up.

## Contract

All business logic for this project lives in `src/template_formal/` (see
[`../src/template_formal/AGENTS.md`](../src/template_formal/AGENTS.md)).
Scripts here may only:

- resolve real filesystem paths (project root, output dirs),
- call one or two functions imported from `template_formal.*` or shared
  `infrastructure.*`,
- write JSON/figures the called function returned, and print the paths it
  produced (for manifest collection).

No loop over trial results, no numeric computation, no conditional beyond
argument/precondition checks belongs here. `colony/demo.py` and
`colony/visualization.py` were moved *into* `src/` from this directory for
exactly this reason (see their module docstrings) — resist moving that kind
of logic back.

## Enforcement

`scripts/audit/check_template_drift.py --strict` (run from the monorepo
root) runs an AST-based thin-orchestrator check
(`infrastructure/project/drift/orchestrator.py`'s `check_project_scripts`,
reported under the `thin_orchestrator` category) against every project's
`scripts/`. It passes clean for this project — verified this session:

```bash
cd /path/to/template  # monorepo root
uv run python scripts/audit/check_template_drift.py --strict
# -> template_drift: no drift detected.
```

If you add logic to a script here that trips this check, the fix is almost
always "move the logic into `src/template_formal/`, import it, add a test" —
not loosening the script.

## See also

- [`../AGENTS.md`](../AGENTS.md) — project root map.
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — where the moved-out business
  logic (e.g. `colony/demo.py`, `colony/visualization.py`) gets its own real
  test coverage.
