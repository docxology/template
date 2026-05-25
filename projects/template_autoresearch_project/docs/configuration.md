# Configuration

`template_autoresearch_project` splits configuration between infrastructure
readiness and manuscript loop settings.

## `autoresearch.yaml` (infrastructure readiness)

Loaded by `infrastructure.autoresearch.load_autoresearch_config` and merged
into `build_autoresearch_plan()`:

- `enabled`: opts the project into AutoResearch validation.
- `strict`: turns readiness warnings into blocking errors where applicable.
- `topic`: names the research loop in generated plans and reports.
- `quality_checks`: selects deterministic validation surfaces.
- `stage_gates`: declares exact pipeline stage names that must exist.
- `required_artifacts`: lists files that must exist after analysis (merged with
  `domain_profile.yaml` `artifact_expectations` in the plan).

## `manuscript/config.yaml` (loop settings)

Loaded by `src.config.load_manuscript_loop_settings`:

- `analysis.scripts`: runs the thin orchestrators in `scripts/`.
- `autoresearch_project.review_policy`: records the required human review mode.
- `autoresearch_project.loop_stages`: configures deterministic loop stages.
- `autoresearch_project.research_questions`: declares questions and expected
  evidence paths.

Runtime loop configuration is merged in `src.config.build_loop_config(plan,
settings)` so `required_artifacts` and `quality_checks` come from the composed
plan, not a second parse of `autoresearch.yaml` in project code.

## Scripts

- `scripts/run_autoresearch_loop.py` calls `src.loop.run_autoresearch_loop`.
- `scripts/z_generate_manuscript_variables.py` calls
  `src.manuscript_variables` helpers and writes resolved manuscript files.

## Validation phases

`validate_autoresearch_plan(..., phase=...)` supports:

- `intrinsic` — domain profile, experiment plan, pipeline contracts, thin
  orchestrators
- `extrinsic` — evidence registry and artifact manifest (post-write surfaces)
- `all` — default; runs every configured check

The readiness validator only checks local deterministic surfaces. It does not
execute pipeline stages or approve publication automatically.
