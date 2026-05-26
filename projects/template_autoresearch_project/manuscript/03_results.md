# Results {#sec:results}

## Candidate Outcome {#sec:candidate-outcome}

The generated loop selected `{{ACCEPTED_CANDIDATE_ID}}`
(`{{ACCEPTED_CANDIDATE_TITLE}}`, `{{ACCEPTED_MODEL_TYPE_LABEL}}`) after evaluating
`{{EVALUATED_CANDIDATE_COUNT}}` candidate(s) from a proposed set of
`{{CANDIDATE_COUNT}}`. The `{{BASELINE_ID}}`
(`{{BASELINE_MODEL_TYPE_LABEL}}`) baseline reached `{{BASELINE_ACCURACY}}`
`{{METRIC_NAME}}`, while the selected candidate reached `{{BEST_ACCURACY}}`, an
absolute change of `{{ACCURACY_DELTA}}`. The selected model has
`{{ACCEPTED_PARAMETER_COUNT}}` parameters. The transformer-candidate evaluated
flag is `{{TRANSFORMER_EVALUATED}}`, and the candidate budget exhausted flag is
`{{BUDGET_EXHAUSTED}}`, which means the ledger records
`{{DEFERRED_CANDIDATE_COUNT}}` deferred proposal(s) rather than expanding the run
automatically.

The benchmark score is `{{BENCHMARK_SCORE}}`. That score is not a model-quality
claim by itself; it is a compact grading artifact for the methods contract:
metric improvement, budget compliance, offline execution, and selected-candidate
recording. The candidate score figure is registered as
{{FIGURE_REF_CANDIDATE_SCORES}}, the confusion matrix as
{{FIGURE_REF_CONFUSION_MATRIX}}, the per-class diagnostic as
{{FIGURE_REF_PER_CLASS_ACCURACY}}, the learning curves as
{{FIGURE_REF_LEARNING_CURVES}}, the complexity diagnostic as
{{FIGURE_REF_COMPLEXITY_ACCURACY}}, the selected-candidate error examples as
{{FIGURE_REF_ERROR_EXAMPLES}}, the candidate lifecycle diagnostic as
{{FIGURE_REF_CANDIDATE_LIFECYCLE}}, the training-dynamics diagnostic as
{{FIGURE_REF_TRAINING_DYNAMICS}}, the final readiness matrix as
{{FIGURE_REF_STAGE_MATRIX}}, and the process closure as
{{FIGURE_REF_CLOSURE_FLOW}}.

{{CANDIDATE_INTERVAL_TABLE}}

## Run-Derived Figures {#sec:run-derived-figures}

{{FIGURE_BLOCK_CANDIDATE_SCORES}}

{{FIGURE_BLOCK_CONFUSION_MATRIX}}

{{FIGURE_BLOCK_PER_CLASS_ACCURACY}}

## Training And Error Diagnostics {#sec:training-error-diagnostics}

{{FIGURE_BLOCK_LEARNING_CURVES}}

{{FIGURE_BLOCK_TRAINING_DYNAMICS}}

{{FIGURE_BLOCK_COMPLEXITY_ACCURACY}}

{{FIGURE_BLOCK_ERROR_EXAMPLES}}

{{FIGURE_BLOCK_CANDIDATE_LIFECYCLE}}

The selected candidate's best held-out epoch is `{{ACCEPTED_BEST_EPOCH}}`, its
final learning rate is `{{ACCEPTED_FINAL_LEARNING_RATE}}`, its train-loss
reduction is `{{ACCEPTED_LOSS_REDUCTION}}`, and its final train-test accuracy
gap is `{{ACCEPTED_TRAIN_TEST_GAP}}`. These values come from the configured
training diagnostics rather than from a manually maintained result summary.

{{TRAINING_DIAGNOSTICS_TABLE}}

## Diagnostic Analysis {#sec:diagnostic-analysis}

