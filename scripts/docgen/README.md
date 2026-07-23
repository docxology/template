# scripts/docgen/

Derived documentation generator scripts.

## Scripts

| Script | Output |
|--------|--------|
| `active_projects.py` | `docs/_generated/active_projects.md` |
| `api_reference.py` | `docs/reference/api-reference.md` (CI `--check`) |
| `architecture_overview.py` | `docs/_generated/architecture_overview.mmd` / `.svg` |
| `counts.py` | `docs/_generated/COUNTS.md` |
| `coverage_history.py` | `docs/_generated/coverage_history.md` |
| `stage_table.py` | Stage table marker block in `scripts/AGENTS.md` |
| `exemplar_roster.py` | `docs/_generated/exemplar_roster.md` + `template_manifest.json` |
| `publication_records.py` | `docs/_generated/publication_records.md` + GitHub README block + per-exemplar `STANDALONE.md` |

## Usage

```bash
# Run from repo root
uv run python scripts/docgen/counts.py --write
uv run python scripts/docgen/api_reference.py --check
uv run python scripts/docgen/exemplar_roster.py
uv run python scripts/docgen/publication_records.py --refresh-external
```

Output goes to `docs/_generated/`.
