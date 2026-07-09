---
name: template-pitch-deck
description: Pitch-deck generation exemplar — short/medium/long PDF+PPTX decks from one token-resolved, diligence-cited content source.
version: 1.0.0
author: docxology
license: MIT
tags: [exemplar, slides, reportlab, pptx, mermaid, pitch-deck]
---

# template-pitch-deck

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_pitch_deck/`. Load this when working inside the project.

## When to Use

- Working inside the `template_pitch_deck` exemplar — running scripts, editing content, or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new pitch/grant-report/stakeholder-update deck.
- Adding a new format-agnostic slide renderer to `infrastructure/rendering/` (e.g. this is the reference for `DeckContent`/`Slide`/`DeckTheme`).
- Validating that the exemplar's contracts (thin-orchestrator, token honesty, cliché lint, diligence citation coverage, no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run python projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py
uv run python projects/templates/template_pitch_deck/scripts/15_generate_diagrams.py
uv run python projects/templates/template_pitch_deck/scripts/20_render_decks.py
uv run python projects/templates/template_pitch_deck/scripts/30_audit_diligence.py
uv run pytest projects/templates/template_pitch_deck/tests --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90
uv run pytest tests/infra_tests/rendering/test_slide_deck.py tests/infra_tests/rendering/test_pptx_deck.py tests/infra_tests/rendering/test_mermaid_figure.py
```

PPTX rendering needs the opt-in group: `uv sync --group rendering-pptx`.

## Pitfalls

- **Keep scripts thin.** Content/validation logic belongs in this project's `src/`; layout/drawing logic belongs in `infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py` — never in `scripts/`.
- **No mocks.** All tests must use real YAML, real rendered files (read back with `pypdf`/`python-pptx`), real repo introspection.
- **Every fact-bearing slide needs a `source` citation.** `src/diligence_audit.py` fails the build otherwise (title-kind slides are exempt).
- **Never hand-type a fact.** All `PITCH_SUBJECT_*`/`EXEMPLAR_*` token values come from `src/deck_tokens.py::build_deck_tokens`, which reads them live from the repo — adding a new fact means adding a new live read, not a literal.
- **PDF/PPTX parity is load-bearing.** The two renderers must always produce identical slide counts, text, AND font sizes for the same `DeckContent` — a change to one renderer's slide-kind dispatch or font-size constant needs the matching change in the other (see `test_render_pptx_slide_count_matches_render_pdf_page_count`; font sizes are imported from `slide_deck.py` into `pptx_deck.py`, never re-declared).
- **QR codes need a real `source_base_url`.** `Slide.qr_url` (drawn bottom-right, both renderers) is only populated when `manuscript/config.yaml`'s `deck.source_base_url` is non-empty — `attach_qr_urls` is a no-op otherwise. New infra capabilities (QR generation reuses `infrastructure.steganography.barcode_generators.generate_qr_code`) need their transitive dependency (`qrcode[pil]`) declared in THIS project's own `pyproject.toml`, not just the root repo's — see the isolated-venv pitfall below.
- **Isolated-venv dependency check is not a one-time step.** Every time new code imports a not-yet-used `infrastructure.*` capability, re-run `uv run python scripts/pipeline/stage_01_test.py --project templates/template_pitch_deck --project-only` (not a bare root-venv `pytest`) — it is the only thing that catches a transitive dependency (reportlab/pypdf/Pillow/qrcode so far) missing from this project's own `pyproject.toml`.
- **Outputs are disposable.** Never hand-edit `output/`; regenerate from `manuscript/` + `src/`. This includes `output/slides_standalone/*.md` — generated per-slide pages, not hand-authored.
- **Run from the repo root.** Commands assume the template monorepo root as working directory.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Rendering primitives: `infrastructure/rendering/slide_deck.py`, `pptx_deck.py`, `mermaid_figure.py`
- Exemplar roster: [`projects/AGENTS.md`](../../../../AGENTS.md)
