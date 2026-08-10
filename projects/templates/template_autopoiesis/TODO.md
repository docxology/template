# template_autopoiesis TODO

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

## Integrity and template-status gaps

- Keep the grammar the single source of truth in `manuscript/config.yaml` (`autopoiesis:` block) and all generation logic in `src/` (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- Keep materialization routed through `src/emit_templates.py::emit_all` for
  every child-facing analysis, test, project, and manuscript file so standalone
  emitters and generated children cannot drift silently.
- Keep provenance recompute-based: verification must re-derive the tree hash from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Keep the placeholder-safe `manuscript/config.yaml.example` synchronized with the live config shape, including the list-form slot and dependency syntax.
- Add an optional archetype-selection filter so forks can materialize a subset of the combinatoric product space rather than one child per domain.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and materializes/verifies children, while Stage 03 renders the descriptive manuscript PDF.
- Finish the remaining `SPEC.md` Phase 10 items and keep them in step with the
  declared grammar surface.
- Consider fencing `manuscript/preamble.md` as a complete LaTeX block to eliminate renderer recovery warnings.

## Dependency-mode gaps

- `dep_mode="template"` remains intentionally loud (`NotImplementedError`) until a seam contract is defined that does not require parent infrastructure at child runtime.

## Test and validator gaps

- Keep figure fallback handling explicit for empty arrays, and require
  malformed or under-specified grammar shapes to fail before expansion with real
  negative controls.
- Strengthen the mutation meta-gate with an additional stubbed-kernel case per domain, so green-by-construction theater cannot slip through as new domains are added.
- Eliminate the remaining meta-gate skip by selecting the first available negative-control primitive per domain (the signal domain's first primitive has none).

## Minor upcoming

No active rows are currently scoped at this size.

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AUTOPOIESIS-MUTATION-1` | Medium | Existing mutation meta-gate | per-domain mutation report | `uv run pytest projects/templates/template_autopoiesis/tests -q` | removing a domain guard must fail the mutated case |
| `AUTOPOIESIS-ARCHETYPE-1` | Medium | Config schema extension | filtered child manifest | project validator plus generated-child integrity tests | unknown archetype filter must fail closed |

## Major upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AUTOPOIESIS-SPEC-1` | Major | Grammar/spec lockstep | `SPEC.md` Phase 10 checklist | strict drift and spec-contract tests | fenced preamble/spec mismatch must fail validation |

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
