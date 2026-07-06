# Documentation Package

## Purpose

Documentation code generates and maintains live repo documentation surfaces:
figures, API references, architecture diagrams, active-project rosters,
publication matrices, and measured count facts. It should derive facts from the
tree instead of copying volatile literals into prose.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Figures and manuscript helpers | `figure_manager.py`, `image_manager.py`, `markdown_integration.py` | Figure registry, insertion, table-of-figures, cross-reference helpers. |
| API docs | `api_reference_gen.py`, `glossary_gen.py` | AST-derived public API docs and marker injection. |
| Pipeline docs | `stage_table.py` | Stage table rendered from `core/pipeline/pipeline.yaml`. |
| Generated facts | `counts_doc.py`, `active_projects_doc.py`, `architecture_overview.py` | `docs/_generated/COUNTS.md`, active projects, architecture diagram. |
| Publication docs | `publication_records.py` | DOI/archive/config/GitHub publication matrix. |

## Boundaries

- Generators own generated blocks between explicit markers; hand-authored prose
  outside markers must be preserved.
- Do not import project code when AST parsing is sufficient. API reference
  generation must stay safe on incomplete optional dependencies.
- Counts and rosters are source-owned by generators; do not hand-edit generated
  facts.
- Publication records may refresh external state only when the command or user
  explicitly requests it.

## Public Commands

```bash
uv run python scripts/docgen/counts.py --check
uv run python scripts/docgen/counts.py --write
uv run python scripts/docgen/active_projects.py
uv run python scripts/docgen/api_reference.py --check
uv run python scripts/docgen/architecture_overview.py
uv run python scripts/docgen/publication_records.py
```

## Tests

```bash
uv run pytest tests/infra_tests/documentation -q
uv run pytest tests/infra_tests/test_check_template_drift.py -q
```

Run `uv run python scripts/audit/check_template_drift.py --strict` after changing any
long-lived docs, generated-doc producers, or hardcoded-count policy.

## Change Checklist

- If a doc claim is numeric or roster-shaped, add it to `COUNTS.md` generation or
  link `docs/_generated/active_projects.md`.
- Keep marker-based injectors idempotent.
- Do not cite local navigation indexes such as `.codegraph/` or `.leann/` as
  evidence.

## See Also

- [`README.md`](README.md)
- [`../skills/AGENTS.md`](../skills/AGENTS.md)
- [`../../docs/_generated/AGENTS.md`](../../docs/_generated/AGENTS.md)
