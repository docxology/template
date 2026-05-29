# template_autoresearch_project - Agent Notes

## Purpose

This project is the public exemplar for deterministic AutoResearch loops in
`template/`. It should remain small, auditable, and runnable through `run.sh`.

## Architecture

- Business logic: `src/`
  - `loop.py` — thin orchestrator (`run_autoresearch_loop`)
  - `ml_data.py` — MNIST task config, fixture loading, provenance summary, and array validation
  - `ml_models.py` — baseline and candidate evaluation, robustness transforms, and model-result records
  - `ml_training.py` — numpy-only softmax, MLP, patch-attention features, SGD schedules, clipping, and metric primitives
  - `ml_selection.py` — bounded task orchestration, candidate ranking, tie-breaking, histories, and error examples
  - `ml_task.py` — compatibility exports for the public ML API
  - `diagnostics_records.py` — probability-aware prediction records and candidate row validators
  - `diagnostics_metrics.py` — class metrics, calibration, robustness, probability quality, statistical summary, and training dynamics
  - `diagnostics_intervals.py` — Wilson intervals, bootstrap intervals, rank stability, and paired-comparison statistics
  - `diagnostics_reports.py` — diagnostic bundle assembly, selection audit, boundary report, and JSON writers
  - `diagnostics.py` — compatibility exports by diagnostic surface
  - `security.py` — local deterministic security profile, threat model, SBOM-style inventory, checksum attestation, and security review packet
  - `models.py` — loop result dataclasses
  - `config.py` — manuscript settings + plan merge (`build_loop_config`)
  - `writers.py` — JSON/CSV/manifest I/O; delegates figure batching to `writers_figure_dispatch.py` and benchmark grading to `writers_benchmark.py`
  - `reports.py` — markdown and review-packet renderers
  - `figures_core.py` — shared chart primitives (bar panels, matrix annotations)
  - `figures_ml.py` — compatibility barrel; implementations in `figures_ml_{candidates,calibration,matrices,mnist}.py`
  - `figures_process.py` — stage matrix, candidate lifecycle, and closure-flow figures
  - `figures_security.py` — security-control and integrity-chain figures
  - `figures.py` — compatibility exports by figure family
  - `manuscript_variables.py` — facade; token logic in `manuscript_tokens_{core,ml,figures,format}.py`
  - `manuscript_tables.py` — facade; builders in `manuscript_tables_{builders,format}.py`
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
5. `run_bounded_ml_task()` + `write_ml_task_artifacts()` — deterministic ML results, candidate ledger, shared diagnostic bundle, selection audit, boundary report, benchmark score, figures, and figure-quality report
6. `build_claims()` + `finalize_loop_payloads()` — file-backed claims and loop JSON/review payloads
7. `write_method_contract_artifacts()` — research program, idea ledger, run ledger, deferred review decisions, benchmark scores
8. `update_result_payloads()` — provisional refresh (`readiness_valid=False`)
9. `write_security_artifacts()` + schema/research-object manifests + phase ledger + `write_artifact_manifest()` — local security profile, threat model, inventory, attestation, review, and manifest passes
10. `validate_autoresearch_plan(..., phase="extrinsic")` — evidence, artifacts, method ledgers, review gates, benchmarks, security artifacts
11. `write_autoresearch_report()` — combined intrinsic + extrinsic readiness
12. `build_claims()` + `update_result_payloads()` — final refresh with `readiness_valid`, readiness evidence, and output paths
13. `write_final_visual_artifacts()` — regenerate captions and figures from the final validated loop state
14. `write_manuscript_hydration_artifacts()` — write variables, figure-blocks, and token provenance sidecars
15. `write_evidence_registry_report()` + `write_security_artifacts()` + phase ledger + schema/research-object manifests + `write_artifact_manifest()` — final registry, local security evidence, settlement ledger, and manifests

Loop stages use status `declared` (intent only — not pipeline execution proof).
Claims are `supported` only when the configured evidence path points at
substantive content on disk — a non-empty, parseable artifact (an empty file,
`{}`/`[]`, an all-null JSON tree, or a header-only CSV does not support a claim).
This substance binding is shared with the figure-quality and benchmark gates via
`src/artifact_content.is_substantive_artifact` and is locked by negative-control
tests in `tests/test_gate_negative_controls.py`.
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
- Add orchestration in `src/loop.py`; add I/O in `src/writers.py` (or `writers_figure_dispatch.py` / `writers_benchmark.py` when the surface grows); add renderers in `src/reports.py`.
- Keep ML task logic in `src/ml_data.py`, `src/ml_models.py`,
  `src/ml_training.py`, and `src/ml_selection.py`; do not move model evaluation
  into scripts.
- Keep true publication approval in the human-authored `human_review.yaml`.
  Generated readiness may never self-approve publication.
- Add manuscript tokens in `src/manuscript_tokens_*.py` (re-export via `manuscript_variables.py`), tables in `manuscript_tables_builders.py`, figure blocks, and provenance — then extend tests.
- Register every generated figure with source artifact, alt text, and claim
  boundary metadata before inserting it into numbered manuscript files.
- Keep figure generation methods in `output/figures/figure_registry.json`; the
  manuscript figure-method table is hydrated from that registry.
- Keep all numbered manuscript run-derived values tokenized; strict tokenization
  means the hydration script is expected to fail on raw accepted-candidate IDs,
  metric values, dataset/model labels, artifact paths, or registry captions.
- Keep `autoresearch.yaml` stage names exact against `pipeline.yaml`.
- Update `docs/` when changing configurable methods or output contracts.

## Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md)
- `manuscript/config.yaml` uses split DOIs: `publication.doi` (concept), `version_doi`, `version_record`
- Current release/DOI records are generated in [`docs/_generated/publication_records.md`](../../../docs/_generated/publication_records.md); release with `uv run python scripts/publish_project_release.py --project template_autoresearch_project --tag <vX.Y.Z> --repo docxology/template_autoresearch_project` after choosing the intended tag from `paper.version`.
