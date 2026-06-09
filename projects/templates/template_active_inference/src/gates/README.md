# Validation gates

Deterministic gates that check generated outputs are well-formed and concordant
across the five tracks before the manuscript is composed.

- `validation.py` — output/structure validation and cross-track consistency checks.
- `documentation_contract.py` — Markdown links, generated-doc links,
  README/AGENTS pairs, command context, and historical evidence wording.
- `method_inventory.py` — AST-backed source/script method inventory for
  documentation coverage.
