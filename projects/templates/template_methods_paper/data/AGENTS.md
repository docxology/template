# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

This exemplar has no external dataset: its "input" is the controlled
vocabulary declared in code (`src/methods_dsl/vocabulary.py`,
`src/methods_dsl/units.py`), not a CSV fixture. `data/` therefore holds only
the claim ledger, matching `template_code_project`'s convention for exemplars
without a dataset.

## `claim_ledger.yaml`

Evidence-registry for manuscript claims that are intentionally sourced from
code, the dataset, or generated reports rather than `{{VARIABLE}}` injection.

### Schema (preserve when adding rows)

| Field | Purpose |
| --- | --- |
| `claim_id` | Stable identifier |
| `kind` | Claim category |
| `value` | Declared numeric or textual value |
| `source` | Provenance (module, manuscript section, artifact) |
| `source_tier` | Trust tier for validation |
| `freshness` | Staleness policy |
| `artifact_path` | Optional path to backing file |

## Edit protocol

1. Edit `claim_ledger.yaml` only when manuscript claims, figure defaults, or
   source-backed numeric facts change.
2. Re-run evidence validation / pipeline stages that consume the ledger.
3. Do not store generated CSV/JSON/PNG under `data/` — those go to `output/`.

Quick orientation: [`README.md`](README.md).
