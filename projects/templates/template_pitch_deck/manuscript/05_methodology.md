# Methodology {#sec:methodology}

The deck is generated deterministically from a structured content model rather
than authored slide-by-slide.

## Deck construction

`manuscript/deck_content_{short,medium,long}.yaml` are the single source of
truth for slide content across three lengths. `src/deck_tokens.py` resolves
live repository facts (`{{TOKEN}}` placeholders) from `template_template`'s own
`manuscript/config.yaml` and the public exemplar roster — never hand-typed
literals. `src/render_orchestration.py` then renders the resolved model into
PDF (via reportlab) and PPTX (via python-pptx) through `scripts/20_render_decks.py`,
with both renderers consuming one shared content model.

## Validation

Three offline audits run as real gates before the deck ships:

| Check | Tool | Failure mode |
| --- | --- | --- |
| Token resolution | `src/token_resolution.py` | any unresolved `{{TOKEN}}` fails the run |
| Cliché lint | `src/cliche_lint.py` | any stock pitch phrase fails the run |
| Diligence citations | `src/diligence_audit.py` | any fact-bearing slide lacking a source fails |

`scripts/10_audit_deck_content.py` runs the token and cliché checks in one pass;
`scripts/30_audit_diligence.py` enforces 100% fact-citation coverage across all
three lengths. PowerPoint/PDF slide-count parity is verified for every render.
