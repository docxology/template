# template_formal TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
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
- Add any future fault-injection or protocol-timing parameters under typed source loaders (`network/bus.py::FaultConfig`) rather than reading ad hoc YAML from scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_formal`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator (a later registration stage owns this).

## Test and validator gaps

- Add a negative control before widening any new typed-invariant claim beyond the ISC-1..40 surface already covered.
- Add dashboard/report schema assertions only if a future stage adds a dashboard (none ships in v1 — manuscript + CLI scripts + figures only, per Out of Scope).
- Registration is complete: `infrastructure/project/public_scope.py`, `docs/_generated/{active_projects,exemplar_roster,COUNTS}.md`, root `.gitignore` (both `projects/templates/template_formal/` and `output/templates/template_formal/` negations), `scripts/audit/check_template_drift.py --strict`, and `scripts/audit/check_tracked_all.py` all pass clean. `CLAUDE.md` and `README.md`'s hand-maintained exemplar lists/tables also mention `template_formal`.
- Not yet updated (lower-priority, pre-existing staleness predates this template — several of these were already missing `template_pitch_deck` too): `MAINTAINERS.md`'s tracked-project-list sentence, `projects/AGENTS.md`'s "Eighteen projects" paragraph, `projects/README.md`'s exemplar bullets/tables, `projects/templates/AGENTS.md`'s "seventeen" structure list, `projects/PAI.md`'s table. These are prose-only (not gated by `check_template_drift.py`); backfill in a dedicated roster-hygiene pass rather than piecemeal per-template edits.

## Minor upcoming

No active rows are currently scoped at this size.

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `FORMAL-ABLATION-1` | Medium | Existing colony experiment fixtures | calibrated ablation matrix | project tests plus deterministic manuscript binding | omitted axis must fail the experiment registry |
| `FORMAL-INVARIANT-1` | Medium | Typed runtime protocol surface | typed-invariant negative-control fixture | strict mypy oracle and runtime test | illegal state fixture must fail mypy/runtime checks |

## Major upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `FORMAL-SPEC-1` | Major | Optional Lean/TLA+ tools | real formal-spec receipt | explicit formal script when tools are installed | decorative or skipped spec must not report pass |

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
