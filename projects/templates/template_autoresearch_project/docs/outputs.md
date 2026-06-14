# Outputs

Running `template_autoresearch_project` creates machine-readable data,
human-readable reports, registry-backed figures, manuscript variables,
variable provenance, and review material.

How these artifacts are *validated* (which gates bind their truth, which are hard
gates vs. opt-in) is documented in [validation-architecture.md](validation-architecture.md).
The integrity attestation and research-object manifest now surface present-but-empty
artifacts (`empty` / `empty_artifact_count`); the schema manifest fails the run on a
nonconforming governance payload.

Core data:

| Path | Role |
| --- | --- |
| `output/data/autoresearch_plan.json` | Composed plan from project profile, experiment plan, and pipeline DAG |
| `output/data/autoresearch_loop.json` | Full loop payload with config, stages, claims, metrics, and paths |
| `output/data/autoresearch_claims.json` | Evidence-grounded generated claims |
| `output/data/autoresearch_stage_matrix.csv` | Tabular stage status for spreadsheet review (`status` is `declared`, not execution proof) |
| `output/data/autoresearch_review_packet.json` | Machine-readable human review packet |
| `output/data/autoresearch_evidence_overview.json` | Reviewer-facing overview of readiness vs. approval, claim evidence, source-ledger freshness, benchmark boundary, and security/integrity status |
| `output/data/research_program.json` | Human-authored research program, autonomy level, budget, and edit allowlist |
| `output/data/idea_ledger.json` | Proposed, accepted, rejected, and deferred research ideas plus candidates |
| `output/data/run_ledger.json` | Replay ledger with budget use and stop condition |
| `output/data/review_decisions.json` | Required human review gate decisions |
| `output/data/benchmark_scores.json` | Benchmark-style grading status for configured tasks |
| `output/data/benchmark_boundary.json` | Fixture, metric-direction, candidate-budget, statistical-method, and non-claim boundary for benchmark-adjacent diagnostics |
| `output/data/mnist_task_config.json` | Resolved local MNIST dataset, baseline, training, and candidate-search configuration |
| `output/data/ml_task_results.json` | MNIST subset summary, baseline, candidates, accepted candidate, and metric delta |
| `output/data/ml_candidate_ledger.json` | Candidate lifecycle ledger with proposed, evaluated, accepted, rejected, and deferred states |
| `output/data/ml_confusion_matrix.csv` | Accepted-candidate confusion matrix over the local test split |
| `output/data/ml_training_history.csv` | Epoch-level train/test accuracy and loss for evaluated candidates |
| `output/data/ml_error_examples.json` | Accepted-candidate test-set error examples for qualitative review |
| `output/data/ml_prediction_records.json` | Per-candidate probability, confidence, margin, prediction, and correctness records |
| `output/data/ml_classification_diagnostics.json` | Accepted-candidate class metrics, confusion pairs, confidence interval, and train/test gaps |
| `output/data/ml_candidate_intervals.json` | Baseline and evaluated-candidate Wilson accuracy intervals |
| `output/data/ml_class_balance.json` | Train/test class counts for the local offline MNIST fixture |
| `output/data/ml_calibration_report.json` | Accepted-candidate calibration bins, expected calibration error, and high-confidence errors |
| `output/data/ml_calibration_bin_intervals.json` | Wilson intervals for empirical accuracy inside each calibration bin, including empty-bin markers |
| `output/data/ml_robustness_report.json` | Deterministic no-retrain perturbation scores for evaluated candidates |
| `output/data/ml_probability_diagnostics.json` | Accepted-candidate confidence, margin, entropy, and correctness histogram diagnostics |
| `output/data/ml_bootstrap_intervals.json` | Deterministic bootstrap intervals for accepted-candidate accuracy and macro F1 |
| `output/data/ml_paired_comparison.json` | Matched baseline-vs-accepted correctness counts and exact McNemar summary |
| `output/data/ml_statistical_summary.json` | Accepted-candidate Brier, NLL, top-2, kappa, selective-accuracy, and candidate probability-quality summary |
| `output/data/ml_training_diagnostics.json` | Configured learning-rate, gradient-clipping, best-epoch, loss-reduction, and train-test gap diagnostics |
| `output/data/ml_candidate_rank_stability.json` | Deterministic bootstrap rank-stability frequencies and accepted-vs-runner-up delta interval |
| `output/data/ml_candidate_selection_audit.json` | Candidate ranking audit with objective metric, Wilson interval, probability quality, parameters, and tie-break context |
| `output/data/ml_diagnostic_boundary.json` | Generated claim-boundary table separating objective selection, diagnostics, robustness, integrity, and review governance |
| `output/data/autoresearch_phase_ledger.json` | Ordered loop-settlement ledger for intrinsic checks, artifact writes, readiness settlement, and final manifests |
| `output/data/figure_quality_report.json` | Local checks for generated figures: registry binding, source-data substance (non-empty/parseable), nonblank pixels, alt text, and dimensions |
| `output/data/figure_style.json` | Style provenance for the run — dpi, colormaps, fonts, and resolved colour palette used to render every figure (schema `template-autoresearch-figure-style-v1`; configured via `figures.yaml`) |
| `output/data/autoresearch_security_profile.json` | Local deterministic security profile, network policy, integrity algorithm, framework labels, and explicit non-claims |
| `output/data/autoresearch_threat_model.json` | STRIDE and ATT&CK-scoped local artifact threat model with assets, threats, controls, and residual risks |
| `output/data/autoresearch_supply_chain_inventory.json` | SBOM-style local input and generated-artifact inventory with SHA-256 hashes |
| `output/data/autoresearch_inventory_export.json` | Compact local inventory export; not a complete dependency SBOM or CycloneDX claim |
| `output/data/autoresearch_integrity_attestation.json` | Local checksum attestation over required inventory records |
| `output/data/autoresearch_schema_manifest.json` | Schema-version manifest for generated JSON governance payloads, with explicit generic-table exemptions |
| `output/data/research_object_manifest.json` | Local research-object manifest with project paths, checksums, source ledger, schema manifest, and approval state |
| `output/data/manuscript_variables.json` | Variables injected into the manuscript |
| `output/data/manuscript_variable_provenance.json` | Source artifact and JSON-pointer mapping for injected variables and fragments |
| `output/data/manuscript_figure_blocks.json` | Registry-backed Pandoc figure blocks inserted into the hydrated manuscript |

