# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## `claim_ledger.yaml`

Evidence-registry for manuscript claims that are intentionally sourced from code,
examples, or generated reports rather than `{{VARIABLE}}` injection.

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

1. Edit only when manuscript claims, code constants, or source-backed numeric
   facts change (dead-end thresholds, confirmation seeds, team counts, etc.).
2. Re-run the ablation suite and evidence validation after ledger edits.
3. Do not store generated CSV/JSON/PNG under `data/`.

Quick orientation: [`README.md`](README.md).
