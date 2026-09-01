# Manuscript Notes

Author-facing manuscript surface. Most numbered files are composed or hydrated
from sheaf fragments, generated variables, and source registries.

## Edit Boundaries

| Surface | Rule |
| --- | --- |
| `sections/imrad/` | Edit prose fragments here. See `sections/imrad/AGENTS.md`. |
| `sheaf/manifest.yaml` | Bind tracks to IMRAD sections. See `sheaf/AGENTS.md`. |
| `sheaf/tracks.yaml` | Register live fragment tracks and generated renderers. |
| `00_abstract.md`, `17_conclusion.md`, `99_references.md` | Manual files outside the main sheaf matrix. |
| `00_00_sheaf_coverage.md` | Regenerated coverage page; do not hand-edit. |
| Numbered IMRAD files | Composed outputs unless explicitly listed as manual above. |
| `config.yaml` | Publication metadata plus `sheaf:` settings. |

## Contracts

- Run-derived numbers are hydrated from `output/data/manuscript_variables.json`;
  never freeze fresh counts in prose.
- Compose emits `{{token}}` placeholders; hydration is the single substitution
  boundary and should fail closed on unknown or malformed tokens.
- Figure captions, alt text, and section bindings come from `../figures.yaml`.
- Keep publication claims scoped to deterministic toy artifacts unless new
  measured outputs are generated, copied, and validated.

## Commands

```bash
uv run python ../scripts/compose_manuscript.py
uv run python ../scripts/compose_manuscript.py --validate-only --strict
uv run python ../scripts/z_generate_manuscript_variables.py
uv run pytest ../tests/test_manuscript_hydrate.py ../tests/test_typography_contract.py ../tests/test_sheaf_compose.py
```
