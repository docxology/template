# template_active_inference TODO

This backlog is future-only. It is not the current artifact contract and does
not create publication claims. Current claims remain deterministic,
locally reproducible, public, and toy-only. Completed work belongs in generated
artifacts, README/AGENTS files, tests, manuscript fragments, and sheaf
registries rather than in this file.

## Current verification evidence

In this 2026-06-09 audit, `uv run pytest tests/ --cov=src --cov-fail-under=90` passed 361 tests with 90.59% coverage. Replace this paragraph only after rerunning that exact command and updating the result from the fresh output.

## Promotion rule

A future capability becomes live only after it has a configured producer,
deterministic artifact, manuscript consumer, typed claim evidence, semantic
restriction, validation gate, and failing negative control. Prefer deepening
stable canonical tracks over adding versioned `_vN` siblings.

| Requirement | Minimum proof before promotion |
| --- | --- |
| Producer | Configured script or renderer in the analysis DAG |
| Artifact | Deterministic file under `output/data/`, `output/reports/`, or `output/figures/` |
| Manuscript consumer | Bound IMRAD fragment or generated evidence table |
| Typed claim evidence | Claim-ledger predicate with explicit field, expected value, tolerance, or list predicate |
| Semantic restriction | Certificate field that catches disagreement, missing evidence, or stale output |
| Validation gate | `validate_outputs`, `validate_manuscript`, `lake build`, or project test |
| Negative control | Test that mutates artifact/config/claim text and proves the gate fails |

## Unblocked backlog

No unblocked future rows remain after the 2026-06-09 hardening pass. Add new
future work here only after it has a size, proof artifact, gate/predicate, and
negative control that fit the promotion rule above.

## Blocked major scope

These areas remain out of scope until a later plan supplies provenance,
licensing/privacy review, typed claim evidence, semantic restrictions, gates,
and negative controls. They are not ready for `AI-*` promotion IDs.

| Blocked area | Why blocked | Required unblock artifact | Required gate/predicate | Negative control |
| --- | --- | --- | --- | --- |
| Empirical adapter | Current artifacts are deterministic toy models, not biological or real-world data | `output/data/empirical_adapter_manifest.json` | scope-boundary and claim-ledger gates | Empirical result prose without manifest fails |
| Private or restricted data | This exemplar is public and self-contained | `output/reports/data_provenance_audit.json` | provenance and license validator | Private path or unlicensed source passes |
| Network-dependent research | Pipeline must remain locally reproducible | `output/reports/offline_reproducibility_audit.json` | offline pipeline gate | Network call required for core pipeline |
| LLM-generated evidence | Claims must come from generated local artifacts, not opaque model output | `output/reports/evidence_source_audit.json` | evidence registry and claim-ledger gates | LLM-only claim passes evidence audit |
| Non-toy model claims | Current validation covers finite pedagogical examples only | `output/reports/model_scope_audit.json` | scope-boundary validator | Non-toy generalization appears in results |
