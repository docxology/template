# template_model

A **model** exemplar tool — a pre-trained linear regression model that
predicts a numeric target from a single numeric feature, using fixed, real
coefficients computed via ordinary least squares (OLS) on a small embedded
dataset. A model is a tool with a specific entrypoint contract: `predict.sh`
in place of a generic `run.sh`, plus the same `validate.sh` pattern every
other tool exemplar uses.

## Files

```
template_model/
├── tools.yaml            # Tool manifest (type: model)
├── model_weights.json    # Real OLS coefficients + training data + provenance
├── README.md             # This file
├── AGENTS.md             # Agent-oriented documentation
├── .gitignore
└── scripts/
    ├── predict.sh        # Inference entrypoint
    └── validate.sh       # Environment + payload validation
```

## Quick Start

```bash
# Validate environment
bash scripts/validate.sh

# Validate a payload against the model's feature contract
bash scripts/validate.sh <<< '{"hours_studied": 6.5}'

# Run inference
bash scripts/predict.sh <<< '{"hours_studied": 6.5}'
# → {"prediction": 80.3697, "feature_name": "hours_studied", "target_name": "exam_score"}
```

## Manifest (`tools.yaml`)

| Field | Value |
|---|---|
| type | `model` |
| version | `1.0` |
| license | `CC0-1.0` |
| entrypoints | `scripts/predict.sh`, `scripts/validate.sh`, `model_weights.json` |

## The Model

Linear regression, `exam_score = intercept + coefficient * hours_studied`,
trained on the 10-point dataset embedded in `model_weights.json`
(R² ≈ 0.998 against that data). Coefficients are computed via the standard
closed-form OLS formulas — no external ML library, fully deterministic and
reproducible by any reader from the embedded `training_data` array alone.

## Customising

1. Replace `model_weights.json`'s `training_data` with your own dataset, and
   the `intercept`/`coefficient` with your own trained values (or point
   `predict.sh` at a real training pipeline if you need more than one
   feature or a non-linear model).
2. Update `tools.yaml` — bump `version`, adjust `tags`, and add any
   additional entrypoints (e.g. a `train.sh` if you want in-repo retraining).
3. Keep `scripts/validate.sh` green before committing.
