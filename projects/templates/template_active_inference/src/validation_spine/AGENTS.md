# Validation spine package (`src/validation_spine/`)

This package owns the falsifiable validation-spine artifacts for the Active Inference exemplar.

## Contracts

- Keep provenance records deterministic: every declared artifact must include existence, size, producer, and SHA-256 state.
- Keep replay checks local and offline. Replays should rebuild small deterministic artifacts in a temporary directory and compare hashes or parsed JSON payloads.
- Keep counterexamples explicit: each row needs a gate, mutation, expected failure flag, and test reference.
- Do not add manuscript rendering or figure-generation logic here. This package reports validation evidence; orchestration remains in `scripts/generate_validation_spine.py`.

## Verification

```bash
uv run pytest tests/test_validation_spine.py -q
uv run python scripts/generate_validation_spine.py
```
