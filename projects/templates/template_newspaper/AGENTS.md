# AGENTS — `template_newspaper`

Guidance for AI agents and contributors working in this project. Read this
before editing. It mirrors the sibling templates' agent contract.

## What this project is

A pure-Python **newspaper layout engine** that renders a 12-page large-format
PDF (*The Triplicate*) from structured YAML. It is a canonical monorepo exemplar
alongside `template_code_project` and `template_prose_project`, and obeys the
same project contract.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## The one rule that matters

**Content is data; the engine is the press.** Editions live in `content/`. If a
change to the *newspaper's words or sections* requires editing `src/`, that is a
bug in the abstraction — fix the engine to be driven by data instead.

## Directory contract

| Path | Role | Edit when… |
|------|------|-----------|
| `src/newspaper/` | the engine (9 modules) | adding a layout *capability* |
| `content/` | the edition (YAML) | changing *this paper's* content |
| `scripts/` | Stage-02 orchestrators (preflight, figures, render) | changing the pipeline wiring |
| `manuscript/` | descriptive paper for Stage-03 infra render | documenting the engine |
| `tests/` | pytest suite | always, alongside engine changes |
| `output/` | generated artifacts (PDF, figures, reports) | never by hand |
| `docs/` | human documentation | when behavior changes |

## Verification is non-negotiable

This project's correctness is **visual**. After any layout or content change:

1. `uv run python scripts/10_generate_figures.py && uv run python scripts/20_render_newspaper.py`
2. Raster pages with `pdftoppm -png -r 100 output/pdf/the-triplicate.pdf /tmp/p`
   and **look at them**. Do not claim a layout works from code alone.
3. `uv run pytest`, `uv run mypy src/newspaper`, `uvx ruff check src scripts tests`.

`RenderResult.all_pages_fit == False` means content was dropped off a page —
treat it as a failure, not a warning.

## Gotchas (learned the hard way)

- **`.ttc` subfont order is face-specific.** Didot is `0=Regular, 1=Italic,
  2=Bold`. Verify with `TTFont(name, path, subfontIndex=i).face` before trusting.
- **Compact boxes do not fill a 15″ column** — prose does. Under-set feature
  pages need a long article, not more small boxes.
- **Classifieds must flow unboxed** (`classified` template) to pack densely;
  use the `display` box kind only for boxed house ads.
- Only `typography.py` may name a font. Everything else uses `Fonts` roles.
