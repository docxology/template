# Deck Rendering Architecture {#sec:architecture}

## Content model

`infrastructure/rendering/slide_deck.py` defines the format-agnostic content
model shared by both renderers:

- `Slide` — one slide's title, bullets, an optional speaker-notes string, an
  optional local figure path, and a `kind` — one of six layout hints:
  `title` (deck opener/closer), `section` (section-divider), `content`
  (default: title + bullets), `stat` (one large highlighted number +
  label), `quote` (a pull-quote + attribution), or `diagram` (title + a
  large full-bleed figure, e.g. a rendered Mermaid diagram).
- `DeckContent` — a deck title/subtitle plus an ordered tuple of `Slide`.
- `SlideBudget` — the three published maximum lengths (`SHORT` ≤ 11 slides,
  `MEDIUM` ≤ 38, `LONG` ≤ 58) and `filter_deck_for_budget`, a pure function
  that truncates a deck to a budget without mutating slide order or content.

## Two renderers, one model

`infrastructure/rendering/slide_deck.render_pdf` draws each slide directly
with ReportLab's canvas API onto a 16:9 page — no LaTeX/pandoc dependency,
following the same "project needs pixel-level layout control" reasoning that
led `template_newspaper` to a hand-written ReportLab engine, but implemented
as a generic, project-agnostic *format* renderer (like
`infrastructure/rendering/docx_renderer.py` or `epub_renderer.py`) rather than
a project-owned layout engine, because a slide deck — unlike a newspaper's
column geometry — is a reusable output shape any future project can consume.

`infrastructure/rendering/pptx_deck.render_pptx` builds the identical slide
sequence with `python-pptx` (an opt-in dependency:
`uv sync --group rendering-pptx`), matching title/section/content slide
handling 1:1 with the PDF path. Both renderers are exercised by
`tests/infra_tests/rendering/test_slide_deck.py` and
`test_pptx_deck.py`, including a direct parity test that renders the same
`DeckContent` through both paths and asserts the PDF page count equals the
PPTX slide count.

## Project-side content

`projects/templates/template_pitch_deck/src/` holds only pitch-deck-domain
code — loading `manuscript/deck_content_*.yaml` into `DeckContent` objects,
resolving `{{TOKEN}}` values, and linting for cliché — never layout/drawing
code. `scripts/20_render_decks.py` is the thin orchestrator that ties content
loading, token resolution, cliché linting, and the two infra renderers
together into the six published artifacts under
`output/{pdf,pptx}/`.
