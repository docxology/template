# Reference Contracts

This directory holds the public reference contracts for the Active Inference
exemplar.

| File | Role |
| --- | --- |
| [`method-inventory.md`](method-inventory.md) | Generated inventory for every Python `class` and `def` in the project, including scripts and internal helpers. |
| [`rendering-reproducibility.md`](rendering-reproducibility.md) | Contract for sheaf rendering, replay, provenance, figure metadata, PDF/web parity, and copied-output reproducibility. |

Regenerate the method inventory with:

```bash
uv run --directory projects/templates/template_active_inference \
  python scripts/generate_method_inventory.py
```

Validate generated outputs with:

```bash
uv run --directory projects/templates/template_active_inference \
  python scripts/validate_outputs.py
```
