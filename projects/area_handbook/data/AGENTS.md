# data/

## Fixture schema

Root mapping:

- `area_id`, `area_label`, `version` (non-empty strings)
- `themes`: non-empty list of `{ id, label, description }`
- `evidence`: list of `{ id, statement, theme, weight, source_label, reviewed_at }`

Rules enforced in `src/corpus_io.py`:

- `theme` on each evidence row must match a theme `id`
- `weight` in `[0, 1]`, finite (no NaN or infinity)
- `id` fields non-empty after strip; **no duplicate** theme or evidence ids
- theme `label` / `description` and evidence `statement` / `source_label` / `reviewed_at` non-blank
