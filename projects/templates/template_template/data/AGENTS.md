# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## `claim_ledger.yaml`

Evidence registry for manuscript claims that are intentionally sourced from
canonical code/configuration or cited literature rather than live repository
introspection.

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

1. Never copy live repository counts into the ledger; expose them as generated
   manuscript metrics.
2. When a policy constant changes, update its canonical executable source first;
   tests require the ledger and generated token to match that source.
3. For external empirical values, identify the cited primary source precisely.
4. Re-run manuscript evidence validation after ledger edits.
5. Do not store generated metrics JSON or manuscript output under `data/`.

Quick orientation: [`README.md`](README.md).
