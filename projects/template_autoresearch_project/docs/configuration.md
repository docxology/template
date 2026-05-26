# Configuration

`template_autoresearch_project` splits configuration between infrastructure
readiness, the human-authored AutoResearch program, the MNIST neural-network
task, and manuscript loop settings. The central case study is a tiny
deterministic small MNIST task, but the default run remains offline and proposal-only.

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
- `security_profile`: enables the local deterministic security layer. The
  public exemplar uses `local_deterministic`, `default_offline`, SHA-256
  integrity checks, STRIDE plus MITRE ATT&CK T1195 labels, and
  `external_signing: false`.
- `required_artifacts`: lists files that must exist after analysis (merged with
  `domain_profile.yaml` `artifact_expectations` in the plan).

## `program.md` and `seed_ideas.yaml`

`program.md` is the human-authored research program. `seed_ideas.yaml` records
the deterministic proposal set used to produce accepted, rejected, and deferred
idea ledgers. The accepted ML-loop idea declares the softmax, MLP, and
patch-attention candidate identifiers, expected artifacts, and touched paths.
Accepted ideas must carry evidence links; candidates must keep their
`touched_paths` inside `edit_allowlist`.

## `human_review.yaml`

`human_review.yaml` is the only route to a true generated
`publication_approved` value. The file is human-authored and uses schema
`template-autoresearch-human-review-v1`:

- `publication_approved`: boolean, default `false`.
- `reviewer`: non-empty only for a true approval.
- `reviewed_at`: `null` unless `publication_approved: true`.
- `decisions`: review-gate decisions, each one of `approved`, `deferred`, or
  `rejected`.

Generated review packets and decisions may copy this state, but readiness alone
does not approve publication.

## `mnist_task.yaml`

`mnist_task.yaml` is the executable experiment contract. It declares the task
identifier, display name, local MNIST subset path, provenance path, seed,
metric direction, candidate budget, baseline, training defaults, and each
candidate model configuration. The
configured iteration budget decides how many candidates are evaluated; any
remaining candidates are written as deferred rather than executed later by an
autonomous process.

Training defaults and per-candidate overrides include batch size, epoch count,
learning rate, learning-rate decay, gradient-clipping norm, and L2 penalty. The
resolved values are serialized to `mnist_task_config.json`; epoch-level learning
rates and train/test metrics are serialized to `ml_training_history.csv`; and
best-epoch, final-rate, loss-reduction, and train-test gap summaries are
serialized to `ml_training_diagnostics.json`.

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

`src/ml_training.py` uses `numpy` only, with compatibility exports through
`src/ml_task.py`, `src/ml_data.py`, `src/ml_models.py`, and
`src/ml_selection.py`. It loads the local MNIST subset, evaluates a
nearest-centroid baseline, trains bounded neural candidates by deterministic
SGD or a fixed patch-attention representation plus softmax head, and selects
the best result with deterministic parameter-count tie-breaking. The task writes
`mnist_task_config.json`, `ml_task_results.json`, `ml_candidate_ledger.json`,
`ml_confusion_matrix.csv`, `ml_experiment_report.md`,
`ml_benchmark_score.json`, `ml_candidate_scores.png`,
`ml_confusion_matrix.png`, `ml_per_class_accuracy.png`,
`ml_training_history.csv`, `ml_error_examples.json`, `ml_learning_curves.png`,
`ml_complexity_accuracy.png`, `mnist_error_examples.png`,
`ml_prediction_records.json`, `ml_classification_diagnostics.json`,
`ml_candidate_intervals.json`, `ml_class_balance.json`,
`ml_calibration_report.json`, `ml_robustness_report.json`,
`ml_probability_diagnostics.json`, `ml_bootstrap_intervals.json`,
`ml_paired_comparison.json`, `ml_statistical_summary.json`,
`ml_training_diagnostics.json`, `ml_candidate_selection_audit.json`,
`ml_diagnostic_boundary.json`,
`ml_calibration_reliability.png`,
`ml_classification_metrics_heatmap.png`, `ml_confusion_pairs.png`,
`ml_generalization_gap.png`, `ml_robustness_matrix.png`,
`ml_probability_margin_distribution.png`, `ml_bootstrap_intervals.png`,
`ml_paired_correctness.png`, `ml_selective_accuracy.png`,
`ml_probability_quality.png`, `ml_training_dynamics.png`,
`autoresearch_candidate_lifecycle.png`,
`mnist_class_balance.png`, `mnist_subset_contact_sheet.png`, and final registry metadata through
`src.writers`.

