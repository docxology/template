# template_autoscientists TODO

Forward-only integrity backlog for the coordination-mechanism testbed exemplar.
Keep completed work out of this file once the proof artifacts and tests exist.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_autoscientists/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_autoscientists/tests/ --cov=projects/templates/template_autoscientists/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: figure registry passes after generated `output/figures/figure_registry.json`; evidence registry still reports 10 unsupported numeric tokens; artifact manifest remains advisory-drifted after single-stage regeneration.
- Live Hermes path stays opt-in through the `requires_ollama` test marker and is not part of the default render gate.

## Integrity and template-status gaps

- Keep the deterministic proposer, dead-end registry, confirmation band, and reorganization logic as the default gated path.
- Add a small generated readiness report that distinguishes deterministic fixture evidence from live language-model behavior.
- Preserve the no-mocks policy by adding any new coordination seam as a real deterministic test double or fixture object.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the shipped experiment mirror when code defaults change.
- Add a script-level config summary artifact if the analysis scripts begin reading YAML directly instead of constructing defaults in code.

## Documentation and signposting gaps

- Link every new analysis artifact from README, AGENTS, and the manuscript method section before treating it as a public template surface.
- Add a short fork checklist for replacing `DeterministicProposer` with a real proposer while retaining matched-budget controls.

## Test and validator gaps

- Add a negative control that fails when the experiment mirror diverges from `SearchConfig` or `SyntheticObjective` defaults.
- Add a validator for stale live-Hermes transcripts if live transcript fixtures are ever checked in.
- Register the remaining numeric claims in the evidence registry or rewrite them as clearly illustrative constants before treating Stage 04 as warning-free.
- Add a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks, or document that only full `PipelineExecutor` runs are manifest-authoritative.

## Ordered improvement ladder

1. Keep deterministic fixture replay green under project coverage.
2. Add readiness/report artifacts for deterministic versus live boundaries.
3. Add config-driven orchestration only after tests prove parity with current code defaults.
4. Promote any live agent path only with offline transcript fixtures, stale-transcript detection, and no-network default validation.
