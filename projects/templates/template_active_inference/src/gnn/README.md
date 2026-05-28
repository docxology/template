# GNN (Generalized Notation Notation)

Parsing and modelling of the Active Inference GNN specifications under `../../gnn/`.

- `parser.py` — parse `.gnn.md` specifications into structured models.
- `model.py` — the GNN model object (factors, matrices, connections).
- `concordance.py` — check that the GNN model agrees with the analytical,
  numeric, and pymdp tracks (single source of truth for model structure).