`mnist_task.yaml` also configures the statistical diagnostic policy:
calibration bin count, deterministic bootstrap resamples and seed offset,
low-margin and high-confidence thresholds, selective-accuracy coverage
thresholds, and the no-retrain robustness transforms.

## Manuscript hydration and figures

`src.manuscript_variables` treats run-derived names, paths, metrics, figure
captions, and generated tables as validated variables. It reads the final
`autoresearch_loop.json`, ML result payload, candidate ledger, review decisions,
benchmark scores, artifact manifest, and figure registry. It then writes:

- `output/data/manuscript_variables.json`
- `output/data/manuscript_variable_provenance.json`
- `output/data/manuscript_figure_blocks.json`

Numbered manuscript files should use uppercase token placeholders for
run-derived facts. The hydration script rejects raw accepted-candidate IDs,
model labels, dataset labels, artifact paths, metric values, and registry
captions when they should be injected. Figure blocks are generated from
`output/figures/figure_registry.json`, so captions and image paths stay
synchronized with the final validated run.
The same registry records a generation method, validation hook, source artifact,
alt text, and claim boundary for each figure; manuscript hydration exposes those
records through a generated figure-method table.

The manuscript scholarship connects those local artifacts to FAIR data,
research-object packaging, Workflow Run RO-Crate provenance, Datasheets for
Datasets, Model Cards, zero-trust architecture, SSDF, SLSA, and ATT&CK supply
chain compromise. The project borrows the documentation and artifact-integrity
discipline, not the full packaging, signing, deployment, or monitoring
standards.

The manuscript also maintains `manuscript/source_ledger.yaml` with schema
`template-autoresearch-source-ledger-v1`. Each current-trends citation declares
`citekey`, `canonical_url`, `source_tier`, and `checked_as_of`. Tests and
`scripts/check_source_ledger.py` validate the ledger offline; they check shape,
HTTPS URLs, allowed source tiers, non-future ISO dates, BibTeX coverage, and
manuscript references without making live web calls.

## Security artifacts

`src.security` emits `autoresearch_security_profile.json`,
`autoresearch_threat_model.json`, `autoresearch_supply_chain_inventory.json`,
`autoresearch_inventory_export.json`, `autoresearch_integrity_attestation.json`,
`autoresearch_security_review.md`,
`autoresearch_security_control_matrix.png`, and
`autoresearch_integrity_chain.png`. The inventory is SBOM-style local metadata,
not SPDX or CycloneDX; the compact inventory export is still not a complete
dependency SBOM; and the attestation is local SHA-256 evidence, not Sigstore or
SLSA signed provenance.

## Scripts

- `scripts/run_autoresearch_loop.py` calls `src.loop.run_autoresearch_loop`.
- `scripts/check_source_ledger.py` validates `manuscript/source_ledger.yaml`
  offline and prints source-tier counts.
- `scripts/z_generate_manuscript_variables.py` calls
  `src.manuscript_variables` helpers, writes resolved manuscript files, and
  enforces strict tokenization for numbered manuscript sources.

## Validation phases

`validate_autoresearch_plan(..., phase=...)` supports:

- `intrinsic` — domain profile, experiment plan, pipeline contracts, thin
  orchestrators, AI-assisted disclosure
- `extrinsic` — evidence registry, artifact manifest, method ledgers, review
  decisions, benchmark grading outputs, and enabled security artifacts
  (post-write surfaces)
- `all` — default; runs every configured check

The readiness validator only checks local deterministic surfaces. It does not
execute pipeline stages or approve publication automatically.
