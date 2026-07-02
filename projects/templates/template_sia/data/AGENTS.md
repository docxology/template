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

1. Edit only when manuscript claims, SIA config defaults, or fixture counts change.
2. Re-run the SIA loop and validation after ledger edits.
3. Do not store generated reports or figures under `data/`.

Quick orientation: [`README.md`](README.md).
