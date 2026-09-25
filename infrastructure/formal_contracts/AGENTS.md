# infrastructure/formal_contracts — Agent Notes

## Purpose

Typed, machine-checkable contract layer for manuscripts ("well-typed
research", GOAL C seed). Frozen dataclass blocks; monoidal composition
into a `Manuscript`; fail-closed `check_manuscript` enforcing evidence
tiers, formal resolvability, acyclicity, and no orphans.

> **Honesty note.** The structure is a preorder-enriched graph with
> monoidal (disjoint-union) composition. It is NOT a topos or a full
> categorical structure; do not overclaim in docs or manuscripts.

## Public API

- `compose(blocks) -> Manuscript` — validates unique ids, resolvable
  edges/children, acyclicity (cycle path in message), raises
  `CompositionError` with `Diagnostic` list.
- `check_manuscript(manuscript) -> Report` — fail-closed: claims need
  supporting evidence of declared tier (`UNSUPPORTED_CLAIM`,
  `INSUFFICIENT_TIER`); formal statements must resolve (`DANGLING_REF`);
  blocks must be reachable from a section (`ORPHAN_BLOCK`).
- `compose_manuscripts(*parts)` / `EMPTY_MANUSCRIPT` — monoid operations.
- `read_blocks(markdown_text)` — reader for `::: {.claim #id}` /
  `.definition` / `.evidence` / `.figure` / `.table` / `.dataset` divs
  and `[@cite]` references. A reader, never a renderer.
- `Diagnostic` carries stable dotted codes from
  `diagnostics.FormalCode` (namespace `FORMAL.*` — new codes; adding is
  non-breaking, changing is breaking).

## Modules

- `model.py` — frozen block dataclasses, `EvidenceTier` (linearly
  ordered), `EdgeKind`, `DependencyEdge`, `MatchPolicy`.
- `checker.py` — `compose`, `check_manuscript`, `Manuscript`, `Report`,
  `Diagnostic`, `CompositionError`.
- `diagnostics.py` — `FormalCode` dotted IDs.
- `reader.py` — markdown formalism-convention reader (+ `ReaderError`).

## Boundaries

- No changes to `infrastructure/rendering/` or `infrastructure/validation/`.
  A future rendering-side integration would consume `check_manuscript`
  reports; the hook point is noted in the lane report, not implemented here.
- No network, no LLM calls, no mock frameworks in tests.

## See Also

- [`../validation/content/diagnostic_codes.py`](../validation/content/diagnostic_codes.py) — the dotted-code convention these codes follow
- [`../../docs/prompts/SKILL.md`](../../docs/prompts/SKILL.md)
