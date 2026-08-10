# Generated documentation snippets

This directory mixes **script-generated files** with two **maintainer-written** hub files (`README.md`, `AGENTS.md`) and one retained historical snapshot (`hermes_knowledge_audit.json`, no longer produced by any generator). Every other file listed below is generator output — do not edit it by hand; regenerate it with the command in its row.

| File | Source |
|------|--------|
| [active_projects.md](active_projects.md) | **Generated** — `uv run python scripts/docgen/active_projects.py` |
| [architecture_overview.md](architecture_overview.md) / [architecture_overview.svg](architecture_overview.svg) / `.mmd` | **Generated** — `uv run python scripts/docgen/architecture_overview.py` |
| [coverage_history.md](coverage_history.md) | **Generated** — `uv run python scripts/docgen/coverage_history.py --from-dir=<dir>` (offline) or `--from-gh --days=30` (online, needs `gh`) |
| [coverage_snapshot.json](coverage_snapshot.json) | **Generated** — `uv run python scripts/docgen/counts.py --refresh-coverage-provenance --write`; versioned source-commit/source-tree/source-hash provenance for the COUNTS.md coverage table, validated fail-closed |
| [status_evidence.json](status_evidence.json) | **Generated** — `uv run python scripts/docgen/status_evidence.py --write`; source-bound typed evidence for the STATUS.md ledger |
| [COUNTS.md](COUNTS.md) | **Generated** — `uv run python scripts/docgen/counts.py` (`--check` in CI, `--write` to refresh); measured infra counts, pytest collection totals, package roster |
| [exemplar_roster.md](exemplar_roster.md) | **Generated** — `uv run python scripts/docgen/exemplar_roster.py` (`--check` in CI and pre-commit) |
| [hermes_knowledge_audit.json](hermes_knowledge_audit.json) | **Historical snapshot** — legacy external audit metadata; superseded by current generated facts |
| [publication_records.md](publication_records.md) | **Generated publication matrix** — public exemplar GitHub/Zenodo/config records; refresh with `scripts/docgen/publication_records.py --refresh-external` |
| [skills_index.md](skills_index.md) | **Generated** — `uv run python -m infrastructure.skills write-index` |
| [last-run-summary.md](last-run-summary.md) | **Generated** — auto-written by `infrastructure.core.pipeline.multi_project` on every `./run.sh --pipeline` invocation (best-effort). Schema: [`../operational/logging/output-design.md`](../operational/logging/output-design.md) |
| `README.md`, `AGENTS.md` | **Maintainer** — policy and conventions for linking to generated content |

## Policy

- **Public canonical templates are generated scope.** Their tracked roster is
  [active_projects.md](active_projects.md); private lifecycle mirrors may appear
  or disappear locally. Use `projects/templates/template_code_project/` as the
  default control-positive walkthrough, not as a second roster definition.
- **[active_projects.md](active_projects.md)** lists the public CI/documentation project scope **at generation time**. Runtime `discover_projects()` may include local-only private symlinks; do not duplicate that local roster in RUN_GUIDE, PAI, security tables, or similar.
- For walkthroughs, commands, and “see also” paths, use **`projects/templates/template_code_project/`** as the control-positive exemplar unless the doc’s purpose is to compare layouts.
- Describe other work as folder patterns (`projects/active/{name}/`, `projects/working/{name}/`, `projects/archive/{name}/`) rather than enumerating sibling projects in prose as if permanent.

## Regeneration

**Public active projects** — after changing tracked template project directories under `projects/`:

```bash
uv run python scripts/docgen/active_projects.py
```

**Coverage history** — refreshed automatically by the `performance` job on `main` (informational, never blocks). Locally:

```bash
# Offline: parse a directory of coverage-*.xml files
uv run python scripts/docgen/coverage_history.py --from-dir=./_artefacts --days=30

# Online: pull last N days of CI artefacts via the GitHub CLI (needs `gh auth login`)
uv run python scripts/docgen/coverage_history.py --from-gh --days=30
```

**Canonical factsheet** — regenerate with `uv run python scripts/docgen/counts.py --write`; never hand-edit [`COUNTS.md`](COUNTS.md) (CI and pre-commit run `counts.py --check`). After changing an exemplar `src/` or its tests, rerun that project's coverage gate and then `uv run python scripts/docgen/counts.py --refresh-coverage-provenance --write`; ordinary `--write` fails closed when source hashes no longer match.

**Status evidence** — after changing a row in [`../../STATUS.md`](../../STATUS.md), run `uv run python scripts/docgen/status_evidence.py --write`; CI/checks use `uv run python scripts/docgen/status_evidence.py --check` to reject stale receipts.

**Publication records matrix** — when citing repository/DOI publication status, re-run `uv run python scripts/docgen/publication_records.py --refresh-external`; do not hand-edit [`publication_records.md`](publication_records.md).

**Skills index** — after adding/removing `SKILL.md` descriptors:

```bash
uv run python -m infrastructure.skills write-index
```
