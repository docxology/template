# template_pitch_deck TODO

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

- Keep PPTX ZIP-member timestamps normalized and require two-run PDF/PPTX
  digest equality in the deterministic artifact gate.
- Keep all three lengths in the raster QA matrix and fail on clipping or overlap
  when the configured raster toolchain is available.
- Mermaid rendering remains optional: `mmdc` plus Chrome/Chromium is bounded by the renderer policy, and an unavailable tool produces an explicit warning/fallback rather than a false embedded-diagram claim.
- Keep publication DOI/repository metadata source-bound and distinguish an
  unavailable deposit from a real owner-authorized publication receipt.
- Content-slide figures flow below their bullet body in both output formats, and `_preflight_all_lengths` audits every configured length before writing any artifact.
- QR annotations are structurally checked against the configured standalone target. A real publication or device-scan check remains an external release concern and must not be inferred from local raster output.

## Configurable-surface gaps

- The `deck.pitch_subject` and `deck.subjects` configuration selects the
  authored subject and content prefix; a fork may add another subject without
  changing the renderer or token path-safety contract.
- Theme is currently monochrome-red (black + white + 3× the same highlight, `manuscript/config.yaml`'s `deck.theme` block); `config.yaml.example` demonstrates a distinct 3-accent palette as a starting point for forks.
- `SlideBudget` (short/medium/long max-slide counts, currently 11/38/58) lives in `infrastructure/rendering/slide_deck.py`, not per-project config — a fork wanting different length budgets currently edits the shared infrastructure constant.

## Documentation and signposting gaps

- `manuscript/README.md` and `src/README.md` are new, minimal — expand with worked examples if this exemplar gains a second pitch subject.
- No architecture diagram doc yet beyond the in-deck Mermaid figure itself; consider a `docs/architecture.md` mirroring `template_newspaper`'s.

## Test and validator gaps

- Keep deterministic generated-sequence tests proving budget filtering is
  prefix-preserving and non-mutating across boundary and oversized decks.
- `mermaid_figure.py`'s real-render tests are skipped when `mmdc` is absent; CI coverage of that path depends on the runner having mermaid-cli installed.
- Keep adversarial token sequences in the regression suite so generated decks
  cannot leak unresolved braces.

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
