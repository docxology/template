# Deterministic ML-Loop Experiment

- Task: small MNIST neural-network classification
- Seed: 20260525
- Train/test size: 2000/500
- Baseline accuracy: 0.826
- Accepted candidate: `exp-mlp-tanh-64`
- Best accuracy: 0.894
- Accuracy delta: 0.068
- Candidate budget exhausted: `true`
- LLM calls used: 0
- Cost used: 0.00

## Candidate Ledger

| Candidate | Status | Model | Parameters | Accuracy | Delta |
| --- | --- | --- | ---: | ---: | ---: |
| `exp-softmax-linear` | rejected | softmax_regression | 7850 | 0.882 | 0.056 |
| `exp-mlp-relu-32` | rejected | mlp | 25450 | 0.886 | 0.060 |
| `exp-tiny-patch-attention` | rejected | tiny_patch_transformer | 5994 | 0.304 | -0.522 |
| `exp-mlp-tanh-64` | accepted | mlp | 50890 | 0.894 | 0.068 |
| `exp-mlp-relu-64-deferred` | deferred | mlp | 0 | N/A | N/A |

## Training Diagnostics

Epoch-level metrics are written to `output/data/ml_training_history.csv`; training summaries are written to `output/data/ml_training_diagnostics.json`; accepted-candidate error examples are written to `output/data/ml_error_examples.json`. Probability records, classification diagnostics, calibration bins, and robustness smoke-test rows are written to `output/data/ml_prediction_records.json`, `output/data/ml_classification_diagnostics.json`, `output/data/ml_calibration_report.json`, `output/data/ml_robustness_report.json`, `output/data/ml_probability_diagnostics.json`, `output/data/ml_bootstrap_intervals.json`, and `output/data/ml_paired_comparison.json`, plus `output/data/ml_statistical_summary.json`.

This report is generated from deterministic local data. It does not call an external model, execute generated code, or approve the manuscript.
