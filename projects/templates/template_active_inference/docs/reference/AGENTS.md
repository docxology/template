# reference/ - Public Contracts

## Purpose

This directory contains stable, reader-facing reference contracts for the
Active Inference exemplar. The files here describe generated method coverage,
rendering reproducibility, replay expectations, and artifact provenance.

## Local Rules

- Keep this directory documentation-only. Implementation belongs in
  [`../../src/`](../../src/), orchestration in [`../../scripts/`](../../scripts/),
  and generated outputs in [`../../output/`](../../output/).
- Treat [`method-inventory.md`](method-inventory.md) as generated. Update it
  with [`../../scripts/generate_method_inventory.py`](../../scripts/generate_method_inventory.py)
  and verify with `--check`.
- Keep [`rendering-reproducibility.md`](rendering-reproducibility.md) aligned
  with the live render, replay, figure registry, copied-output, and sheaf
  artifact contracts.
- Do not hand-author volatile counts when the manuscript variable generator or
  generated artifacts can provide them.

## Verification

```bash
uv run --directory projects/templates/template_active_inference \
  python scripts/generate_method_inventory.py --check
uv run --directory projects/templates/template_active_inference \
  python scripts/validate_outputs.py
```
