# Configuration

`template_autoresearch_project` splits configuration between infrastructure
readiness, the human-authored AutoResearch program, and manuscript loop
settings. The central case study is a tiny deterministic ML task, but the
default run remains offline and proposal-only.

## `autoresearch.yaml` (infrastructure readiness)

Loaded by `infrastructure.autoresearch.load_autoresearch_config` and merged
into `build_autoresearch_plan()`:

- `enabled`: opts the project into AutoResearch validation.
- `strict`: turns readiness warnings into blocking errors where applicable.
- `topic`: names the research loop in generated plans and reports.
- `autonomy_level`: remains `proposal_only` for the public exemplar.
- `budget`: records iteration, wall-clock, LLM-call, and cost limits.
- `edit_allowlist`: limits proposal candidates to explicit project paths.
- `metric_direction` and `acceptance_policy`: record how candidates are judged.
- `quality_checks`: selects deterministic validation surfaces.
- `stage_gates`: declares exact pipeline stage names that must exist.
- `review_gates`: declares required human decisions.
- `benchmark_tasks`: declares grading outputs for benchmark-style checks.
- `disclosure_required` / `disclosure_text`: requires AI-assisted status prose
  in the manuscript.
- `required_artifacts`: lists files that must exist after analysis (merged with
  `domain_profile.yaml` `artifact_expectations` in the plan).

## `program.md` and `seed_ideas.yaml`

`program.md` is the human-authored research program. `seed_ideas.yaml` records
the deterministic proposal set used to produce accepted, rejected, and deferred
idea ledgers. The accepted ML-loop idea declares candidate feature maps, ridge
penalties, complexity scores, expected artifacts, and touched paths. Accepted
ideas must carry evidence links; candidates must keep their `touched_paths`
inside `edit_allowlist`.

The ML-loop candidate parameters are consumed by `src.ml_task.load_candidate_specs`.
The configured iteration budget decides how many candidates are evaluated; any
remaining candidates are written as deferred rather than executed later by an
autonomous process.

## `manuscript/config.yaml` (loop settings)

Loaded by `src.config.load_manuscript_loop_settings`:

- `analysis.scripts`: runs the thin orchestrators in `scripts/`.
- `project_config.review_policy`: records the required human review mode.
- `project_config.loop_stages`: configures deterministic loop stages.
- `project_config.research_questions`: declares questions and expected
  evidence paths.

Runtime loop configuration is merged in `src.config.build_loop_config(plan,
settings)` so `required_artifacts` and `quality_checks` come from the composed
plan, not a second parse of `autoresearch.yaml` in project code.

## ML task implementation

`src/ml_task.py` uses `numpy` only. It generates a fixed-seed nonlinear binary
classification dataset, evaluates a majority-class baseline, scores bounded
linear and quadratic ridge-classifier candidates by held-out accuracy, and
selects the best result with deterministic simplicity tie-breaking. The task
writes `ml_task_results.json`, `ml_candidate_ledger.json`,
`ml_experiment_report.md`, `ml_benchmark_score.json`, and
`ml_candidate_scores.png` through `src.writers`.

## Scripts

- `scripts/run_autoresearch_loop.py` calls `src.loop.run_autoresearch_loop`.
- `scripts/z_generate_manuscript_variables.py` calls
  `src.manuscript_variables` helpers and writes resolved manuscript files.

## Validation phases

`validate_autoresearch_plan(..., phase=...)` supports:

- `intrinsic` — domain profile, experiment plan, pipeline contracts, thin
  orchestrators, AI-assisted disclosure
- `extrinsic` — evidence registry, artifact manifest, method ledgers, review
  decisions, and benchmark grading outputs (post-write surfaces)
- `all` — default; runs every configured check

The readiness validator only checks local deterministic surfaces. It does not
execute pipeline stages or approve publication automatically.
