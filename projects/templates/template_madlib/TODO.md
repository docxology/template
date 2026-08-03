# template_madlib TODO

Forward-only integrity backlog for the deterministic token-injection manuscript
exemplar. This tree is part of the public template roster and must satisfy the
same forkability contract as the older exemplars.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_madlib/manuscript --repo-root .`
- Project tests and coverage: 181 passed, 99.22% coverage (required floor: 90%).
- Generated artifacts come from `scripts/01_generate_madlib_artifacts.py` and `scripts/z_generate_manuscript_variables.py`.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_madlib --strict` — no drift detected.
- Project-local output validator: `scripts/02_validate_outputs.py` → `src.output_validator.validate_generated_outputs`, declared third analysis script; writes `output/reports/output_validation.json`.
- Live test counts and coverage are read from
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned
  here; keep every `src/` module (config, composition, tokens, analysis,
  artifact_writers, manuscript_variables) branch-covered under the 90% gate.

## Integrity and template-status gaps

- Fixed in this pass: corrected publication-boundary prose that falsely claimed deposited DOIs were blank, synchronized version markers to `0.1.1`, added the missing `.agents/` catalog READMEs, created `docs/README.md` and `data/README.md`, and documented `00_preflight.py` in `scripts/AGENTS.md`.
- Fixed in this pass: added the project-local output validator (`src/output_validator.py`) with declared-artifact stale guard wired into `analysis.scripts`; corrected Evaluation readiness prose and cover figure text that still enumerated a live DOI/external release as absent; replaced stale `tokens.py` docstring examples.

- Keep the lexicon, conditional section plan, token provenance, and authoring contract as generated evidence, not prose-only claims.
- Keep digest invariants, claim-ledger alignment, review-packet assembly, and fork-migration obligations config-owned and test-covered.
- Split any oversized source module before adding new visualization or report builders.
- Preserve public imports for artifact generation and figure writers when refactoring internals.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` placeholder-safe while retaining every required schema block a fork needs.
- Add schema-level validation before adding new optional madlib sections or generated figures.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript Methods aligned on the same source-owned generation contract.
- Keep fork guidance explicit: replacing toy lexicon categories with domain lexicons also requires config rows, source changes where behavior changes, validators, tests, Stage 04/05 review-packet checks, claim-ledger evidence, and conservative metadata.
- Keep review-packet guidance explicit that PDF/HTML alone are not enough; data, reports, figures, validation results, and copy statistics travel with the manuscript.

## Test and validator gaps

- ~~Add a project-local output validator if Stage 04 cannot catch token provenance, figure registry, and authoring-contract regressions together.~~ ✓ Implemented as `src/output_validator.py` + `scripts/02_validate_outputs.py`, wired into `manuscript/config.yaml` `analysis.scripts`; covered by `tests/test_output_validator.py`.
- ~~Add a stale-artifact check if generated artifact names or report schemas grow beyond the current fixture coverage.~~ ✓ The validator's declared inventory (`DECLARED_FIGURE_FILES`, `PROJECT_OWNED_DATA_FILES`, `PROJECT_OWNED_REPORT_FILES`) fails on undeclared or missing project-owned artifacts.
- Preserve review-packet assertions if future copied-output layout changes make output statistics, validation reports, or copied data/report/figure categories optional.
- Consider adding hypothesis-based property tests for the SHA-256 digest invariant if the lexicon format changes (current determinism is verified with parametric seed/lexicon tests).

## Ordered improvement ladder

1. Keep release metadata, module size, tests, and drift gates green as the published canonical exemplar evolves.
2. ~~Add negative controls for unresolved placeholders and missing token provenance.~~ ✓ Covered in `test_config.py` and `test_tokens.py`.
3. ~~Add negative controls for digest-invariant drift and missing review-packet artifacts.~~ ✓ Covered in `test_tokens.py` and `test_composition_and_analysis.py`.
4. Add schema migrations only with compatibility tests from the current config.
5. Promote domain-fork examples only after they add domain validators and explicit non-claim boundaries.
