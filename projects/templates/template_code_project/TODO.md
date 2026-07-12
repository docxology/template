# template_code_project TODO

Forward-only backlog for the code-first numerical exemplar — the reference
thin-orchestrator control-positive path for code-centric research projects.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`
- Stage 02 analysis must write `output/data/optimization_results.csv` before strict manuscript-variable generation: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project`
- Stage 03 manuscript render: `uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project`
- Stage 04 output validation: `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_code_project/src/` and `uv run mypy projects/templates/template_code_project/src/` must both pass clean.
- Benchmark reproducibility: tracked benchmark reports and figures contain only deterministic facts; wall-clock timing is logged as a runtime diagnostic, and two-run byte-equality tests enforce the boundary.
- Live test count and measured coverage percentage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (regenerated, never hardcoded here; both numbers drift faster than this file).

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for code-centric research projects.
- Keep dashboard, API docs, figures, and manuscript variables generated from source, not hand-maintained output snapshots.
- Add a project-local output validation script only if it checks artifacts beyond the generic Stage 04 validators.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Add any future optimizer hyperparameter config under typed source loaders rather than reading ad hoc YAML from scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_code_project`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator.

## Test and validator gaps

- Add a negative control before widening optimizer claims beyond the bundled deterministic objectives.
- Add dashboard schema assertions whenever dashboard fields or chart payloads change.
- Close remaining infrastructure-path branch misses in `analysis/scientific_reports.py` and `analysis/workflow.py` with subprocess isolation tests mirroring `TestImportFallback` if coverage gates tighten further.

## Ordered improvement ladder

1. Preserve the strict analysis-to-manuscript variable contract.
2. Add focused validators for any new generated artifact family.
3. Expand benchmark scenarios only with deterministic seeds, expected-shape tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.
