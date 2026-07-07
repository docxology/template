# template_code_project TODO

Forward-only integrity backlog for the optimization research control-positive
exemplar. Keep this file focused on template status, not general feature ideas.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`
- Stage 02 analysis must write `output/data/optimization_results.csv` before strict manuscript-variable generation.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: PDF, markdown, output structure, figure registry, evidence registry, and design overlays pass; artifact manifest reports advisory drift after single-stage regeneration.
- Code quality: `uv run ruff check projects/templates/template_code_project/src/` and `uv run mypy projects/templates/template_code_project/src/` must both pass clean.
- Coverage floor: ≥90% on `src/` (`pyproject.toml`); live test count + measured coverage percentage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (per Rule 2, [`docs/agent_instructions.md`](docs/agent_instructions.md) — do not hardcode either number here, both drift faster than this file).

## Recent improvements (2026-06)

- Fixed ruff errors: removed unused `field` import from `scientific_complexity.py`; suppressed unused variable via `# noqa: F841`.
- Fixed mypy errors: renamed loop variable in `multi_factor_analysis` fallback branch (`v` → `variant`) to resolve type-inference conflict; removed stale `type: ignore[misc]` from `log_success` fallback definition.
- Added `# pragma: no cover` to standalone-mode import fallback lines in `_runtime.py` and `_infra.py` (covered by subprocess isolation tests already in the suite).
- Added 34 new tests covering previously untested code paths:
  - `compare_algorithms` (all branches: pre-computed results, timing, stability, convergence rate, fastest/slowest ranking)
  - `multi_factor_analysis` (all branches: custom weights with unknown keys, zero-total weights, low convergence/stability recommendations, `_variant_score` for unconverged variants, degenerate empty-variants case)
  - `BackendProfile` analysis methods: `effective_max_stable_alpha` with explicit override, `effective_label_alpha` both paths, `profile_stable_region`, `compare_profiles_at_alpha`
  - `AlphaSweepConfig.resolved_alphas` ValueError path (neither alphas nor min/max/num provided) and linspace path
  - `convergence_rate = 0.0` branch for single-history-point variants

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
- `analysis/scientific_reports.py` lines 234, 274-277 (infrastructure-path branches) and `analysis/workflow.py` branch misses remain; these are only reachable with specific infrastructure states. Consider subprocess isolation tests mirroring `TestImportFallback` if coverage gates tighten further.

## Ordered improvement ladder

1. Preserve the strict analysis-to-manuscript variable contract.
2. Add focused validators for any new generated artifact family.
3. Expand benchmark scenarios only with deterministic seeds, expected-shape tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.
