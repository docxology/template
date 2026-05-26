# template_autoresearch_project - Agent Notes

## Purpose

This project is the public exemplar for deterministic AutoResearch loops in
`template/`. It should remain small, auditable, and runnable through `run.sh`.

## Architecture

- Business logic: `src/`
  - `loop.py` — thin orchestrator (`run_autoresearch_loop`)
  - `ml_training.py` — local MNIST subset loading, numpy neural networks, bounded candidate evaluation, configurable SGD schedules, training histories, probabilities, robustness rows, and error examples
  - `ml_task.py`, `ml_data.py`, `ml_models.py`, `ml_selection.py` — compatibility exports for orchestration, data, model, and selection entry points
  - `diagnostics_reports.py` — prediction records, class metrics, candidate intervals, class balance, calibration, confusion-pair, generalization-gap, robustness, bootstrap, probability-margin, paired-comparison, statistical-summary, and training-dynamics reports
  - `diagnostics.py`, `diagnostics_records.py`, `diagnostics_metrics.py`, `diagnostics_intervals.py` — compatibility exports by diagnostic surface
  - `security.py` — local deterministic security profile, threat model, SBOM-style inventory, checksum attestation, and security review packet
  - `models.py` — loop result dataclasses
  - `config.py` — manuscript settings + plan merge (`build_loop_config`)
  - `writers.py` — JSON/CSV/manifest I/O and final visual artifact refresh
  - `reports.py` — markdown and review-packet renderers
  - `figures_core.py` — stage matrix, candidate score, confusion matrix, learning-curve, training-dynamics, complexity, per-class, error-example, calibration, class-metric, confusion-pair, generalization-gap, robustness, probability-margin, bootstrap-interval, paired-correctness, selective-accuracy, probability-quality, lifecycle, class-balance, contact-sheet, closure-flow, security-control, and integrity-chain figures + registry metadata
  - `figures.py`, `figures_ml.py`, `figures_process.py`, `figures_security.py` — compatibility exports by figure family
  - `manuscript_variables.py` — strict render-time token hydration, figure blocks, and provenance sidecars
  - `source_ledger.py`, `artifact_schemas.py`, `research_object.py` — offline source-ledger validation, schema manifest generation, and local research-object manifest packaging
- Thin scripts: `scripts/`
- Project docs: `docs/`
- Manuscript source: `manuscript/`
- Human-authored program: `program.md`
- Seed proposals: `seed_ideas.yaml`
- Executable MNIST task config: `mnist_task.yaml`
- Local input data: `data/`
- Generated artifacts: `output/`

The analysis stage must not perform network calls, LLM calls, generated-code
execution, runtime dataset downloads, or autonomous approval. It composes
existing infrastructure modules:

- `infrastructure.autoresearch`
- `infrastructure.validation.evidence_registry`
- `infrastructure.core.pipeline.artifacts`
- `infrastructure.rendering.manuscript_injection`

## Loop flow

1. `build_autoresearch_plan()` and `build_loop_config()` — canonical artifacts and manuscript settings
2. `validate_autoresearch_plan(..., phase="intrinsic")` — domain, experiment, pipeline, scripts
3. `write_core_loop_artifacts()` — plan JSON, loop markdown, stage matrix CSV, figure
4. `write_evidence_registry_report()` — first registry snapshot from on-disk artifacts
5. `run_bounded_ml_task()` + `write_ml_task_artifacts()` — deterministic ML results, candidate ledger, diagnostics, selection audit, boundary report, benchmark score, figures
6. `build_claims()` + `finalize_loop_payloads()` — file-backed claims and loop JSON/review payloads
7. `write_method_contract_artifacts()` — research program, idea ledger, run ledger, deferred review decisions, benchmark scores
8. `update_result_payloads()` — provisional refresh (`readiness_valid=False`)
9. `write_security_artifacts()` + schema/research-object manifests + `write_artifact_manifest()` — local security profile, threat model, inventory, attestation, review, and manifest passes
10. `validate_autoresearch_plan(..., phase="extrinsic")` — evidence, artifacts, method ledgers, review gates, benchmarks, security artifacts
11. `write_autoresearch_report()` — combined intrinsic + extrinsic readiness
12. `build_claims()` + `update_result_payloads()` — final refresh with `readiness_valid`, readiness evidence, and output paths
13. `write_final_visual_artifacts()` — regenerate captions and figures from the final validated loop state
14. `write_manuscript_hydration_artifacts()` — write variables, figure-blocks, and token provenance sidecars
15. `write_evidence_registry_report()` + `write_security_artifacts()` + schema/research-object manifests + `write_artifact_manifest()` — final registry, local security evidence, and manifests

Loop stages use status `declared` (intent only — not pipeline execution proof).
Claims are `supported` only when the configured evidence path exists on disk.
Accepted seed ideas require evidence links; candidate `touched_paths` must stay
inside `autoresearch.yaml` `edit_allowlist`. The ML-loop candidate budget is
finite; candidates beyond it are recorded as deferred.
Security artifacts are local-only integrity evidence: no network calls, no
external signing, no production SLSA compliance claim, no complete dependency
SBOM claim, and no runtime security monitoring are part of the default exemplar.

## Run Commands

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only
uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues
```

## Editing Rules

- Keep `scripts/` as orchestrators only.
- Add orchestration in `src/loop.py`; add I/O in `src/writers.py`; add renderers in `src/reports.py`.
- Keep ML task logic in `src/ml_training.py` and its compatibility exports; do
  not move model evaluation into scripts.
- Keep true publication approval in the human-authored `human_review.yaml`.
  Generated readiness may never self-approve publication.
- Add manuscript tokens, generated tables, figure blocks, and provenance through
  `src/manuscript_variables.py` and tests.
- Register every generated figure with source artifact, alt text, and claim
  boundary metadata before inserting it into numbered manuscript files.
- Keep figure generation methods in `output/figures/figure_registry.json`; the
  manuscript figure-method table is hydrated from that registry.
- Keep all numbered manuscript run-derived values tokenized; strict tokenization
  means the hydration script is expected to fail on raw accepted-candidate IDs,
  metric values, dataset/model labels, artifact paths, or registry captions.
- Keep `autoresearch.yaml` stage names exact against `pipeline.yaml`.
- Update `docs/` when changing configurable methods or output contracts.
