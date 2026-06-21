# GNN Track Notes

Project-owned parser, model, and concordance checks for the Active Inference GNN
specifications in `../../gnn/*.gnn.md`.

## Where To Look

| Task | Location |
| --- | --- |
| Dataclasses and variable/edge shape contract | `model.py` |
| Section parser and structural errors | `parser.py` |
| Cross-lane concordance checks | `concordance.py` |
| Public exports | `__init__.py` |

## Contracts

- Treat the `.gnn.md` files as the canonical model descriptions; code and
  manuscript prose conform to them, not the reverse.
- Parser failures must be loud and specific (`GNNParseError`) for malformed
  required sections, dimensions, parameters, or connection edges.
- Preserve lossless-enough round trips for model metadata used by formal interop
  and roadmap-track artifacts.
- When variables or edges change, check analytical assumptions, SI simulation
  model code, ontology aliases, and Lean witness names for drift.

## Commands

```bash
uv run pytest tests/test_gnn.py tests/test_method_inventory.py tests/test_roadmap_promotion.py
uv run python scripts/generate_formal_interop_tracks.py
```
