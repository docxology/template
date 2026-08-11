# template_formal TODO

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

## Optional formal side-spec

- Formal side-specs (Lean 4 + TLA+) are non-default, run via `scripts/check_formal_specs.sh`.
- Keep the Lean and TLA+ side-specs optional but real: the formal-check script
  must invoke the actual tools when installed, report unavailable tools
  explicitly, and never turn a skipped side-spec into a pass claim.
- Keep theorem and invariant claims non-vacuous, zero-`sorry`, and paired with
  a runtime or typed negative control when the protocol surface changes.

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for illegal-state-unrepresentable, session-typed, affine-discipline design applied to a decentralized multiagent domain.
- Keep the manuscript's claim-scoping section ("what mypy --strict proves" vs "what is a runtime discipline") in lockstep with `tests/mypy_fixtures/` — every strong claim needs a live ISC-numbered test, not just prose.
- Keep the formal side-specs (Lean/TLA+) wired to `scripts/check_formal_specs.sh` for as long as they ship; do not let either drift to vestigial/unwired status (ISC-36 anti).

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Any future fault-injection or protocol-timing parameters must enter through typed source loaders (`network/bus.py::FaultConfig`) rather than ad hoc YAML reads in scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_formal`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator (a later registration stage owns this).

## Test and validator gaps

- Keep a negative control before widening any typed-invariant claim beyond the ISC-1..40 surface already covered.
- The public roster and generated documentation are generator-owned; use the current public-scope, drift, tracked-path, and generated-document gates rather than recording registration state in this TODO.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FORMAL-SPEC-1` | blocked-tool | Medium | Optional Lean/TLA+ tools | Install or pin the required tool, or record its unavailable status; run the explicit formal script when available and attach a real formal-spec receipt. | real formal-spec receipt | `uv run pytest tests -q --no-cov --timeout=120` | decorative or skipped spec must not report pass |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
