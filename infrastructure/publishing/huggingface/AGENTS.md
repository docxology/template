# HuggingFace Publishing Adapter

## Purpose

Publishes manuscript and reproducibility bundles to HuggingFace Hub repositories,
usually as datasets for research artifacts.

## Contracts

- Keep `dry_run=True` as the safe default.
- Resolve tokens from explicit config first, then `HUGGINGFACE_TOKEN` or
  `HF_TOKEN`; never log token values.
- Preserve the raw HTTP path for hermetic tests and dependency-light installs.
- Use the optional `huggingface_hub` client only for real Hub uploads that need
  Git-LFS handling.
- Return structured `HuggingFaceResult` values instead of raising on HTTP or
  credential failures.

## Verification

```bash
uv run pytest tests/infra_tests/publishing/test_huggingface_adapter.py
```

## Parent Docs

- Publishing module: [`../AGENTS.md`](../AGENTS.md)
- Adapter README: [`README.md`](README.md)
