# scripts/docgen/

Derived documentation generator scripts (stub directory).

The generators currently live at the `scripts/` root level:
- `generate_active_projects_doc.py`
- `generate_api_reference_doc.py`
- `generate_architecture_overview.py`
- `generate_counts.py`
- `generate_coverage_history.py`
- `generate_stage_table_doc.py`
- `generate_exemplar_roster_doc.py`
- `generate_publication_records_doc.py`

## Usage

```bash
# Run from repo root
uv run python scripts/generate_stage_table_doc.py
uv run python scripts/generate_api_reference_doc.py --check
```

Output goes to `docs/_generated/`.
