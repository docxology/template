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

- `toy_sweep.py` - finite toy sweeps, uncertainty summaries, benchmark matrices,
  policy grids, graph-world invariants, state-space catalogs, causal-ablation
  matrices, and deterministic figure/hash reports.
- `formal_interop.py` - GNN, ontology, Lean, model-checking, and interop
  witness artifacts plus proof extraction.
- `integration_audit.py` - validation dependency graph, producer completeness,
  stale-artifact, claim-evidence, token-provenance, artifact diffoscope,
  artifact-license, release-note, and scope-boundary audits.
- `visualization_audit.py` - registry-backed figure quality report joining
  rendered image dimensions, RGB mode, hashes, source mappings, statistical
  figure-source bridges, explicit scholarship/sheaf crosswalk rows, and
  alt/caption metadata.
- `scholarship.py` - source matrix builder and validator that rederives saved
  bibliography rows from live references, manuscript citation sections, sheaf
  tracks, manifest sections, scope-boundary text, and evidence artifact paths.
- `sheaf_tracks.py` - canonical provenance, replay matrix, sensitivity,
  uncertainty, counterexample, model-checking, interop, adversarial-audit,
  evidence-field, release-bundle, theorem-traceability, gate-index, artifact
  diffoscope, proof-extraction, state-space, causal-ablation, artifact-license,
  release-note, semantic, dependency, track-improvement, and blocked-scope
  artifacts.
- `supplemental.py` - promoted supplemental proof-dependency, state-transition,
  ablation-sensitivity, and release-attestation artifacts plus their validators.

## Verification

Run focused project tests after touching this package:

```bash
uv run pytest tests/test_track_consolidation.py tests/test_roadmap_promotion.py -q --no-cov
```
