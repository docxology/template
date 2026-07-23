# template_autoscientists TODO

Forward-only backlog for the deterministic coordination-mechanism testbed
exemplar (arXiv:2605.28655 primitives: proposer, dead-end registry,
confirmation band, reorganization).

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_autoscientists/manuscript --repo-root .`
- Project tests and coverage (read live counts from
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) and the gate
  output, not a pinned number here):
  `uv run pytest projects/templates/template_autoscientists/tests/ --cov=projects/templates/template_autoscientists/src --cov-fail-under=90`
- Repo drift gate:
  `uv run python scripts/audit/check_template_drift.py --strict`
- Stage-04 output validation (figure registry, evidence registry, artifact manifest):
  `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_autoscientists`
- The live Hermes path stays opt-in through the `requires_ollama` test marker
  (skipped at runtime in `test_hermes_live.py`) and is not part of the default
  render gate.

## Integrity and template-status gaps

- Keep the deterministic proposer, dead-end registry, confirmation band, and
  reorganization logic as the default gated path.
- Add a small generated readiness report that distinguishes deterministic
  fixture evidence from live language-model behavior.
- Preserve the no-mocks policy by adding any new coordination seam as a real
  deterministic test double or fixture object.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the shipped experiment
  mirror when code defaults (`SearchConfig`, `SyntheticObjective`) change.
- Add a script-level config summary artifact if the analysis scripts begin
  reading YAML directly instead of constructing defaults in code.

## Documentation and signposting gaps

- Link every new analysis artifact from README, AGENTS, and the manuscript
  method section before treating it as a public template surface.
- Add a short fork checklist for replacing `DeterministicProposer` with a real
  proposer while retaining matched-budget controls.

## Test and validator gaps

- Register the remaining unsupported numeric claims in the evidence registry or
  rewrite them as clearly illustrative constants before treating Stage 04 as
  warning-free.
- Add a stable final artifact-manifest refresh path for single-stage
  analysis/render/copy checks, or document that only full `PipelineExecutor`
  runs are manifest-authoritative. **Documented:**
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  provides the stable refresh path for single-stage runs; full
  `PipelineExecutor` runs remain the only source of per-stage provenance.
- Add a validator for stale live-Hermes transcripts if live transcript fixtures
  are ever checked in.
- **Shipped:** the shared evidence registry now fails validation when a
  claim-ledger `artifact_path` escapes the project or no longer resolves on
  disk; the stale ablation artifact reference was corrected and covered by
  infrastructure-level negative controls.

## Ordered improvement ladder

1. Keep deterministic fixture replay green under the project coverage gate.
2. Add readiness/report artifacts for the deterministic-versus-live boundary.
3. Add config-driven orchestration only after tests prove parity with current
   code defaults.
4. Promote any live agent path only with offline transcript fixtures,
   stale-transcript detection, and a no-network default validation.