Figures:

| Path | Role |
| --- | --- |
| `output/figures/autoresearch_stage_matrix.png` | Visual stage, claim, and artifact readiness matrix |
| `output/figures/ml_candidate_scores.png` | Baseline and evaluated-candidate test accuracy chart |
| `output/figures/ml_confusion_matrix.png` | Accepted-candidate confusion matrix figure |
| `output/figures/ml_per_class_accuracy.png` | Per-class diagnostic derived from the accepted-candidate confusion matrix |
| `output/figures/ml_learning_curves.png` | Candidate held-out accuracy curves over training epochs |
| `output/figures/ml_complexity_accuracy.png` | Parameter-count versus held-out accuracy diagnostic |
| `output/figures/mnist_error_examples.png` | Accepted-candidate error example grid from the local test split |
| `output/figures/ml_calibration_reliability.png` | Reliability curve and confidence-bin count diagnostic |
| `output/figures/ml_classification_metrics_heatmap.png` | Per-class precision, recall, and F1 heatmap |
| `output/figures/ml_confusion_pairs.png` | Ranked non-diagonal confusion-pair chart |
| `output/figures/ml_generalization_gap.png` | Train/test accuracy and loss comparison by evaluated candidate |
| `output/figures/ml_robustness_matrix.png` | Candidate accuracy under deterministic identity, shift, and low-contrast transforms |
| `output/figures/ml_probability_margin_distribution.png` | Confidence and prediction-margin distributions by correctness |
| `output/figures/ml_bootstrap_intervals.png` | Deterministic bootstrap interval chart for accepted-candidate metrics |
| `output/figures/ml_paired_correctness.png` | Matched accepted-vs-baseline correctness heatmap |
| `output/figures/ml_selective_accuracy.png` | Coverage versus selective accuracy at configured confidence thresholds |
| `output/figures/ml_probability_quality.png` | Candidate Brier score and negative log likelihood comparison |
| `output/figures/ml_training_dynamics.png` | Final versus best-epoch accuracy and train-test gap chart for evaluated candidates |
| `output/figures/ml_candidate_rank_stability.png` | Bootstrap top-rank frequency and mean-rank diagnostic for evaluated candidates |
| `output/figures/autoresearch_candidate_lifecycle.png` | Candidate lifecycle counts from the proposal and candidate ledger |
| `output/figures/mnist_class_balance.png` | Train/test class-count diagnostic for the local MNIST fixture |
| `output/figures/mnist_subset_contact_sheet.png` | Deterministic contact sheet from the local fixed data subset and provenance file |
| `output/figures/autoresearch_closure_flow.png` | File-backed research-process closure figure |
| `output/figures/autoresearch_security_control_matrix.png` | Local security control matrix generated from the threat model |
| `output/figures/autoresearch_integrity_chain.png` | Local checksum integrity-chain figure generated from the attestation |
| `output/figures/figure_registry.json` | Registered figure metadata, captions with generation-method sentences, source artifacts, validation hooks, alt text, and claim boundaries |

Reports:

| Path | Role |
| --- | --- |
| `output/reports/autoresearch_loop.json` | Report copy of the loop payload |
| `output/reports/autoresearch_loop.md` | Human-readable loop report |
| `output/reports/autoresearch_review_packet.md` | Human review packet with required actions |
| `output/reports/autoresearch_evidence_overview.md` | Reviewer-facing markdown summary that preserves the readiness/approval boundary and surfaces source-ledger or benchmark-boundary issues |
| `output/reports/autoresearch_summary.md` | Short project summary |
| `output/reports/autoresearch_security_review.md` | Adversarial local security review packet for human assessment |
| `output/reports/ml_experiment_report.md` | Human-readable deterministic ML-loop report |
| `output/reports/ml_benchmark_score.json` | Grading output for metric improvement, budget compliance, offline execution, and selection status |
| `output/reports/autoresearch_readiness.json` | Structured readiness validation result |
| `output/reports/autoresearch_readiness.md` | Human-readable readiness validation result |
| `output/reports/benchmark_readiness_smoke.json` | Measured readiness grade (auto-graded): fraction of checks passing — core artifacts substantive, ≥1 supported claim, ML accuracy improved over baseline; scores below 1.0 and is flagged `incomplete` on a hollow/degraded run |
| `output/reports/evidence_registry.json` | Compact evidence-registry summary with fact counts, source tiers, freshness warnings, and a bounded fact sample |
| `output/reports/artifact_manifest.json` | Artifact manifest with sizes and checksums |

Pipeline rendering also produces manuscript, PDF, HTML, and slide outputs when
the standard `run.sh` path reaches render and copy stages.

The evidence-registry validator still builds the complete in-memory registry
for manuscript checks. The default report is compact to keep reviewer artifacts
small; set `TEMPLATE_EVIDENCE_REGISTRY_FULL=1` only for local debugging to emit
`output/reports/evidence_registry_full.json`, which is not a required artifact.
