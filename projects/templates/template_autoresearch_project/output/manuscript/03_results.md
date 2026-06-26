# Results {#sec:results}

## Candidate Outcome {#sec:candidate-outcome}

The generated loop selected `exp-mlp-tanh-64`
(`One-hidden-layer tanh MLP`, `MLP`) after evaluating
`4` candidate(s) from a proposed set of
`5`. The `nearest_centroid_baseline`
(`nearest-centroid`) baseline reached `82.6%`
`test_accuracy`, while the selected candidate reached `89.4%`, an
absolute change of `6.8%`. The selected model has
`50890` parameters. The transformer-candidate evaluated
flag is `true`, and the candidate budget exhausted flag is
`true`, which means the ledger records
`1` deferred proposal(s) rather than expanding the run
automatically.

The benchmark score is `1`. That score is not a model-quality
claim by itself; it is a compact grading artifact for the methods contract:
metric improvement, budget compliance, offline execution, and selected-candidate
recording. Rank-stability diagnostics report that the selected candidate is top
ranked in `72.5%` of deterministic bootstrap
resamples, with runner-up `exp-mlp-relu-32`. The candidate
score figure is registered as
@fig:ml_candidate_scores, the confusion matrix as
@fig:ml_confusion_matrix, the per-class diagnostic as
@fig:ml_per_class_accuracy, the learning curves as
@fig:ml_learning_curves, the complexity diagnostic as
@fig:ml_complexity_accuracy, the selected-candidate error examples as
@fig:mnist_error_examples, the candidate lifecycle diagnostic as
@fig:autoresearch_candidate_lifecycle, rank stability as
@fig:ml_candidate_rank_stability, the training-dynamics diagnostic as
@fig:ml_training_dynamics, the final readiness matrix as
@fig:autoresearch_stage_matrix, and the process closure as
@fig:autoresearch_closure_flow.

| Candidate | Status | Correct/test | Accuracy | Wilson 95% interval |
| --- | --- | --- | --- | --- |
| baseline | baseline | 413/500 | 82.6% | 79.0% to 85.7% |
| softmax linear | rejected | 441/500 | 88.2% | 85.1% to 90.7% |
| mlp relu 32 | rejected | 443/500 | 88.6% | 85.5% to 91.1% |
| tiny patch attention | rejected | 152/500 | 30.4% | 26.5% to 34.6% |
| mlp tanh 64 | accepted | 447/500 | 89.4% | 86.4% to 91.8% |

