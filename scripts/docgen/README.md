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
uv run python scripts/docgen/counts.py --verify-coverage --write \
  --coverage-snapshot-output /owned/retained/counts_coverage.snapshot.data
uv run python scripts/docgen/api_reference.py --check
uv run python scripts/docgen/exemplar_roster.py
uv run python scripts/docgen/publication_records.py --refresh-external
```

Prepare the nominated DATA file by independently copying the selected SDK's
`counts_coverage.py` byte-for-byte outside both the repository and SDK. Retain
its original bytes before measurement. `--verify-coverage --write` refuses
without `--coverage-snapshot-output`; every exemplar must measure successfully
before the existing literal writer changes that DATA copy. The repository,
selected SDK, and wheel remain unchanged. After original terminal custody
closes, the owner reviews/applies the literal delta as a new source epoch,
rebuilds the SDK, and refreshes coverage provenance. Partial measurement never
publishes a DATA refresh.

Output goes to `docs/_generated/`.