The selected candidate macro F1 is `{{ACCEPTED_MACRO_F1}}`, with a held-out
accuracy interval of `{{ACCEPTED_ACCURACY_INTERVAL}}`. Probability diagnostics
report expected calibration error `{{ACCEPTED_CALIBRATION_ECE}}` and
`{{HIGH_CONFIDENCE_ERROR_COUNT}}` high-confidence error(s). The top
non-diagonal confusion pair is `{{TOP_CONFUSION_PAIR}}`, and the minimum
selected-candidate accuracy across deterministic robustness transforms is
`{{ROBUSTNESS_MIN_ACCURACY}}`. These values are descriptive diagnostics for the
validated local run, not external benchmark claims.

### Classification And Error Structure {#sec:classification-error-structure}

The class-level and error-pattern diagnostics are intentionally visual-first:
{{FIGURE_REF_CALIBRATION_RELIABILITY}} checks confidence calibration,
{{FIGURE_REF_CLASSIFICATION_METRICS}} separates precision, recall, and F1 by
digit, and {{FIGURE_REF_CONFUSION_PAIRS}} ranks the non-diagonal confusions
that most shape the selected-candidate error profile. The accompanying tables
preserve the same values for audit and downstream comparison.

{{FIGURE_BLOCK_CALIBRATION_RELIABILITY}}

{{FIGURE_BLOCK_CLASSIFICATION_METRICS}}

{{FIGURE_BLOCK_CONFUSION_PAIRS}}

{{CLASSIFICATION_DIAGNOSTICS_TABLE}}

{{CALIBRATION_BIN_TABLE}}

{{CONFUSION_PAIR_TABLE}}

### Uncertainty, Generalization, And Perturbation {#sec:uncertainty-generalization-perturbation}

Additional uncertainty and matched-comparison diagnostics report bootstrap
accuracy interval `{{BOOTSTRAP_ACCURACY_INTERVAL}}`, bootstrap macro-F1 interval
`{{BOOTSTRAP_MACRO_F1_INTERVAL}}`, paired net accuracy gain
`{{PAIRED_NET_GAIN}}`, exact McNemar p-value `{{MCNEMAR_P_VALUE}}`, mean
correct-prediction confidence `{{MEAN_CORRECT_CONFIDENCE}}`, mean error
confidence `{{MEAN_ERROR_CONFIDENCE}}`, and `{{LOW_MARGIN_COUNT}}` low-margin
selected-candidate prediction(s). These diagnostics are generated from the
fixed local test split and are reported as run evidence, not as population-level
certification.

{{FIGURE_REF_GENERALIZATION_GAP}} compares train and test behavior,
{{FIGURE_REF_ROBUSTNESS_MATRIX}} shows deterministic no-retrain perturbation
results, {{FIGURE_REF_PROBABILITY_MARGIN}} summarizes confidence and margin
distributions, {{FIGURE_REF_BOOTSTRAP_INTERVALS}} shows local resampling
intervals, and {{FIGURE_REF_PAIRED_CORRECTNESS}} exposes the matched
selected-versus-baseline correctness table used by the paired comparison.

{{FIGURE_BLOCK_GENERALIZATION_GAP}}

{{FIGURE_BLOCK_ROBUSTNESS_MATRIX}}

{{FIGURE_BLOCK_PROBABILITY_MARGIN}}

{{FIGURE_BLOCK_BOOTSTRAP_INTERVALS}}

{{FIGURE_BLOCK_PAIRED_CORRECTNESS}}

{{ROBUSTNESS_SCORE_TABLE}}

{{PROBABILITY_DIAGNOSTICS_TABLE}}

{{BOOTSTRAP_INTERVAL_TABLE}}

{{PAIRED_COMPARISON_TABLE}}

### Probability Quality And Selective Prediction {#sec:probability-quality-selective-prediction}

