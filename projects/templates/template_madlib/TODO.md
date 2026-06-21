# template_madlib TODO

Forward-only integrity backlog for the deterministic token-injection manuscript
exemplar. This tree is part of the public template roster and must satisfy the
same forkability contract as the older exemplars.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_madlib/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90`
- Generated artifacts come from `scripts/01_generate_madlib_artifacts.py` and `scripts/z_generate_manuscript_variables.py`.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Publication evidence: standalone GitHub repository `docxology/template_madlib`, concept DOI `10.5281/zenodo.20786638`, and version DOI `10.5281/zenodo.20786639`.

## Integrity and template-status gaps

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

- Add a project-local output validator if Stage 04 cannot catch token provenance, figure registry, and authoring-contract regressions together.
- Add a stale-artifact check if generated artifact names or report schemas grow beyond the current fixture coverage.
- Preserve review-packet assertions if future copied-output layout changes make output statistics, validation reports, or copied data/report/figure categories optional.

## Ordered improvement ladder

1. Keep release metadata, module size, tests, and drift gates green as the published canonical exemplar evolves.
2. Add negative controls for unresolved placeholders and missing token provenance.
3. Add negative controls for digest-invariant drift and missing review-packet artifacts.
4. Add schema migrations only with compatibility tests from the current config.
5. Promote domain-fork examples only after they add domain validators and explicit non-claim boundaries.
