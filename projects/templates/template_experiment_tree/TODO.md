# TODO — template_experiment_tree (future-only)

## Validation evidence
- 29 tests green; 92.23% coverage on `src/` (floor 90%).
- Registration gate: `scripts/gates/public_capabilities.py` passes.

## Integrity gaps
- PDF render not yet admitted as tracked publication evidence (v1 ships token shells only).

## Improvement ladder
1. Hydrate manuscript tokens from `manuscript_variables.json` in the render pipeline and admit the combined PDF as evidence.
2. Add a tree-state diff report (what changed between renders).
3. Optional round-based branch pruning helpers.
