# AutoResearch Module - Agent Notes

## Purpose

`infrastructure/autoresearch` provides opt-in deterministic readiness checks.
Use it when a project wants AutoResearchClaw-inspired planning and validation
without autonomous research execution.

## Boundaries

- No network calls.
- No LLM calls.
- No generated-code execution.
- No autonomous self-approval loops.
- Scripts remain thin; use `python -m infrastructure.autoresearch.cli` instead
  of adding root entry points.

## Public Interfaces

- `AutoResearchConfig`
- `BudgetPolicy`
- `ReviewGate`
- `BenchmarkTask`
- `EvidenceLink`
- `ResearchIdea`
- `ExperimentCandidate`
- `ResearchProgram`
- `RunLedger`
- `AutoResearchPlan`
- `AutoResearchIssue`
- `AutoResearchReport`
- `INTRINSIC_QUALITY_CHECKS` / `EXTRINSIC_QUALITY_CHECKS`
- `load_autoresearch_config(project_root)`
- `parse_string_sequence(value, *, default)`
- `build_autoresearch_plan(repo_root, project_name, projects_dir="projects")`
- `validate_autoresearch_plan(plan, project_root, *, phase="all")`
- `write_autoresearch_report(project_root, report)`

## Validation phases

`validate_autoresearch_plan(..., phase=...)`:

| Phase | Checks |
| --- | --- |
| `intrinsic` | `domain_profile`, `experiment_plan`, `pipeline_contracts`, `thin_orchestrators`, `ai_disclosure` |
| `extrinsic` | `evidence_registry`, `artifact_manifest`, `method_contracts`, `review_gates`, `benchmark_tasks` |
| `all` | every configured check (default) |

Stage-gate and unknown quality-check validation always runs regardless of
phase.

## Validation Inputs

The module validates only file-backed deterministic surfaces:

- `autoresearch.yaml`
- `domain_profile.yaml`
- `experiment_plan.yaml`
- `pipeline.yaml`
- `output/reports/artifact_manifest.json`
- project evidence registry facts
- root and project script thin-orchestrator drift
- `output/data/idea_ledger.json`
- `output/data/run_ledger.json`
- `output/data/review_decisions.json`
- `output/data/benchmark_scores.json`
- configured disclosure text or `{{DISCLOSURE_TEXT}}` token in manuscript Markdown

## Configuration Rules

`stage_gates` are exact `pipeline.yaml` stage names, not gate labels.
Valid `quality_checks` are:

- `domain_profile`
- `experiment_plan`
- `pipeline_contracts`
- `evidence_registry`
- `artifact_manifest`
- `thin_orchestrators`
- `method_contracts`
- `review_gates`
- `benchmark_tasks`
- `ai_disclosure`

Strict mode promotes advisory readiness defects to errors. Configuration
defects such as unknown stage names or unknown checks are always errors.
