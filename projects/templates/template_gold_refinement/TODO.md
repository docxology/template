# template_gold_refinement TODO

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

- Keep the refinery pipeline (ore → smelting → assaying → cupellation →
  nine-nines certification) as the gated default path, with purity monotonic
  across stages.
- Keep mega-madlib token injection deterministic, seeded, and config-owned
  (lexicon in config, no hardcoded selections).
- Keep `src/evidence.py` cross-checking every manuscript contribution claim
  against its evidence source, including dotted Python member paths.
- Transmission bookends (`transmission_begin` / `transmission_end`) frame the
  certified output and remain validated as a pair.
- Preserve the no-mocks / deterministic-seed policy for any new refinery stage
  or assay probe.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the declared config blocks
  (`contribution_claims`, `pipeline_phases`, `audit_rules`, `steganography`,
  `evaluation`, `authoring_contract`, and explicit LLM-review gates) when code
  defaults change.
- The prefix-constrained reverse assay uses the config-selected target and
  generated report surface; forks must preserve ordered-prefix semantics.
- The noncompensatory `PurityVector` remains domain-selectable only when a fork
  supplies evidence for the added dimensions.

## Documentation and signposting gaps

- Keep README and AGENTS clear that Stage 02 generates figures and the
  evidence/figure registries while Stage 03 renders the certified manuscript.
- Keep `docs/domain_fork_guide.md` and `src/domain_adapter.py` cross-linked so
  forkers can remap stages (clinical evidence, legal citation, engineering spec).
- Keep the analogy-break boundary documented: where gold-refining fails as a
  model for manuscript composition.

## Test and validator gaps

- Platform references remain an external-evidence concern; do not promote the
  publishing-status block without source-bound records for each platform.
- The analogy-boundary theorem is a local design predicate, not evidence of
  manuscript quality or a substitute for domain validation infrastructure.
- Integration with real manuscript validation and real-paper measurement is
  outside this deterministic toy exemplar until a licensed, owner-approved
  source and claim ledger are supplied.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
