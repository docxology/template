# AGENTS.md — docs/ for template_pitch_deck

Agent-facing notes for this documentation tree. The nearest authoritative
contracts are [`../AGENTS.md`](../AGENTS.md) (exemplar), [`../src/AGENTS.md`](../src/AGENTS.md),
[`../scripts/AGENTS.md`](../scripts/AGENTS.md), and
[`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — each wins over this file.

## Layout

- `src/` — content-domain logic only; no layout/drawing code. Modules that
  import `infrastructure.*` must be declared in
  `../manuscript/layer_contract.yaml`'s `allow_infrastructure_imports`.
- `scripts/` — thin orchestrators; numeric prefixes are order-sensitive
  (audit → diagrams → render → diligence audit). They exit non-zero on real
  failure; never mask an error with `|| true`.
- `manuscript/` — two distinct things live there: the deck content YAMLs and
  the standard manuscript. Do not conflate them.

## Validation gates (from repo AGENTS.md)

1. Unresolved-token detection — `src/token_resolution.py` raises loudly on any
   `{{TOKEN}}` with no resolved value; never silently ship a literal.
2. Cliché denylist — `src/cliche_lint.py`, word-boundary regex, case-insensitive.
3. Diligence/citation coverage — every slide referencing a
   `PITCH_SUBJECT_*`/`EXEMPLAR_*` fact token needs a `source` citation; a
   `DiligenceAuditFailure` blocks that deck length's PDF/PPTX write.
4. Never hand-type a fact into `src/deck_tokens.py`; every value comes from a
   live repository read, raising rather than fabricating when unavailable.

## Conventions observed in this repo

- Zero-mock tests: real YAML, real rendered files read back, real introspection.
- Publication identifiers in `manuscript/config.yaml` are real and recorded;
  never set a placeholder `github_repository` or fake DOI (placeholder flips
  the PUBLISHING-STATUS block to a false "published" state).
- Never hand-edit `output/`; regenerate through the render orchestration.

## How docs here are maintained

- Keep this tree short and factual; one file per concern.
- Measured counts belong in the monorepo's generated
  `docs/_generated/COUNTS.md`, not here.
