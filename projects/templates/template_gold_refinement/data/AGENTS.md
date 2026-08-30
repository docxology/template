# AGENTS.md — template_gold_refinement/data

Static data assets consumed by `src/integrity.py`.

## Files

| File | Purpose |
| --- | --- |
| `claim_ledger.yaml` | Claim registry keyed by refinery stage and purity target. Each claim must appear in the manuscript before the gate passes. |

## Agent Rules

- Do not add computed or generated artefacts here; `data/` is source-only.
- Claim keys must be stable across runs — ledger mutation breaks the integrity gate (negative control: renaming or removing an expected claim key is asserted to fail the integrity check in the project test suite rather than pass silently). Negative control: deliberately altering a recorded assay value makes the next validation run exit non-zero until the mutation is reverted.
Mutating a stable key is the deliberately-wrong input the integrity gate rejects out of hand; regenerate from source instead of editing.
