# Generated documentation snippets

This directory mixes **one script-generated file** with **maintainer-written** hub files (`README.md`, `AGENTS.md`).

| File | Source |
|------|--------|
| [active_projects.md](active_projects.md) | **Generated** — `uv run python scripts/generate_active_projects_doc.py` |
| [architecture_overview.svg](architecture_overview.svg) / `.mmd` | **Generated** — `uv run python scripts/generate_architecture_overview.py` |
| [coverage_history.md](coverage_history.md) | **Generated** — `uv run python scripts/generate_coverage_history.py --from-dir=<dir>` (offline) or `--from-gh --days=30` (online, needs `gh`) |
| [canonical_facts.md](canonical_facts.md) | **Generated** — live test runs, discovery, and CI configuration (refresh with `generate_active_projects_doc.py` + measured pytest; see file footer) |
| `README.md`, `AGENTS.md` | **Maintainer** — policy and conventions for linking to generated content |

## Policy

- **`projects/` is a rotating set** of workspaces. The only path **guaranteed** as the long-term control-positive layout is **`projects/template_code_project/`**. Everything else appears or disappears as maintainers promote or move projects.
- **[active_projects.md](active_projects.md)** lists active `projects/` names from `discover_projects()` **at generation time**. Treat it as authoritative for that moment; do not duplicate that roster in RUN_GUIDE, PAI, security tables, or similar.
- For walkthroughs, commands, and “see also” paths, use **`projects/template_code_project/`** as the control-positive exemplar unless the doc’s purpose is to compare layouts.
- Describe other work as folder patterns (`projects/{name}/`, `projects_in_progress/`, `projects_archive/`) rather than enumerating sibling projects in prose as if permanent.

## Regeneration

**Active projects** — after adding, removing, or renaming directories under `projects/`:

```bash
uv run python scripts/generate_active_projects_doc.py
```

**Coverage history** — refreshed automatically by the `performance` job on `main` (informational, never blocks). Locally:

```bash
# Offline: parse a directory of coverage-*.xml files
uv run python scripts/generate_coverage_history.py --from-dir=./_artefacts --days=30

# Online: pull last N days of CI artefacts via the GitHub CLI (needs `gh auth login`)
uv run python scripts/generate_coverage_history.py --from-gh --days=30
```

**Canonical factsheet** — when CI gates, project counts, or fep_lean scale change, re-run the measurements cited in [`canonical_facts.md`](canonical_facts.md) (discovery tests, `projects/fep_lean` `pytest --collect-only`, optional full `pytest` with coverage) and edit that file so numbers stay ground-truthed.