Probability-quality diagnostics report Brier score `{{ACCEPTED_BRIER_SCORE}}`,
negative log likelihood `{{ACCEPTED_NEGATIVE_LOG_LIKELIHOOD}}`, top-2 accuracy
`{{ACCEPTED_TOP2_ACCURACY}}`, and Cohen kappa `{{ACCEPTED_COHEN_KAPPA}}` for the
selected candidate. At the highest configured confidence threshold, retained
coverage is `{{SELECTIVE_HIGH_CONFIDENCE_COVERAGE}}` and selective accuracy is
`{{SELECTIVE_HIGH_CONFIDENCE_ACCURACY}}`.

The selective-prediction view in {{FIGURE_REF_SELECTIVE_ACCURACY}} reports the
configured confidence-threshold trade-off: retaining fewer predictions can raise
selective accuracy, but the coverage table keeps that trade-off explicit. The
candidate probability-quality comparison in {{FIGURE_REF_PROBABILITY_QUALITY}}
keeps accuracy separate from proper-score behavior, so the selected candidate is
not treated as automatically best on every diagnostic axis.

{{FIGURE_BLOCK_SELECTIVE_ACCURACY}}

{{FIGURE_BLOCK_PROBABILITY_QUALITY}}

{{STATISTICAL_SUMMARY_TABLE}}

{{SELECTIVE_ACCURACY_TABLE}}

{{PROBABILITY_QUALITY_TABLE}}

## Candidate Ledger {#sec:candidate-ledger}

{{ML_CANDIDATE_LEDGER_TABLE}}

The candidate-selection audit separates the objective ranking from descriptive
diagnostics. It records the configured metric, Wilson interval, probability
quality, parameter count, and deterministic tie-break context for each
evaluated candidate. The diagnostic-boundary table states what each generated
surface supports and what it does not support.

{{CANDIDATE_SELECTION_AUDIT_TABLE}}

{{DIAGNOSTIC_BOUNDARY_TABLE}}

## Readiness And Review Artifacts {#sec:readiness-review-artifacts}

The broader AutoResearch run writes the reproducibility, benchmark, review, and
manuscript-hydration surfaces summarized below.

{{FIGURE_BLOCK_STAGE_MATRIX}}

{{FIGURE_BLOCK_CLOSURE_FLOW}}

{{AUTORESEARCH_ARTIFACT_TABLE}}

{{REVIEW_GATE_TABLE}}

{{BENCHMARK_SCORE_TABLE}}

## Security Readiness And Integrity Evidence {#sec:security-readiness-integrity}

The local security profile reports attestation status
`{{SECURITY_ATTESTATION_STATUS}}` after checking
`{{SECURITY_ATTESTATION_CHECKED_COUNT}}` file record(s), with
`{{SECURITY_ATTESTATION_MISSING_COUNT}}` missing record(s) and
`{{SECURITY_ATTESTATION_MISMATCH_COUNT}}` checksum mismatch(es). The inventory
contains `{{SECURITY_INVENTORY_INPUT_COUNT}}` input record(s) and
`{{SECURITY_INVENTORY_ARTIFACT_COUNT}}` generated-artifact record(s). The
integrity-chain figure is {{FIGURE_REF_INTEGRITY_CHAIN}}. These values support
local artifact-integrity claims only; they do not claim external signing,
production SLSA compliance, or runtime security monitoring.

{{FIGURE_BLOCK_INTEGRITY_CHAIN}}

{{SECURITY_INTEGRITY_TABLE}}

## Manuscript Hydration Provenance {#sec:manuscript-hydration-provenance}

The final run supports `{{SUPPORTED_CLAIM_COUNT}}` manuscript-facing claim(s)
and checks `{{REQUIRED_ARTIFACT_COUNT}}` required artifact(s). The rendered
manuscript uses injected variables from generated data payloads, so the abstract
and results track the latest analysis run rather than hard-coded counts. The
final readiness status is `{{READINESS_STATUS}}`; generated review decisions are
recorded as deferred for human review rather than as self-approval.

{{VARIABLE_PROVENANCE_TABLE}}
