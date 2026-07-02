# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## `claim_ledger.yaml`

Evidence-registry for manuscript claims that are intentionally sourced from code
constants, config defaults, or generated reports rather than `{{VARIABLE}}` injection.

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

1. Edit only when textbook config defaults, constant whitelists, or structural
   contract values change — not when chapter stubs are filled.
2. Re-run the scaffold and manuscript integrity tests after ledger edits.
3. Do not store generated chapter content or figures under `data/`.

Quick orientation: [`README.md`](README.md).
