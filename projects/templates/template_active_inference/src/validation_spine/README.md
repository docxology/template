# Validation spine package

Deterministic artifact contracts for the Active Inference exemplar's validation spine.

- `artifacts.py` writes and validates the artifact provenance, deterministic replay, and counterexample matrix records.
- The package is invoked by `scripts/generate_validation_spine.py` and by gate tests before manuscript/output validation.
- Outputs are local project artifacts under `output/data/` and `output/reports/`.

## Verification

```bash
uv run pytest tests/test_validation_spine.py -q
uv run python scripts/generate_validation_spine.py
```
