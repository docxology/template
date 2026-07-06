## Reproducibility

### Determinism guarantee

Given the same `config.yaml` (grammar hash `{{GRAMMAR_HASH}}`), seed `{{GRAMMAR_SEED}}`,
and `template_autopoiesis` source code, the same child project is produced
on every invocation.  The determinism chain is:

1. `seed` + `slot_name` + `ordinal` + `options` → SHA-256 → option index.
2. All file contents are assembled without random or time-dependent inputs.
3. The tree hash is computed from file contents, not file metadata.

### Recompute / verify

```bash
# Expand and materialize
uv run python scripts/autopoiesis.py expand --output output/spec.json
uv run python scripts/autopoiesis.py materialize --out-root output/children

# Verify integrity
uv run python scripts/autopoiesis.py verify output/children/<child_name>
```

### Toolchain

- Python ≥ 3.10
- numpy, matplotlib, pyyaml (runtime)
- pytest, pytest-cov (test)
- hypothesis (optional — property tests skip gracefully if absent)

### Build command

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src \
  --cov-fail-under=90
```
