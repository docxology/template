# template_code_project TODO

Forward-only integrity backlog for the optimization research control-positive
exemplar. Keep this file focused on template status, not general feature ideas.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`
- Stage 02 analysis must write `output/data/optimization_results.csv` before strict manuscript-variable generation.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: PDF, markdown, output structure, figure registry, evidence registry, and design overlays pass; artifact manifest reports advisory drift after single-stage regeneration.

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for code-centric research projects.
- Add a project-local output validation script only if it checks artifacts beyond the generic Stage 04 validators.
- Keep dashboard, API docs, figures, and manuscript variables generated from source, not hand-maintained output snapshots.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Add any future optimizer hyperparameter config under typed source loaders rather than reading ad hoc YAML from scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_code_project`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator.

## Test and validator gaps

- Add a negative control before widening optimizer claims beyond the bundled deterministic objectives.
- Add dashboard schema assertions whenever dashboard fields or chart payloads change.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

## Ordered improvement ladder

1. Preserve the strict analysis-to-manuscript variable contract.
2. Add focused validators for any new generated artifact family.
3. Expand benchmark scenarios only with deterministic seeds, expected-shape tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.
