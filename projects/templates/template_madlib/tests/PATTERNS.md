# Test Patterns

- Build temp project trees with real `manuscript/config.yaml` files.
- Assert generated JSON and PNG files exist, contain live values, and are nonblank when visual output is the contract.
- Assert schema-driven titles, method protocol rows, design principles, operational phases, audit rules, and generated tables appear in variables.
- Assert generated Methods prose explains method concepts that tables alone cannot carry: digest construction, review scenario, explicit/default field origin, selection invariants, slot-to-section allocation, figure evidence, claim-ledger alignment, validation gates, review-packet handoff, and fork migration.
- Assert evaluation criteria, QA probes, failure modes, and authoring obligations round-trip from YAML into variables and generated artifacts.
- Assert configured-field explicit/default origins and cover/pipeline figure declarations round-trip into JSON, Markdown variables, and registered figures.
- Assert forks or exemplar updates do not add method claims without a config row, evidence artifact, and failing gate.
- Assert review-packet claims mention generated data, reports, figures, validation results, and copy statistics.
- Use subprocesses for script smoke checks.
- Scan hydrated manuscript output for unresolved `{{TOKEN}}` placeholders.
- Do not use `unittest.mock`, `MagicMock`, or patch decorators.
