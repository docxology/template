# roadmap_tracks/ - Promotion Artifact Builders

## Purpose

This package builds deterministic artifacts for candidate Active Inference
roadmap tracks. It is not a place for live empirical claims, network calls,
private data, or nondeterministic research behavior.

## Local Rules

- Keep business logic in importable functions; project scripts should only
  orchestrate reads, writes, and CLI reporting.
- Treat every new artifact as future-only until the promotion rule in
  [`../../TODO.md`](../../TODO.md) is satisfied; after promotion, keep the
  producer, manuscript binding, typed claim, semantic restriction, gate, and
  negative-control rows in sync.
- Pair every promoted artifact with a validation function and a negative-control
  test that proves stale, missing, or unsupported evidence fails.
- Write JSON deterministically with stable keys and fixed finite grids.
- Do not make the gate cache or generated roadmap artifacts a manuscript claim
  unless the corresponding sheaf track, manuscript binding, and validation gate
  are live.

## Modules

- `toy_sweep.py` - facade over the split modules below: keeps
  `write_toy_sweep_artifacts` / `validate_toy_sweep_artifacts` and re-exports the
  builders, helpers, and schema constants so existing
  `from roadmap_tracks.toy_sweep import ...` imports stay stable.
- `toy_sweep_types.py` - schema constants and tolerances (`TOY_SWEEP_SCHEMA`,
  `ASSUMPTION_INDEX_SCHEMA`, `EXPECTED_ASSUMPTION_EQUATIONS`,
  `OBSERVABLE_RESIDUAL_TOLERANCE`).
- `toy_sweep_helpers.py` - closed-form observable helpers
  (`_same_state_probability`, `_posterior_correlation`, `_joint_entropy`,
  `_marginal_entropy`) over `analytical.bernoulli_toy`.
- `toy_sweep_builders.py` - deterministic `build_*` builders
  (`build_analytical_observable_sweep` through `build_causal_ablation_matrix`)
  for finite toy sweeps, uncertainty summaries, benchmark matrices, policy grids,
  graph-world topology sweeps/traces/invariants, state-space catalogs, and
  causal-ablation matrices; reads JSON via `from json_io import load_json`.
- `formal_interop.py` - GNN, ontology, Lean, model-checking, and interop
  witness artifacts plus proof extraction.
- `integration_audit.py` - validation dependency graph, producer completeness,
  stale-artifact, claim-evidence, token-provenance, artifact diffoscope,
  artifact-license, release-note, and scope-boundary audits.
- `visualization_audit.py` - registry-backed figure quality report joining
  rendered image dimensions, RGB mode, hashes, source mappings, statistical
  figure-source bridges, explicit scholarship/sheaf crosswalk rows, and
  alt/caption metadata.
- `visualization_contract.py` - typography-token minima, raw font-size literal
  scanning, and auxiliary visual-output classification used by the visualization
  quality audit.
- `scholarship.py` - source matrix builder and validator that rederives saved
  bibliography rows from live references, manuscript citation sections, sheaf
  tracks, manifest sections, scope-boundary text, and evidence artifact paths.
- `security.py` - source/config secret scanner and security posture validator
  that separates enforced local release controls from scoped production-only
  security obligations.
- `sheaf_tracks.py` - canonical provenance, replay matrix, sensitivity,
  uncertainty, counterexample, model-checking, interop, adversarial-audit,
  evidence-field, release-bundle, theorem-traceability, gate-index, artifact
  diffoscope, proof-extraction, state-space, causal-ablation, artifact-license,
  release-note, security-posture, artifact-contract, semantic, dependency,
  track-improvement, and blocked-scope artifacts.
- `supplemental.py` - promoted supplemental proof-dependency, state-transition,
  ablation-sensitivity, and release-attestation artifacts plus their validators.

## Verification

Run focused project tests after touching this package:

```bash
uv run pytest tests/test_track_consolidation.py tests/test_roadmap_promotion.py -q --no-cov
```
