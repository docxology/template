# TODO — template_experiment_tree (future-only)

## Validation evidence
- 29 tests green; 92.23% coverage on `src/` (floor 90%).
- Registration gate: `scripts/gates/public_capabilities.py` passes.

## Integrity and template-status gaps
- PDF render not yet admitted as tracked publication evidence (v1 ships token shells only).
- Current test and validator contract: 29 tests cover the tree engine, store, report, and token backing; validators fail closed on frozen-node mutation, run-command drift, and unbacked tokens.

## Configurable-surface gaps
- Current configurable-surface contract: `manuscript/config.yaml` owns publication metadata and render settings; tree policy (status vocabulary, run-command contract) is engine-owned in `src/template_experiment_tree/tree.py` and not yet config-exposed.

## Documentation and signposting gaps
- Documentation and signposting gaps: none open — README, AGENTS, and STANDALONE carry the required configuration, validation, fork, run-path, publication, and test signposts.

## Test and validator gaps
- Current test and validator contract covers tree discipline and token backing; missing: a validator for cross-tree node-id reuse and a render-stage admission test for the tracked PDF.

## Upcoming work
- minor upcoming: admit the combined PDF as tracked evidence once the render pipeline hydrates `{{EXP_*}}` tokens.
- medium upcoming: tree-state diff report (what changed between renders).
- major upcoming: round-based branch pruning helpers with frozen-node preservation.
