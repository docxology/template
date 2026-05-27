# AutoResearch Loop Report

- Project: `template_autoresearch_project`
- Topic: Deterministic bounded AutoResearch for a small MNIST neural-network task
- Readiness valid: `true`
- Supported claims: 6

## ML Task

- Accepted candidate: `exp-mlp-tanh-64`
- Baseline accuracy: 0.826
- Best accuracy: 0.894
- Accuracy delta: 0.068

## Stages

- `plan`: declared - Declared 12 pipeline stage contract(s).
- `gate`: declared - Declared exact stage-gate names from autoresearch.yaml.
- `experiment`: declared - Ran the fixed-seed bounded ML-loop candidate evaluation.
- `evidence`: declared - Declared local domain, experiment, pipeline, and output evidence targets.
- `claims`: declared - Mapped configured questions to on-disk evidence paths.
- `artifacts`: declared - Declared machine-readable data and human-readable report outputs.
- `readiness`: declared - Scheduled intrinsic and extrinsic AutoResearch readiness checks.

## Claims

- `rq1` (supported): Can the template express a bounded AutoResearch loop without autonomous execution? Evidence is grounded in `output/reports/autoresearch_loop.md`.
- `rq2` (supported): Can a deterministic candidate loop evaluate and select a small MNIST neural-network configuration under budget? Evidence is grounded in `output/data/ml_task_results.json`.
- `rq3` (supported): Are manuscript claims grounded in generated project artifacts? Evidence is grounded in `output/reports/evidence_registry.json`.
- `rq4` (supported): Can readiness checks be rerun from the standard validation stage? Evidence is grounded in `output/reports/autoresearch_readiness.json`.
- `rq5` (supported): Does the benchmark ledger record metric improvement, budget compliance, and offline execution? Evidence is grounded in `output/reports/ml_benchmark_score.json`.
- `rq6` (supported): Does the local security layer record artifact-integrity evidence without claiming external signing? Evidence is grounded in `output/data/autoresearch_integrity_attestation.json`.
