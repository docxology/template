# validation_spine/ - Artifact Provenance Spine

## Purpose

This package validates the generated artifact spine for the Active Inference
exemplar: required artifact presence, deterministic fingerprints, producer
metadata, replay provenance, and release-facing provenance drift checks.

## Local Rules

- Keep validators deterministic and filesystem-local; the public exemplar must
  not rely on network calls, private data, or LLM calls.
- Preserve race-safe file provenance through `_file_fingerprint` in
  [`artifacts.py`](artifacts.py). Do not replace it with ad hoc path or mtime
  checks.
- A new required artifact needs a producer, a fingerprinted provenance row, a
  validation rule, and a negative-control test before manuscript prose may rely
  on it.
- Project-local scratch output lives under
  [`../../output/`](../../output/) during pipeline runs. Root
  `output/templates/template_active_inference/` is populated only after the
  stage 05 copy step — see [`../../../../../docs/RUN_GUIDE.md`](../../../../../docs/RUN_GUIDE.md).

## Verification

```bash
uv run pytest tests/test_validation_spine.py tests/test_track_consolidation.py -q --tb=short
```