: Candidate accuracy intervals from `output/data/ml_candidate_intervals.json`; intervals describe the fixed local test split. {#tbl:candidate-intervals}

| Candidate | Observed rank | Top-rank frequency | Mean rank | Accuracy |
| --- | --- | --- | --- | --- |
| softmax linear | 3 | 4.2% | 2.554 | 88.2% |
| mlp relu 32 | 2 | 23.3% | 2.130 | 88.6% |
| tiny patch attention | 4 | 0.0% | 4.000 | 30.4% |
| mlp tanh 64 | 1 | 72.5% | 1.316 | 89.4% |

: Candidate rank-stability table from `output/data/ml_candidate_rank_stability.json`; frequencies are deterministic local bootstrap summaries. {#tbl:candidate-rank-stability}

## Run-Derived Figures {#sec:run-derived-figures}

![Held-out accuracy with Wilson intervals for the baseline and evaluated candidates from output/data/ml_candidate_intervals.json; accepted candidate exp-mlp-tanh-64 improves accuracy from 82.6% to 89.4% on the fixed subset, with deferred proposals kept in the candidate ledger. Generation method: Lollipop accuracy comparison with Wilson interval error bars and direct labels. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_candidate_scores.png){#fig:ml_candidate_scores width="0.8\textwidth"}

![Rank-stability summary for exp-mlp-tanh-64 from output/data/ml_candidate_rank_stability.json; deterministic local bootstrap resampling shows how often each evaluated candidate ranks first under the fixed test split. Generation method: Bootstrap top-rank frequency and mean-rank comparison. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_candidate_rank_stability.png){#fig:ml_candidate_rank_stability width="0.82\textwidth"}

![Accepted-candidate confusion matrix for exp-mlp-tanh-64 on the fixed MNIST handwritten digit database test split, sourced from output/data/ml_confusion_matrix.csv; it diagnoses the selected run, not general full-dataset performance. Generation method: Row-normalized heatmap with cell counts and row percentages. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_confusion_matrix.png){#fig:ml_confusion_matrix width="0.72\textwidth"}

![Per-class accuracy for exp-mlp-tanh-64, computed from output/data/ml_confusion_matrix.csv; variation across digits is a run diagnostic for the fixed local test split. Generation method: Per-class accuracy bars computed from the confusion matrix diagonal. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_per_class_accuracy.png){#fig:ml_per_class_accuracy width="0.78\textwidth"}

## Training And Error Diagnostics {#sec:training-error-diagnostics}

![Epoch-level held-out accuracy curves for evaluated candidates from output/data/ml_training_history.csv; the accepted curve is visually emphasized for exp-mlp-tanh-64. Generation method: Epoch-level held-out accuracy lines with accepted best-epoch marker. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_learning_curves.png){#fig:ml_learning_curves width="0.82\textwidth"}

![Configured-training dynamics for evaluated candidates from output/data/ml_training_diagnostics.json; exp-mlp-tanh-64 is highlighted while best-epoch markers and train-test gaps remain bounded to the local run. Generation method: Final and best-epoch accuracy bars plus train-test gap bars. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_training_dynamics.png){#fig:ml_training_dynamics width="0.84\textwidth"}

![Parameter-count versus held-out accuracy for the baseline and evaluated candidates from output/data/ml_task_results.json; the accepted candidate is highlighted without claiming a general scaling law. Generation method: Log-parameter scatter plot against held-out accuracy. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_complexity_accuracy.png){#fig:ml_complexity_accuracy width="0.78\textwidth"}

![First accepted-candidate error examples for exp-mlp-tanh-64, sourced from output/data/ml_error_examples.json and data/mnist_small.npz; these images support qualitative diagnosis only. Generation method: Deterministic grid of the first accepted-candidate misclassifications. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/mnist_error_examples.png){#fig:mnist_error_examples width="0.82\textwidth"}

![Candidate lifecycle ledger from output/data/ml_candidate_ledger.json: 4 evaluated out of 5 proposed candidates, with deferred proposals kept visible instead of executed automatically. Generation method: Candidate lifecycle status-count bar chart. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_candidate_lifecycle.png){#fig:autoresearch_candidate_lifecycle width="0.78\textwidth"}

The selected candidate's best held-out epoch is `14`, its
final learning rate is `0.144`, its train-loss
reduction is `4.161`, and its final train-test accuracy
gap is `7.0%`. These values come from the configured
training diagnostics rather than from a manually maintained result summary.

| Candidate | Status | Best epoch | Best test accuracy | Final test accuracy | Train-test gap | Loss reduction | Final learning rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| softmax linear | rejected | 17 | 89.4% | 88.2% | 5.9% | 2.917 | 0.273 |
| mlp relu 32 | rejected | 21 | 90.0% | 88.6% | 8.5% | 4.341 | 0.178 |
| tiny patch attention | rejected | 24 | 30.4% | 30.4% | -1.8% | 0.165 | 0.214 |
| mlp tanh 64 | accepted | 14 | 90.0% | 89.4% | 7.0% | 4.161 | 0.144 |

: Configured-training diagnostics from `output/data/ml_training_diagnostics.json`. {#tbl:training-diagnostics}

## Diagnostic Analysis {#sec:diagnostic-analysis}

The selected candidate macro F1 is `89.4%`, with a held-out
accuracy interval of `86.4% to 91.8%`. Probability diagnostics
report expected calibration error `2.9%` and
`11` high-confidence error(s). The top
non-diagonal confusion pair is `4 -> 9 (4)`, and the minimum
selected-candidate accuracy across deterministic robustness transforms is
`80.0%`. These values are descriptive diagnostics for the
validated local run, not external benchmark claims.

### Classification And Error Structure {#sec:classification-error-structure}

The class-level and error-pattern diagnostics are intentionally visual-first:
@fig:ml_calibration_reliability checks confidence calibration,
@fig:ml_classification_metrics_heatmap separates precision, recall, and F1 by
digit, and @fig:ml_confusion_pairs ranks the non-diagonal confusions
that most shape the selected-candidate error profile. The accompanying tables
preserve the same values for audit and downstream comparison.

![Reliability curve for exp-mlp-tanh-64 from output/data/ml_calibration_report.json; expected calibration error and bin counts summarize the accepted candidate on the fixed local test split. Generation method: Reliability curve with confidence-bin support histogram. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_calibration_reliability.png){#fig:ml_calibration_reliability width="0.82\textwidth"}

![Per-class precision, recall, and F1 for exp-mlp-tanh-64, sourced from output/data/ml_classification_diagnostics.json; metrics are scoped to the local test split. Generation method: Per-class precision, recall, and F1 heatmap. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_classification_metrics_heatmap.png){#fig:ml_classification_metrics_heatmap width="0.76\textwidth"}

![Top non-diagonal confusion pairs for exp-mlp-tanh-64, sourced from output/data/ml_classification_diagnostics.json; the bars highlight which local digit pairs account for accepted-candidate errors. Generation method: Ranked off-diagonal confusion-pair bars with true-class error rates. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_confusion_pairs.png){#fig:ml_confusion_pairs width="0.82\textwidth"}

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| 0 | 94.1% | 96.0% | 95.0% | 50 |
| 1 | 98.0% | 98.0% | 98.0% | 50 |
| 2 | 90.7% | 78.0% | 83.9% | 50 |
| 3 | 90.0% | 90.0% | 90.0% | 50 |
| 4 | 83.6% | 92.0% | 87.6% | 50 |
| 5 | 86.3% | 88.0% | 87.1% | 50 |
| 6 | 97.8% | 88.0% | 92.6% | 50 |
| 7 | 88.7% | 94.0% | 91.3% | 50 |
| 8 | 79.6% | 78.0% | 78.8% | 50 |
| 9 | 86.8% | 92.0% | 89.3% | 50 |

: Accepted-candidate class diagnostics from `output/data/ml_classification_diagnostics.json`. {#tbl:classification-diagnostics}

| Confidence bin | Count | Accuracy | Mean confidence | Gap |
| --- | --- | --- | --- | --- |
| 0-0.1 | 0 | 0.0% | 0.0% | 0.0% |
| 0.1-0.2 | 0 | 0.0% | 0.0% | 0.0% |
| 0.2-0.3 | 3 | 0.0% | 27.2% | 27.2% |
| 0.3-0.4 | 4 | 75.0% | 35.0% | 40.0% |
| 0.4-0.5 | 21 | 42.9% | 45.7% | 2.9% |
| 0.5-0.6 | 28 | 67.9% | 55.4% | 12.5% |
| 0.6-0.7 | 24 | 66.7% | 65.0% | 1.7% |
| 0.7-0.8 | 28 | 67.9% | 75.6% | 7.7% |
| 0.8-0.9 | 53 | 90.6% | 85.8% | 4.8% |
| 0.9-1 | 339 | 98.2% | 97.4% | 0.8% |

: Calibration bins from `output/data/ml_calibration_report.json`. {#tbl:calibration-bins}

| Confidence bin | Count | Correct | Accuracy | Wilson 95% | Empty |
| --- | --- | --- | --- | --- | --- |
| 0-0.1 | 0 | 0 | 0.0% | 0.0% to 0.0% | True |
| 0.1-0.2 | 0 | 0 | 0.0% | 0.0% to 0.0% | True |
| 0.2-0.3 | 3 | 0 | 0.0% | 0.0% to 56.2% | False |
| 0.3-0.4 | 4 | 3 | 75.0% | 30.1% to 95.4% | False |
| 0.4-0.5 | 21 | 9 | 42.9% | 24.5% to 63.5% | False |
| 0.5-0.6 | 28 | 19 | 67.9% | 49.3% to 82.1% | False |
| 0.6-0.7 | 24 | 16 | 66.7% | 46.7% to 82.0% | False |
| 0.7-0.8 | 28 | 19 | 67.9% | 49.3% to 82.1% | False |
| 0.8-0.9 | 53 | 48 | 90.6% | 79.7% to 95.9% | False |
| 0.9-1 | 339 | 333 | 98.2% | 96.2% to 99.2% | False |

: Calibration-bin Wilson intervals from `output/data/ml_calibration_bin_intervals.json`; empty bins are reported explicitly. {#tbl:calibration-bin-intervals}

| Pair | Count | True-class error rate |
| --- | --- | --- |
| 4 -> 9 | 4 | 8.0% |
| 8 -> 5 | 4 | 8.0% |
| 2 -> 4 | 3 | 6.0% |
| 2 -> 7 | 3 | 6.0% |
| 5 -> 8 | 3 | 6.0% |
| 6 -> 4 | 3 | 6.0% |
| 2 -> 8 | 2 | 4.0% |
| 3 -> 2 | 2 | 4.0% |
| 3 -> 8 | 2 | 4.0% |
| 5 -> 3 | 2 | 4.0% |

: Top non-diagonal confusion pairs from `output/data/ml_classification_diagnostics.json`. {#tbl:confusion-pairs}

### Uncertainty, Generalization, And Perturbation {#sec:uncertainty-generalization-perturbation}

Additional uncertainty and matched-comparison diagnostics report bootstrap
accuracy interval `86.4% to 92.0%`, bootstrap macro-F1 interval
`86.5% to 91.9%`, paired net accuracy gain
`6.8%`, exact McNemar p-value `0.000`, mean
correct-prediction confidence `90.9%`, mean error
confidence `63.1%`, and `22` low-margin
selected-candidate prediction(s). These diagnostics are generated from the
fixed local test split and are reported as run evidence, not as population-level
certification.

@fig:ml_generalization_gap compares train and test behavior,
@fig:ml_robustness_matrix shows deterministic no-retrain perturbation
results, @fig:ml_probability_margin_distribution summarizes confidence and margin
distributions, @fig:ml_bootstrap_intervals shows local resampling
intervals, and @fig:ml_paired_correctness exposes the matched
selected-versus-baseline correctness table used by the paired comparison.

![Train/test accuracy and loss for evaluated candidates from output/data/ml_classification_diagnostics.json; the plot exposes local generalization gaps without claiming full-dataset behavior. Generation method: Grouped train/test accuracy and loss bars by evaluated candidate. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_generalization_gap.png){#fig:ml_generalization_gap width="0.82\textwidth"}

![Accuracy for evaluated candidates under identity, one-pixel shifts, and low contrast from output/data/ml_robustness_report.json; the deterministic transforms provide a bounded smoke test only. Generation method: Candidate-by-transform accuracy heatmap for deterministic perturbations. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_robustness_matrix.png){#fig:ml_robustness_matrix width="0.84\textwidth"}

![Confidence and prediction-margin histograms for exp-mlp-tanh-64 from output/data/ml_probability_diagnostics.json; the figure separates correct and incorrect local test predictions. Generation method: Confidence and margin histograms split by correctness. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_probability_margin_distribution.png){#fig:ml_probability_margin_distribution width="0.82\textwidth"}

![Deterministic percentile-bootstrap intervals for exp-mlp-tanh-64 from output/data/ml_bootstrap_intervals.json; the intervals summarize local sampling variation for accuracy and macro F1. Generation method: Horizontal percentile-bootstrap interval plot. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_bootstrap_intervals.png){#fig:ml_bootstrap_intervals width="0.78\textwidth"}

![Matched correctness comparison between exp-mlp-tanh-64 and the nearest_centroid_baseline baseline from output/data/ml_paired_comparison.json; discordant cells support the paired test summary. Generation method: Matched accepted-versus-baseline correctness heatmap. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_paired_correctness.png){#fig:ml_paired_correctness width="0.66\textwidth"}

| Candidate | Transform | Accuracy | Samples |
| --- | --- | --- | --- |
| softmax linear | identity | 88.2% | 500 |
| softmax linear | shift_right_1 | 81.4% | 500 |
| softmax linear | shift_down_1 | 78.6% | 500 |
| softmax linear | low_contrast_0_85 | 88.0% | 500 |
| mlp relu 32 | identity | 88.6% | 500 |
| mlp relu 32 | shift_right_1 | 82.4% | 500 |
| mlp relu 32 | shift_down_1 | 80.2% | 500 |
| mlp relu 32 | low_contrast_0_85 | 88.2% | 500 |
| tiny patch attention | identity | 30.4% | 500 |
| tiny patch attention | shift_right_1 | 29.8% | 500 |
| tiny patch attention | shift_down_1 | 25.8% | 500 |
| tiny patch attention | low_contrast_0_85 | 24.6% | 500 |
| mlp tanh 64 | identity | 89.4% | 500 |
| mlp tanh 64 | shift_right_1 | 83.2% | 500 |
| mlp tanh 64 | shift_down_1 | 80.0% | 500 |
| mlp tanh 64 | low_contrast_0_85 | 89.8% | 500 |

: Deterministic no-retrain robustness smoke test from `output/data/ml_robustness_report.json`. {#tbl:robustness-scores}

| Statistic | Value |
| --- | --- |
| Mean confidence | 87.9% |
| Mean correct confidence | 90.9% |
| Mean error confidence | 63.1% |
| Mean margin | 80.2% |
| Mean correct margin | 84.9% |
| Mean error margin | 40.3% |
| Low-margin count | 22 |

: Accepted-candidate probability diagnostics from `output/data/ml_probability_diagnostics.json`. {#tbl:probability-diagnostics}

| Metric | Observed | CI low | CI high | Resample mean |
| --- | --- | --- | --- | --- |
| accuracy | 89.4% | 86.4% | 92.0% | 89.4% |
| macro F1 | 89.4% | 86.5% | 91.9% | 89.3% |

: Deterministic percentile-bootstrap intervals from `output/data/ml_bootstrap_intervals.json`. {#tbl:bootstrap-intervals}

| Matched comparison statistic | Value |
| --- | --- |
| Both correct | 403 |
| Accepted only correct | 44 |
| Baseline only correct | 10 |
| Both wrong | 43 |
| Discordant examples | 54 |
| Exact McNemar p | 0.000 |
| Net accuracy gain | 6.8% |

: Accepted-candidate versus baseline paired comparison from `output/data/ml_paired_comparison.json`. {#tbl:paired-comparison}

### Probability Quality And Selective Prediction {#sec:probability-quality-selective-prediction}

Probability-quality diagnostics report Brier score `0.161`,
negative log likelihood `0.361`, top-2 accuracy
`95.6%`, and Cohen kappa `0.882` for the
selected candidate. At the highest configured confidence threshold, retained
coverage is `67.8%` and selective accuracy is
`98.2%`.

The selective-prediction view in @fig:ml_selective_accuracy reports the
configured confidence-threshold trade-off: retaining fewer predictions can raise
selective accuracy, but the coverage table keeps that trade-off explicit. The
candidate probability-quality comparison in @fig:ml_probability_quality
keeps accuracy separate from proper-score behavior, so the selected candidate is
not treated as automatically best on every diagnostic axis.

![Confidence-threshold trade-off for exp-mlp-tanh-64 from output/data/ml_statistical_summary.json; the plot compares retained coverage, selective accuracy, and the unthresholded accepted-candidate accuracy on the fixed local split. Generation method: Confidence-threshold coverage and selective-accuracy line chart. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_selective_accuracy.png){#fig:ml_selective_accuracy width="0.76\textwidth"}

![Brier score and negative log likelihood for evaluated candidates from output/data/ml_statistical_summary.json; lower values indicate better probability quality within the configured local run, and the accepted candidate is highlighted. Generation method: Brier score and negative-log-likelihood bar comparison. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_probability_quality.png){#fig:ml_probability_quality width="0.82\textwidth"}

| Statistic | Value |
| --- | --- |
| Accuracy | 89.4% |
| Balanced accuracy | 89.4% |
| Macro F1 | 89.4% |
| Top-2 accuracy | 95.6% |
| Cohen kappa | 0.882 |
| Brier score | 0.161 |
| Negative log likelihood | 0.361 |
| Expected calibration error | 2.9% |

: Accepted-candidate statistical summary from `output/data/ml_statistical_summary.json`. {#tbl:statistical-summary}

| Confidence threshold | Coverage | Selective accuracy | Retained | Errors |
| --- | --- | --- | --- | --- |
| 50.0% | 94.4% | 92.2% | 472 | 37 |
| 60.0% | 88.8% | 93.7% | 444 | 28 |
| 70.0% | 84.0% | 95.2% | 420 | 20 |
| 80.0% | 78.4% | 97.2% | 392 | 11 |
| 90.0% | 67.8% | 98.2% | 339 | 6 |

: Selective-accuracy threshold table from `output/data/ml_statistical_summary.json`. {#tbl:selective-accuracy}

| Candidate | Accuracy | Top-2 accuracy | Brier | NLL | Mean confidence |
| --- | --- | --- | --- | --- | --- |
| softmax linear | 88.2% | 95.8% | 0.173 | 0.390 | 85.1% |
| mlp relu 32 | 88.6% | 95.6% | 0.164 | 0.380 | 89.9% |
| tiny patch attention | 30.4% | 46.6% | 0.873 | 2.179 | 13.1% |
| mlp tanh 64 | 89.4% | 95.6% | 0.161 | 0.361 | 87.9% |

: Candidate probability-quality table from `output/data/ml_statistical_summary.json`. {#tbl:probability-quality}

## Candidate Ledger {#sec:candidate-ledger}

| Candidate | Model | Status | Test accuracy | Parameters |
| --- | --- | --- | --- | --- |
| baseline | nearest-centroid | baseline | 82.6% | 7840 |
| softmax linear | softmax regression | rejected | 88.2% | 7850 |
| mlp relu 32 | MLP | rejected | 88.6% | 25450 |
| tiny patch attention | tiny patch-attention | rejected | 30.4% | 5994 |
| mlp tanh 64 | MLP | accepted | 89.4% | 50890 |
| mlp relu 64 deferred | MLP | deferred | N/A | 0 |

: Candidate lifecycle ledger from `output/data/ml_candidate_ledger.json`. {#tbl:ml-candidate-ledger}

The candidate-selection audit separates the objective ranking from descriptive
diagnostics. It records the configured metric, Wilson interval, probability
quality, parameter count, and deterministic tie-break context for each
evaluated candidate. The diagnostic-boundary table states what each generated
surface supports and what it does not support.

| Rank | Candidate | Status | Accuracy | Wilson 95% | Brier | NLL | Parameters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mlp tanh 64 | accepted | 89.4% | 86.4% to 91.8% | 0.161 | 0.361 | 50890 |
| 2 | mlp relu 32 | rejected | 88.6% | 85.5% to 91.1% | 0.164 | 0.380 | 25450 |
| 3 | softmax linear | rejected | 88.2% | 85.1% to 90.7% | 0.173 | 0.390 | 7850 |
| 4 | tiny patch attention | rejected | 30.4% | 26.5% to 34.6% | 0.873 | 2.179 | 5994 |

: Candidate-selection audit from `output/data/ml_candidate_selection_audit.json`; the objective metric ranks candidates, while probability diagnostics and parameter counts audit the chosen tie-break context. {#tbl:candidate-selection-audit}

\begingroup\footnotesize
| Surface | Source | Method | Supports | Does not support |
| --- | --- | --- | --- | --- |
| objective selection | [task results](../data/ml_task_results.json) | rank evaluated candidates by configured held-out metric and deterministic tie... | accepted-candidate selection within this fixed local task | full MNIST state-of-the-art, external benchmark leadership, or universal mode... |
| descriptive diagnostics | [class diagnostics](../data/ml_classification_diagnostics.json) | per-class metrics, calibration, probability quality, and paired comparison | local error analysis and uncertainty description | population-level certification or deployment readiness |
| robustness smoke test | [robustness report](../data/ml_robustness_report.json) | deterministic no-retrain transforms applied to the fixed test split | small perturbation smoke-test evidence | adversarial robustness or distribution-shift robustness |
| artifact integrity | [integrity attestation](../data/autoresearch_integrity_attestation.json) | local SHA-256 checks over declared inputs and generated artifacts | local artifact integrity evidence for the run | external signing, production SLSA compliance, or runtime intrusion detection |
| review governance | [review decisions](../data/review_decisions.json) | deferred generated review decisions with human review required | readiness for human review | machine self-approval or publication acceptance |

: Diagnostic claim-boundary table from `output/data/ml_diagnostic_boundary.json`. {#tbl:diagnostic-boundary}
\endgroup

## Readiness And Review Artifacts {#sec:readiness-review-artifacts}

The broader AutoResearch run writes the reproducibility, benchmark, review, and
manuscript-hydration surfaces summarized below. The schema manifest records
`31` schema-versioned governance payload(s), and
the local research-object manifest records `84`
observed artifact record(s) with checksums and approval state
`false`. The phase ledger records
`3` settlement pass(es), while the
figure-quality report covers `25` registered
figure(s) with validity `false`.

![Validated AutoResearch run with 7 stages, 6 supported claims, and 78 required artifacts from output/data/autoresearch_loop.json; the count summarizes readiness artifacts, not human approval. Generation method: Horizontal count summary from final loop metrics. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_stage_matrix.png){#fig:autoresearch_stage_matrix width="0.8\textwidth"}

![File-backed AutoResearch closure from program through review, with 6 supported claims and readiness passed; review remains a deferred human decision and the provenance path remains inspectable. Generation method: File-backed process-flow diagram from final loop state. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_closure_flow.png){#fig:autoresearch_closure_flow width="0.95\textwidth"}

| Artifact | Role | Bytes |
| --- | --- | --- |
| output/data/autoresearch_claims.json | Loop artifact | 1766 |
| output/data/autoresearch_evidence_overview.json | Evidence registry | 4436 |
| output/data/autoresearch_integrity_attestation.json | Security evidence | 22755 |
| output/data/autoresearch_inventory_export.json | Security evidence | 20203 |
| output/data/autoresearch_loop.json | Loop artifact | 16085 |
| output/data/autoresearch_phase_ledger.json | Run or candidate ledger | 3779 |
| output/data/autoresearch_plan.json | Loop artifact | 17361 |
| output/data/autoresearch_review_packet.json | Review packet | 16204 |
| output/data/autoresearch_schema_manifest.json | Loop artifact | 7226 |
| output/data/autoresearch_security_profile.json | Security evidence | 1537 |
| output/data/autoresearch_stage_matrix.csv | Loop artifact | 749 |
| output/data/autoresearch_supply_chain_inventory.json | Security evidence | 21459 |
| output/data/autoresearch_threat_model.json | Security evidence | 6370 |
| output/data/benchmark_boundary.json | Benchmark grading | 2363 |
| output/data/benchmark_scores.json | Benchmark grading | 621 |
| output/data/figure_quality_report.json | Loop artifact | 16040 |
| output/data/figure_style.json | Loop artifact | 1117 |
| output/data/idea_ledger.json | Run or candidate ledger | 5233 |
| output/data/manuscript_figure_blocks.json | Manuscript hydration | 13062 |
| output/data/manuscript_variable_provenance.json | Manuscript hydration | 30891 |
| output/data/manuscript_variables.json | Manuscript hydration | 54968 |
| output/data/ml_bootstrap_intervals.json | Loop artifact | 615 |
| output/data/ml_calibration_bin_intervals.json | Loop artifact | 2879 |
| output/data/ml_calibration_report.json | Loop artifact | 2201 |
| output/data/ml_candidate_intervals.json | Loop artifact | 1577 |
| output/data/ml_candidate_ledger.json | Run or candidate ledger | 570872 |
| output/data/ml_candidate_rank_stability.json | Loop artifact | 3135 |
| output/data/ml_candidate_selection_audit.json | Loop artifact | 2145 |
| output/data/ml_class_balance.json | Loop artifact | 2393 |
| output/data/ml_classification_diagnostics.json | Loop artifact | 4246 |
| output/data/ml_confusion_matrix.csv | Loop artifact | 271 |
| output/data/ml_diagnostic_boundary.json | Loop artifact | 2064 |
| output/data/ml_error_examples.json | Loop artifact | 989 |
| output/data/ml_paired_comparison.json | Loop artifact | 470 |
| output/data/ml_prediction_records.json | Loop artifact | 989913 |
| output/data/ml_probability_diagnostics.json | Loop artifact | 3045 |
| output/data/ml_robustness_report.json | Loop artifact | 3758 |
| output/data/ml_statistical_summary.json | Loop artifact | 3032 |
| output/data/ml_task_results.json | Loop artifact | 703566 |
| output/data/ml_training_diagnostics.json | Loop artifact | 2968 |
| output/data/ml_training_history.csv | Loop artifact | 6775 |
| output/data/mnist_task_config.json | Loop artifact | 3926 |
| output/data/research_object_manifest.json | Loop artifact | 20789 |
| output/data/research_program.json | Loop artifact | 965 |
| output/data/review_decisions.json | Review packet | 669 |
| output/data/run_ledger.json | Run or candidate ledger | 328 |
| output/figures/autoresearch_candidate_lifecycle.png | Generated figure | 28053 |
| output/figures/autoresearch_closure_flow.png | Generated figure | 40410 |
| output/figures/autoresearch_integrity_chain.png | Generated figure | 48256 |
| output/figures/autoresearch_security_control_matrix.png | Generated figure | 86574 |
| output/figures/ml_bootstrap_intervals.png | Generated figure | 21834 |
| output/figures/ml_calibration_reliability.png | Generated figure | 73889 |
| output/figures/ml_candidate_rank_stability.png | Generated figure | 43692 |
| output/figures/ml_candidate_scores.png | Generated figure | 59953 |
| output/figures/ml_classification_metrics_heatmap.png | Generated figure | 55092 |
| output/figures/ml_complexity_accuracy.png | Generated figure | 35135 |
| output/figures/ml_confusion_matrix.png | Generated figure | 65820 |
| output/figures/ml_confusion_pairs.png | Generated figure | 33982 |
| output/figures/ml_generalization_gap.png | Generated figure | 48512 |
| output/figures/ml_learning_curves.png | Generated figure | 59258 |
| output/figures/ml_paired_correctness.png | Generated figure | 43309 |
| output/figures/ml_per_class_accuracy.png | Generated figure | 34800 |
| output/figures/ml_probability_margin_distribution.png | Generated figure | 41754 |
| output/figures/ml_probability_quality.png | Generated figure | 38071 |
| output/figures/ml_robustness_matrix.png | Generated figure | 51332 |
| output/figures/ml_selective_accuracy.png | Generated figure | 48274 |
| output/figures/ml_training_dynamics.png | Generated figure | 51004 |
| output/figures/mnist_class_balance.png | Generated figure | 27059 |
| output/figures/mnist_error_examples.png | Generated figure | 28431 |
| output/figures/mnist_subset_contact_sheet.png | Generated figure | 23617 |
| output/reports/autoresearch_evidence_overview.md | Evidence registry | 1136 |
| output/reports/autoresearch_loop.json | Loop artifact | 16085 |
| output/reports/autoresearch_review_packet.md | Review packet | 912 |
| output/reports/autoresearch_security_review.md | Review packet | 1104 |
| output/reports/autoresearch_summary.md | Loop artifact | 255 |
| output/reports/benchmark_readiness_smoke.json | Benchmark grading | 778 |
| output/reports/ml_benchmark_score.json | Benchmark grading | 382 |
| output/reports/ml_experiment_report.md | Loop artifact | 1687 |

: Generated artifact manifest from `output/reports/artifact_manifest.json`. {#tbl:autoresearch-loop}

| Gate | Required | Decision | Rationale |
| --- | --- | --- | --- |
| proposal_review | True | deferred | Decision is read from human_review.yaml when present; generated readiness is not approval. |
| evidence_review | True | deferred | Decision is read from human_review.yaml when present; generated readiness is not approval. |

: Review-gate decisions from `output/data/review_decisions.json`. {#tbl:review-gates}

| Benchmark task | Status | Score | Grading output |
| --- | --- | --- | --- |
| readiness-smoke | graded | 1 | output/reports/benchmark_readiness_smoke.json |
| ml-loop-score | graded | 1 | output/reports/ml_benchmark_score.json |

: Benchmark grading table from `output/data/benchmark_scores.json`. {#tbl:benchmark-scores}

| Phase | Order | Group | Observed artifacts | Description |
| --- | --- | --- | --- | --- |
| intrinsic readiness | 1 | readiness | 3 | validate configured project-intrinsic contracts |
| core artifacts | 2 | loop | 0 | write plan, stage matrix, and provisional loop outputs |
| evidence registry | 3 | evidence | 2 | write local evidence registry |
| ml task | 4 | ml | 54 | run fixed-seed bounded candidate evaluation |
| method contract | 5 | governance | 3 | write program, idea, run, review, and benchmark ledgers |
| provisional payloads | 6 | settlement | 12 | refresh loop payloads before extrinsic validation |
| security artifacts | 7 | security | 10 | write local security and integrity evidence |
| final visuals | 8 | figures | 54 | write final registry-backed figures |
| manuscript hydration | 9 | manuscript | 9 | write variables, provenance, and figure blocks |
| readiness manifest | 10 | settlement | 12 | refresh checksum manifest before extrinsic validation |
| schema manifest | 11 | schema | 2 | write generated JSON schema-version manifest |
| research object manifest | 12 | packaging | 2 | write local research-object manifest |
| extrinsic readiness | 13 | readiness | 3 | validate generated artifacts and extrinsic contracts |
| final schema manifest | 14 | schema | 2 | refresh schema manifest after final payload updates |
| final research object manifest | 15 | packaging | 2 | refresh local research-object manifest |
| artifact manifest | 16 | settlement | 12 | write final artifact checksum manifest |

: Deterministic phase ledger from `output/data/autoresearch_phase_ledger.json`; settlement order is not an autonomy claim. {#tbl:phase-ledger}

| Figure | Pixels | Variance | Source exists | Nonblank |
| --- | --- | --- | --- | --- |
| fig:autoresearch_candidate_lifecycle | 1184x480 | 0.083 | True | True |
| fig:autoresearch_closure_flow | 1664x448 | 0.015 | True | True |
| fig:autoresearch_integrity_chain | 1440x734 | 0.040 | True | True |
| fig:autoresearch_security_control_matrix | 1470x734 | 0.014 | True | True |
| fig:autoresearch_stage_matrix | 1120x416 | 0.080 | True | True |
| fig:ml_bootstrap_intervals | 1152x448 | 0.009 | True | True |
| fig:ml_calibration_reliability | 1152x832 | 0.015 | True | True |
| fig:ml_candidate_rank_stability | 1408x608 | 0.053 | True | True |
| fig:ml_candidate_scores | 1376x688 | 0.013 | True | True |
| fig:ml_classification_metrics_heatmap | 928x832 | 0.092 | True | True |
| fig:ml_complexity_accuracy | 1120x608 | 0.010 | True | True |
| fig:ml_confusion_matrix | 896x768 | 0.046 | True | True |
| fig:ml_confusion_pairs | 1152x576 | 0.129 | True | True |
| fig:ml_generalization_gap | 1184x864 | 0.059 | True | True |
| fig:ml_learning_curves | 1216x608 | 0.018 | True | True |
| fig:ml_paired_correctness | 768x672 | 0.075 | True | True |
| fig:ml_per_class_accuracy | 1152x512 | 0.098 | True | True |
| fig:ml_probability_margin_distribution | 1184x864 | 0.024 | True | True |
| fig:ml_probability_quality | 1344x608 | 0.046 | True | True |
| fig:ml_robustness_matrix | 1280x608 | 0.073 | True | True |
| fig:ml_selective_accuracy | 1088x608 | 0.016 | True | True |
| fig:ml_training_dynamics | 1408x608 | 0.072 | True | True |
| fig:mnist_class_balance | 1216x544 | 0.071 | True | True |
| fig:mnist_error_examples | 1280x734 | 0.234 | True | True |
| fig:mnist_subset_contact_sheet | 1216x544 | 0.228 | True | True |

: Figure-quality checks from `output/data/figure_quality_report.json`; 25 registered figure(s) were checked. {#tbl:figure-quality}

## Security Readiness And Integrity Evidence {#sec:security-readiness-integrity}

The local security profile reports attestation status
`passed` after checking
`80` file record(s), with
`0` missing record(s) and
`0` checksum mismatch(es). The inventory
contains `14` input record(s) and
`69` generated-artifact record(s). The
integrity-chain figure is @fig:autoresearch_integrity_chain. These values support
local artifact-integrity claims only; they do not claim external signing,
production SLSA compliance, or runtime security monitoring.

![Local integrity chain from output/data/autoresearch_integrity_attestation.json; checksums summarize the observed run artifacts and remain unsigned local evidence. Generation method: Local checksum attestation chain with checked, missing, and mismatch counts. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_integrity_chain.png){#fig:autoresearch_integrity_chain width="0.84\textwidth"}

| Integrity field | Value |
| --- | --- |
| status | passed |
| algorithm | sha256 |
| checked files | 80 |
| missing files | 0 |
| checksum mismatches | 0 |
| external signature | False |

: Integrity-attestation summary from `output/data/autoresearch_integrity_attestation.json`. {#tbl:security-integrity}

## Manuscript Hydration Provenance {#sec:manuscript-hydration-provenance}

The final run supports `6` manuscript-facing claim(s)
and checks `78` required artifact(s). The rendered
manuscript uses injected variables from generated data payloads, so the abstract
and results track the latest analysis run rather than hard-coded counts. The
final readiness status is `passed`; generated review decisions are
recorded as deferred for human review rather than as self-approval.

| Source artifact | Injected variables or fragments |
| --- | --- |
| output/data/autoresearch_integrity_attestation.json | 5 |
| output/data/autoresearch_loop.json | 57 |
| output/data/autoresearch_phase_ledger.json | 2 |
| output/data/autoresearch_schema_manifest.json | 1 |
| output/data/autoresearch_security_profile.json | 6 |
| output/data/autoresearch_supply_chain_inventory.json | 3 |
| output/data/autoresearch_threat_model.json | 4 |
| output/data/benchmark_scores.json | 1 |
| output/data/figure_quality_report.json | 3 |
| output/data/manuscript_variable_provenance.json | 1 |
| output/data/ml_bootstrap_intervals.json | 3 |
| output/data/ml_calibration_bin_intervals.json | 1 |
| output/data/ml_calibration_report.json | 3 |
| output/data/ml_candidate_intervals.json | 1 |
| output/data/ml_candidate_ledger.json | 1 |
| output/data/ml_candidate_rank_stability.json | 3 |
| output/data/ml_candidate_selection_audit.json | 1 |
| output/data/ml_class_balance.json | 3 |
| output/data/ml_classification_diagnostics.json | 5 |
| output/data/ml_diagnostic_boundary.json | 1 |
| output/data/ml_paired_comparison.json | 3 |
| output/data/ml_probability_diagnostics.json | 4 |
| output/data/ml_robustness_report.json | 2 |
| output/data/ml_statistical_summary.json | 9 |
| output/data/ml_task_results.json | 39 |
| output/data/ml_training_diagnostics.json | 7 |
| output/data/research_object_manifest.json | 2 |
| output/data/review_decisions.json | 1 |
| output/figures/figure_registry.json | 51 |
| output/reports/artifact_manifest.json | 1 |

: Variable provenance summary from `output/data/manuscript_variable_provenance.json`. {#tbl:variable-provenance}
