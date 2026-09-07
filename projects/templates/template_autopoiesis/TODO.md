# template_autopoiesis TODO

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

- Keep the grammar the single source of truth in `manuscript/config.yaml` (`autopoiesis:` block) and all generation logic in `src/` (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- Keep materialization routed through `src/emit_templates.py::emit_all` for
  every child-facing analysis, test, project, and manuscript file so standalone
  emitters and generated children cannot drift silently.
- Keep provenance recompute-based: verification must re-derive the tree hash from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Keep the placeholder-safe `manuscript/config.yaml.example` synchronized with the live config shape, including the list-form slot and dependency syntax.
- The optional `archetype_filters` mapping is the fork-owned selector for materializing a subset of the combinatoric product space; keep its values schema-validated and included in the grammar digest.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and materializes/verifies children, while Stage 03 renders the descriptive manuscript PDF.
- `SPEC.md` Phase 10 and `manuscript/preamble.md` are source-owned inputs to the deterministic manuscript contract; keep the checklist, explicit fences, and renderer-qualified receipt synchronized.

## Dependency-mode gaps

- `dep_mode="template"` remains intentionally loud (`NotImplementedError`) until a seam contract is defined that does not require parent infrastructure at child runtime.

## Test and validator gaps

- Keep figure fallback handling explicit for empty arrays, and require
  malformed or under-specified grammar shapes to fail before expansion with real
  negative controls.
- Keep mutation coverage per domain and permit an explicit skip only when a domain has no negative-control primitive; a second primitive must be used when available so the meta-gate cannot become green-by-construction.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AUTOPOIESIS-SPEC-1` | blocked-tool | Medium | Pinned renderer and visual QA toolchain | Install or pin the renderer, or record its unavailable receipt; run the explicit Phase 10 visual gate and attach the tool-qualified receipt. | `SPEC.md` Phase 10 checklist + renderer receipt | `uv run pytest projects/templates/template_autopoiesis/tests -q --no-cov --timeout=120` | missing renderer must report blocked-tool; fenced preamble/spec mismatch must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
