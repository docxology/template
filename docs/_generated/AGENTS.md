# docs/_generated — technical guide

## Purpose

This directory holds **generator output** (`active_projects.md`) plus **maintainer-written** index files (`README.md`, this `AGENTS.md`). Only `active_projects.md` is overwritten by that script; do not edit it by hand. **`COUNTS.md`** is updated when maintainers refresh measured test counts and CI facts (see [`README.md`](README.md)).

## Files

| File | Source |
| --- | --- |
| [`active_projects.md`](active_projects.md) | **Generated** — `uv run python scripts/docgen/active_projects.py` |
| [`architecture_overview.md`](architecture_overview.md) / [`architecture_overview.svg`](architecture_overview.svg) / `.mmd` | **Generated** — `uv run python scripts/docgen/architecture_overview.py` |
| [`coverage_history.md`](coverage_history.md) | **Generated** — `uv run python scripts/docgen/coverage_history.py --from-dir=<dir>` (offline) or `--from-gh --days=30` (online, needs `gh`) |
| [`COUNTS.md`](COUNTS.md) | **Maintained** — ground-truthed test counts, gates, and roster notes (refresh with measured `pytest` + `generate_active_projects_doc.py`; see [`README.md`](README.md)) |
| [`hermes_knowledge_audit.json`](hermes_knowledge_audit.json) | **Historical snapshot** — legacy external audit metadata; do not use for current counts |
| [`publication_records.md`](publication_records.md) | **Generated publication matrix** — public exemplar GitHub/Zenodo/config records; refresh with `uv run python scripts/docgen/publication_records.py --refresh-external` |
| [`skills_index.md`](skills_index.md) | **Generated** — `uv run python -m infrastructure.skills write-index` |
| [`last-run-summary.md`](last-run-summary.md) | **Generated** — written by `infrastructure.reporting.multi_project_report.write_last_run_summary` (re-exported from `infrastructure.core.pipeline.multi_project`) from `scripts/runner/execute_multi_project.py` end-of-run. Schema: [`../operational/logging/output-design.md`](../operational/logging/output-design.md) |
| [`README.md`](README.md), `AGENTS.md` | **Maintainer** — policy and linking conventions |

## Conventions

- Link to [`active_projects.md`](active_projects.md) for the public CI/documentation project scope; avoid copying local `discover_projects()` rosters into other guides.
- For concrete paths in examples, default to [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/).

## See Also

- [`README.md`](README.md) — policy and regeneration commands
