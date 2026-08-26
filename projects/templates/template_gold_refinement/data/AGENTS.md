# AGENTS.md — template_gold_refinement/data

Static data assets consumed by `src/integrity.py`.

## Files

| File | Purpose |
| --- | --- |
| `claim_ledger.yaml` | Claim registry keyed by refinery stage and purity target. Each claim must appear in the manuscript before the gate passes. |

## Agent Rules

- Do not add computed or generated artefacts here; `data/` is source-only.
- Claim keys must be stable across runs — ledger mutation breaks the integrity gate.
Mutating a stable key is the deliberately-wrong input the integrity gate rejects out of hand; regenerate from source instead of editing.
