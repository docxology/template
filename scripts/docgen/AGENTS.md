# scripts/docgen/ — Derived Documentation Generators

## Purpose

Thin orchestrators that write to `docs/_generated/` and refresh in-place doc
marker blocks. Each script delegates to `infrastructure.documentation.*` or
related modules.

## Scripts

| Script | Purpose |
|--------|---------|
| `active_projects.py` | Derived active-project inventory |
| `api_reference.py` | API reference from `__all__` (CI `validate --check`) |
| `architecture_overview.py` | Architecture `.mmd`/`.svg` from live state |
| `coverage_history.py` | Coverage-history page from CI artefacts |
| `counts.py` | Line/module count stats (`docs/_generated/COUNTS.md`) |
| `stage_table.py` | Canonical pipeline stage table (marker block) |
| `exemplar_roster.py` | Public exemplar roster doc |
| `publication_records.py` | Publication-records doc, GitHub README table, and per-exemplar `STANDALONE.md` identity blocks |

## Bootstrap pattern

Each script uses `parents[2]` to reach the repo root from `scripts/docgen/`:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path
ensure_repo_root_on_path()
```

## Usage

```bash
uv run python scripts/docgen/stage_table.py
uv run python scripts/docgen/api_reference.py --check
uv run python scripts/docgen/active_projects.py
uv run python scripts/docgen/counts.py --write
uv run python scripts/docgen/publication_records.py --check
```

Root-level `scripts/generate_*.py` filenames remain as backward-compatible shims
where present; prefer the paths above in docs and CI.

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`docs/_generated/`](../../docs/_generated/) — generated output directory
