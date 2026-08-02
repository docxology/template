# template-pitch-deck skill — AGENTS.md

Project-scoped skill bundle for the `template_pitch_deck` exemplar.

| File | Purpose |
| --- | --- |
| [`SKILL.md`](SKILL.md) | The skill itself (frontmatter + canonical sections). |
| [`AGENTS.md`](AGENTS.md) | This file — folder contract. |
| [`README.md`](README.md) | Pointer for humans browsing the tree. |

## Audience

Agents that need to:

- Drive the in-repo exemplar end-to-end (audit, diagrams, charts, render, diligence).
- Fork this exemplar as the starting scaffold for a new pitch/grant-report deck.
- Verify layer boundaries and thin-orchestrator contracts after changes.

## Claim traceability

| Assertion | Source of truth |
| --- | --- |
| One content source renders to six artifacts | `src/render_orchestration.py::render_all_decks` (6-file count check) |
| Every fact token is read live, never hand-typed | `src/deck_tokens.py::build_deck_tokens` (live repo reads only) |
| Unresolved `{{TOKEN}}` fails the build | `src/token_resolution.py::resolve_tokens` (raises `UnresolvedTokenError`) |
| Cliché is a checked gate | `src/cliche_lint.py::lint_deck_texts` (word-boundary denylist) |
| Fact-bearing slides must carry a `source` citation | `src/diligence_audit.py::uncited_fact_slides` + `DiligenceAuditFailure` in `render_one_length` |
| PDF ↔ PPTX parity is load-bearing | shared font-size constants in `infrastructure/rendering/slide_deck.py`, imported by `pptx_deck.py` |
| Slide budgets 11/38/58 | `infrastructure/rendering/slide_deck.py::SlideBudget` |
| No-mocks testing, 90% src coverage floor | `tests/` + `pyproject.toml` `[tool.coverage.report] fail_under = 90` |

## Cross-refs

- Project root: [`../../..`](../../../).
- Project contract: [`../../../AGENTS.md`](../../../AGENTS.md).
