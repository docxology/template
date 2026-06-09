# Reference Contracts

This directory holds the public reference contracts for the Active Inference
exemplar.

| File | Role |
| --- | --- |
| [`method-inventory.md`](method-inventory.md) | Generated inventory for every Python `class` and `def` in the project, including scripts and internal helpers. |
| [`rendering-reproducibility.md`](rendering-reproducibility.md) | Contract for sheaf rendering, replay, provenance, figure metadata, PDF/web parity, and copied-output reproducibility. |

Verify reference documentation with:

```bash
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/generate_method_inventory.py --check
uv run python scripts/validate_outputs.py
```
