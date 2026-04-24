# docs/_generated — technical guide

## Purpose

This directory holds **generator output** (`active_projects.md`) plus **maintainer-written** index files (`README.md`, this `AGENTS.md`). Only `active_projects.md` is overwritten by that script; do not edit it by hand. **`canonical_facts.md`** is updated when maintainers refresh measured test counts and CI facts (see [`README.md`](README.md)).

## Files

| File | Source |
| --- | --- |
| [`active_projects.md`](active_projects.md) | **Generated** — `uv run python scripts/generate_active_projects_doc.py` |
| [`canonical_facts.md`](canonical_facts.md) | **Maintained** — ground-truthed test counts, gates, and roster notes (refresh with measured `pytest` + `generate_active_projects_doc.py`; see [`README.md`](README.md)) |
| [`README.md`](README.md), `AGENTS.md` | **Maintainer** — policy and linking conventions |

## Conventions

- Link to [`active_projects.md`](active_projects.md) for the authoritative list of discovered `projects/` names; avoid copying that roster into other guides.
- For concrete paths in examples, default to [`projects/code_project/`](../../projects/code_project/).

## See Also

- [`README.md`](README.md) — policy and regeneration commands
