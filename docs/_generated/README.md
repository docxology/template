# Generated documentation snippets

This directory mixes **one script-generated file** with **maintainer-written** hub files (`README.md`, `AGENTS.md`).

| File | Source |
|------|--------|
| [active_projects.md](active_projects.md) | **Generated** — `uv run python scripts/generate_active_projects_doc.py` |
| [architecture_overview.svg](architecture_overview.svg) / `.mmd` | **Generated** — `uv run python scripts/generate_architecture_overview.py` |
| [coverage_history.md](coverage_history.md) | **Generated** — `uv run python scripts/generate_coverage_history.py --from-dir=<dir>` (offline) or `--from-gh --days=30` (online, needs `gh`) |
| [COUNTS.md](COUNTS.md) | **Maintained** — ground-truthed test counts, gates, and roster notes (refresh with measured `pytest` + `generate_active_projects_doc.py`; see file footer) |
| [hermes_knowledge_audit.json](hermes_knowledge_audit.json) | **Historical snapshot** — legacy external audit metadata; superseded by current generated facts |
| [publication_records.md](publication_records.md) | **Generated publication matrix** — public exemplar GitHub/Zenodo/config records; refresh with `scripts/generate_publication_records_doc.py --refresh-external` |
| [skills_index.md](skills_index.md) | **Generated** — `uv run python -m infrastructure.skills write-index` |
| [last-run-summary.md](last-run-summary.md) | **Generated** — auto-written by `infrastructure.core.pipeline.multi_project` on every `./run.sh --pipeline` invocation (best-effort). Schema: [`../operational/logging/output-design.md`](../operational/logging/output-design.md) |
| `README.md`, `AGENTS.md` | **Maintainer** — policy and conventions for linking to generated content |

## Policy

- **`projects/` is a rotating set** of workspaces. The only path **guaranteed** as the long-term control-positive layout is **`projects/templates/template_code_project/`**. Everything else appears or disappears as maintainers promote or move projects.
- **[active_projects.md](active_projects.md)** lists the public CI/documentation project scope **at generation time**. Runtime `discover_projects()` may include local-only private symlinks; do not duplicate that local roster in RUN_GUIDE, PAI, security tables, or similar.
- For walkthroughs, commands, and “see also” paths, use **`projects/templates/template_code_project/`** as the control-positive exemplar unless the doc’s purpose is to compare layouts.
- Describe other work as folder patterns (`projects/active/{name}/`, `projects/working/{name}/`, `projects/archive/{name}/`) rather than enumerating sibling projects in prose as if permanent.

## Regeneration

**Public active projects** — after changing tracked template project directories under `projects/`:

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

**Canonical factsheet** — when CI gates, project counts, publishing tests, or public exemplar coverage changes, re-run the measurements cited in [`COUNTS.md`](COUNTS.md) and edit that file so numbers stay ground-truthed.

**Publication records matrix** — when citing repository/DOI publication status, re-run `uv run python scripts/generate_publication_records_doc.py --refresh-external`; do not hand-edit [`publication_records.md`](publication_records.md).

**Skills index** — after adding/removing `SKILL.md` descriptors:

```bash
uv run python -m infrastructure.skills write-index
```
