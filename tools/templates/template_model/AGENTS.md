# AGENTS.md — template_model

> Agent-oriented documentation for the `model` exemplar tool.
> Human developers: see [README.md](README.md).

## Identity

- **Type:** `model`
- **Manifest:** `tools.yaml`
- **Version:** `1.0`

## Invocation

### Predict

```
stdin:  JSON object { "hours_studied": number }
stdout: JSON object { "prediction": number, "feature_name": string, "target_name": string }
exit:   0 = inference completed
        1 = malformed input (missing/non-numeric feature, invalid JSON)
        2 = environment error (model_weights.json missing)
```

```bash
bash scripts/predict.sh <<< '{"hours_studied": 6.5}'
```

### Validate

```
stdin:  (optional) JSON payload to check against the feature contract
stdout: human-readable validation report
exit:   0 = valid (environment ready, or payload conforms)
        1 = invalid (environment broken, or payload malformed)
```

```bash
bash scripts/validate.sh                                   # environment check
bash scripts/validate.sh <<< '{"hours_studied": 6.5}'       # payload check
```

## Agent Decision Guidance

- Use this tool when a task needs a **numeric prediction from a single
  feature** without pulling in a heavyweight ML framework — the model is a
  ~15-line closed-form linear predictor, not a stub.
- Always run `validate.sh` on a payload before `predict.sh` in an unfamiliar
  pipeline — it reports the exact missing/malformed field rather than a bare
  crash.
- `model_weights.json` is the single source of truth for the model's
  coefficients, feature name, and target name — read it, do not hard-code
  the coefficients elsewhere.
- This model is intentionally simple (single feature, linear) so its
  correctness can be hand-verified from the embedded `training_data`; it is
  not a template for production-grade model serving.

## Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| `bash` ≥ 3.2 | Script runtime | Yes |
| `python3` | Inference + validation logic | Yes |
