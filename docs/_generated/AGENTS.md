# docs/_generated — technical guide

## Purpose

This directory holds **generator output** (`active_projects.md`) plus **maintainer-written** index files (`README.md`, this `AGENTS.md`). Only `active_projects.md` is overwritten by that script; do not edit it by hand. **`canonical_facts.md`** is updated when maintainers refresh measured test counts and CI facts (see [`README.md`](README.md)).

## Files

| File | Source |
| --- | --- |
| [`active_projects.md`](active_projects.md) | **Generated** — `uv run python scripts/generate_active_projects_doc.py` |
| [`architecture_overview.svg`](architecture_overview.svg) / `.mmd` | **Generated** — `uv run python scripts/generate_architecture_overview.py` |
| [`coverage_history.md`](coverage_history.md) | **Generated** — `uv run python scripts/generate_coverage_history.py --from-dir=<dir>` (offline) or `--from-gh --days=30` (online, needs `gh`) |
| [`skills_index.md`](skills_index.md) | **Generated** — `uv run python -m infrastructure.skills write` |
| [`last-run-summary.md`](last-run-summary.md) | **Generated** — written by `infrastructure.core.pipeline.multi_project.write_last_run_summary` from `scripts/execute_multi_project.py` end-of-run. Schema: [`../operational/logging/output-design.md`](../operational/logging/output-design.md) |
| [`canonical_facts.md`](canonical_facts.md) | **Maintained** — ground-truthed test counts, gates, and roster notes (refresh with measured `pytest` + `generate_active_projects_doc.py`; see [`README.md`](README.md)) |
| [`README.md`](README.md), `AGENTS.md` | **Maintainer** — policy and linking conventions |

## Conventions

- Link to [`active_projects.md`](active_projects.md) for the authoritative list of discovered `projects/` names; avoid copying that roster into other guides.
- For concrete paths in examples, default to [`projects/template_code_project/`](../../projects/template_code_project/).

## See Also

- [`README.md`](README.md) — policy and regeneration commands
