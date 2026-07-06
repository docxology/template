# scripts/docgen/ — Derived Documentation Generators

## Purpose

This subdirectory (currently a stub) is the planned home for documentation
generation scripts that write to `docs/_generated/` and update in-place doc
blocks.  The scripts currently live at the root of `scripts/` but are candidates
for migration here.

## Planned scripts (currently at scripts/ root)

| Script | Purpose |
|--------|---------|
| `generate_active_projects_doc.py` | Derived active-project inventory |
| `generate_api_reference_doc.py` | API reference from `__all__` (CI `validate --check`) |
| `generate_architecture_overview.py` | Architecture `.mmd`/`.svg` from live state |
| `generate_coverage_history.py` | Coverage-history page from CI artefacts |
| `generate_counts.py` | Line/module count stats |
| `generate_stage_table_doc.py` | Canonical pipeline stage table (marker block) |
| `generate_exemplar_roster_doc.py` | Public exemplar roster doc |
| `generate_publication_records_doc.py` | Publication-records doc |

## Usage (from scripts/ root)

```bash
uv run python scripts/generate_stage_table_doc.py
uv run python scripts/generate_api_reference_doc.py --check
uv run python scripts/generate_active_projects_doc.py
```

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`docs/_generated/`](../../docs/_generated/) — generated output directory
