# template_pools_rules_tools TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
next action, proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Integrity and template-status gaps

- Keep the three resource directories read-only: never write back to `fonds/`, `rules/`, or `tools/` from this project.
- Keep `src/type_defs.py` the single source of truth for all TypedDict shapes; no inline dicts and no `Any` in public signatures.
- Keep graceful-fallback behavior everywhere — `src/` functions return `None` or empty collections when files are absent and never raise.
- Confirm every `pytest.mark.skipif` guard keeps an accurate resource file-path check as pool contents evolve.

## Configurable-surface gaps

- Extend the discovery adapters in `src/integration.py` when new public fonds/rules/tools ship; do not duplicate the discovered roster in manuscript configuration.
- Any new resource-pool category must enter through a typed loader before it is wired into `integration.py`.

## Documentation and signposting gaps

- Keep `.agents/skills/template-pools-rules-tools/SKILL.md` aligned with the public resource-pool surface it discovers.
- Keep README, AGENTS, and CLAUDE guidance clear that repo-root resolution relies on `parents[4]` and that the module is named `type_defs.py` (never `types.py`).

## Test and validator gaps

- Keep malformed fonds/rules/tools payloads covered by regression-discriminating
  negative controls; every new constraint family needs a failing mutation case.
- Extend strong-rule semantic evaluation coverage as new formal constraints are added under `rules/templates/`.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POOLS-FOURTH-FOND-1` | blocked-external | Medium | Owner-approved fourth fond exemplar | Obtain the required owner or external receipt to unblock; run public-scope and standalone gates and attach public fond manifest and registry update. | public fond manifest and registry update | `uv run pytest tests -q --no-cov --timeout=120` | absent exemplar must remain blocked, not skipped as pass |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
