# Pipeline Control Surfaces

This repository keeps adaptive research workflow controls explicit and
file-backed. The controls below are advisory unless a project or command opts
into them.

## Adapted from AutoResearchClaw

The control surface was informed by
[aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
at commit `b5804c5fa0acecc01f56bdf52995e11bb74474cc`: stage contracts/gates, HITL checkpoints, SmartPause-style
recommendation reports, SHA256 artifact manifests, evidence registries,
run lessons, benchmarks, and domain profiles. This template adapts those ideas
only as auditable, file-backed controls that a human or CI job can inspect.

Explicitly **not** adopted: a default 23-stage idea-to-paper autonomous engine,
simulated research results, automatic prompt or skill mutation, hidden
self-approval loops, WebSocket/MCP approval servers, or automatic consumption of
lessons as future instructions. Reports are written to disk; projects opt in to
stronger behavior deliberately.

## AutoResearch Readiness

`infrastructure.autoresearch` adds an opt-in deterministic readiness layer over
existing template modules. It builds an `AutoResearchPlan` from the project
domain profile, experiment plan, pipeline DAG, declared stage gates, required
artifacts, evidence registry, artifact manifest, and thin-orchestrator drift
checks.

Project-local configuration is optional:

```yaml
enabled: true
strict: true
topic: "Deterministic readiness"
quality_checks:
  - domain_profile
  - experiment_plan
  - pipeline_contracts
  - evidence_registry
  - artifact_manifest
  - thin_orchestrators
stage_gates:
  - Project Analysis
  - Output Validation
required_artifacts:
  - output/data/result.csv
```

`stage_gates` entries are exact `pipeline.yaml` stage names. Unknown stage
names or unknown quality checks fail validation. Non-strict mode reports
readiness gaps as warnings where possible; strict mode treats them as errors.

Run readiness validation directly with:

```bash
uv run python -m infrastructure.autoresearch.cli validate --project template_code_project --fail-on-issues
```

Reports are written to
`projects/{project}/output/reports/autoresearch_readiness.json` and
`projects/{project}/output/reports/autoresearch_readiness.md`. The output
validation stage includes AutoResearch readiness when `autoresearch.yaml`
exists.

## Stage Contracts

Default stages in `infrastructure/core/pipeline/pipeline.yaml` may declare:

- `input_artifacts`
- `output_artifacts`
- `definition_of_done`
- `failure_code`
- `retry_policy`
- `gate`
- `rollback_to`

Contracts are metadata plus narrow executor behavior. `retry_policy` controls
stage retries, and `gate` is used only by HITL modes that pause on gates.

## Control Config

Pipeline YAML may add a top-level `control:` block. Values merge in this order:
dataclass defaults, default `pipeline.yaml`, project `pipeline.yaml`, then CLI
flags. Later sources override earlier sources while preserving nested
`stage_policies` fields that were not replaced.

```yaml
control:
  hitl_mode: full-auto
  smart_pause_action: report
  custom_gate_stages: []
  stage_policies:
    "6":
      pause_after: true
      require_approval: true
      allow_guidance: true
      timeout_seconds: 86400
      auto_proceed_on_timeout: false
```

Unknown control keys fail fast. The default config remains `full-auto`.

## Hooks

Stages may declare explicit hook commands under:

- `pre_stage`
- `post_stage`
- `on_fail`
- `on_pause`

Hooks run with `shell=False`, default to a 30 second timeout, and are disabled
under CI unless `run_in_ci: true` is declared. Hook environments include:

- `TEMPLATE_PROJECT`
- `TEMPLATE_STAGE_NAME`
- `TEMPLATE_STAGE_NUM`
- `TEMPLATE_RUN_DIR`
- `TEMPLATE_STAGE_CONTEXT`

## HITL Commands

Pipeline runs default to `--hitl-mode full-auto`. Other modes are:

- `gate-only`: pause after stages with a `contract.gate`
- `checkpoint`: pause after every completed stage
- `custom`: reserved for project-specific stage selections

Non-interactive commands:

```bash
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command status
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command history
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command context
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command validate-response --response-file /tmp/response.json
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command respond --response-file /tmp/response.json
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command guide --hitl-stage 6 --message "Check citations."
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command approve --message "Ready."
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command reject --message "Citation drift."
uv run python scripts/runner/execute_pipeline.py --project template_code_project --hitl-command resume --message "Continue."
```

State is written under `projects/{project}/output/hitl/`. Resuming execution
still uses the existing checkpoint system.

Pause points also write adapter-ready detached review files:

- `output/hitl/agent_context.json` — stage metadata, declared artifacts,
  validation summary, guidance history, and permitted actions.
- `output/hitl/agent_response.schema.json` — accepted response shape. Only
  `approve`, `reject`, `guide`, `resume`, and `abort` are valid actions.

Responses are ignored unless explicitly submitted with `--hitl-command respond`.
There is no WebSocket server, MCP server, or autonomous approval loop.

## SmartPause Recommendations

The executor writes advisory SmartPause recommendations to
`output/reports/pause_recommendations.json`. Scores are based on failed
validation checks, evidence issues, artifact drift, telemetry warnings,
experiment-plan problems, AutoResearch readiness failures, and prior human
rejections.

`control.smart_pause_action: report` is the default. Set it to `pause` only when
a project intentionally wants a nonzero recommendation to create a HITL pause.

## Artifact Manifests

After each successful completed stage, the executor writes a local stage
manifest under `projects/{project}/output/.pipeline/artifacts/` and refreshes
`projects/{project}/output/reports/artifact_manifest.json`. Entries include
path, size, SHA256, producing stage, contract match status, and timestamp.

Validation reports missing declared outputs, changed hashes, and undeclared
artifacts. Logs, HITL state, caches, and `.pipeline` metadata are ignored. The
stable `artifact_manifest.json` is the publication-facing integrity record;
the local stage manifests and their timestamps are not public evidence.

## Snapshots

Each completed stage may write a local snapshot under
`output/reports/snapshots/` with
the artifact manifest hash, artifact hashes, validation summary, evidence count,
stage number, stage name, and timestamp. Compare snapshots or output
directories with:

```bash
uv run python -m infrastructure.core.pipeline.snapshot compare <left> <right> --output-dir projects/templates/template_code_project/output
```

Snapshots are diagnostic state and are ignored by the public checkout.
Comparison reports are written as `snapshot_compare.json` and
`snapshot_compare.md` when `--output-dir` is supplied. Snapshot comparison does
not fork or run project branches.

## Evidence Registry

`infrastructure.validation.evidence_registry` builds a verified registry from
project-local artifacts: manuscript variables, BibTeX keys, figure/table
labels, data JSON values, claim ledgers, and generated artifact paths. The
validation CLI can flag unsupported manuscript numbers and citations:

```bash
uv run python -m infrastructure.validation.cli.main evidence projects/templates/template_code_project --fail-on-issues
```

The output validation stage writes
`projects/{project}/output/reports/evidence_registry.json`. The report includes
source-tier counts and freshness warnings for stale or inactive facts. Abstracts,
results, tables, captions, and claim-ledger-style files are strict zones;
background and introduction prose produce warnings unless strict mode is
requested.

## Domain Profiles

Projects may add `domain_profile.yaml` with:

- `domain`
- `display_name`
- `required_packages`
- `preferred_outputs`
- `validation_gates`
- `figure_types`
- `citation_policy`
- `llm_prompt_guidance`
- `review_gates`
- `source_policy`
- `artifact_expectations`
- `benchmark_rubric`

Missing profiles resolve to a built-in generic profile. Built-in fallback
profiles also cover code research, prose research, and literature review.
Unknown keys fail fast.

The public canonical exemplars ship explicit overlays:
`projects/templates/template_code_project/domain_profile.yaml`,
`projects/templates/template_code_project/experiment_plan.yaml`,
`projects/templates/template_prose_project/domain_profile.yaml`,
`projects/templates/template_prose_project/experiment_plan.yaml`,
`projects/templates/template_autoresearch_project/domain_profile.yaml`, and
`projects/templates/template_autoresearch_project/experiment_plan.yaml`. Treat them as
copy-and-edit starting points for new public projects.

Projects may also add `experiment_plan.yaml` for design validation:

```yaml
conditions:
  - name: baseline
    role: reference
metrics:
  primary:
    name: accuracy
    direction: maximize
protocol: "Run all conditions with identical seeds."
expected_figures: [fig:accuracy]
expected_tables: [tbl:results]
baselines: [baseline]
ablations: [ablation]
```

The allowed condition roles are `reference`, `proposed`, and `variant`. The
validator checks declarations only; it does not generate experiments.

## Run Lessons

Every pipeline execution writes explicit lesson reports under
`projects/{project}/output/reports/lessons.jsonl`, `lessons.md`, and
`next_run_context.md`. Lessons record failed stages, hook failures when present,
artifact drift, validation defects, smart-pause recommendations, slow-stage
notes, and human gate decisions. They are reports, not hidden prompt mutation;
`next_run_context.md` is not automatically consumed.

## Template Benchmark

The benchmark harness lives in `infrastructure/benchmark/template_harness.py`
with a fixed smoke manifest at
`infrastructure/benchmark/template_smoke_manifest.json`.

```bash
uv run python -m infrastructure.benchmark.template_harness --repo-root .
uv run python -m infrastructure.benchmark.template_harness --repo-root . --write-default-manifest
```

The default manifest written by `--write-default-manifest` scores the public
canonical exemplars only — the full `PUBLIC_PROJECT_NAMES` set in
[`infrastructure/project/public_scope.py`](../../infrastructure/project/public_scope.py)
(authoritative roster → [`docs/_generated/active_projects.md`](../_generated/active_projects.md)).
The shipped fixed smoke manifest is generated from and contract-tested against
that same full public roster. Missing projects, validation reports, declared
reproducibility artifacts, renders, or current artifact manifests fail closed.

Benchmark manifests may attach a weighted rubric for reproducibility, evidence
grounding, rendering, cross-reference integrity, source quality, and publication
readiness dimensions. Rubric dimensions must exactly match the checks and use
positive finite weights. Reports can be emitted as JSON or Markdown and include
per-check pass state, score, maximum score, and issues.
