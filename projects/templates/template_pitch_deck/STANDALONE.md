# Standalone Fork Guide

## Purpose

`template_pitch_deck` is a reproducible, token-validated pitch-deck
generation exemplar — one content source renders to short/medium/long
PDF+PPTX decks via new generic `infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py`
primitives.

## Copy This When

Use it when a fork needs to pitch its own work — a grant report, a recurring
stakeholder update, a partner pitch — as a reproducible, fact-checked build
artifact rather than a hand-maintained slide deck.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_pitch_deck \
  --dest projects/working/my_pitch_deck \
  --new-name my_pitch_deck
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude '*.egg-info/' \
  projects/templates/template_pitch_deck/ projects/working/my_pitch_deck/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml` (`deck.pitch_subject`, `deck.theme`, `deck.source_base_url`), `CITATION.cff`-equivalent metadata, and author/publication fields.
- Replace `manuscript/deck_content_{short,medium,long}.yaml` with your own pitch narrative; update `src/deck_tokens.py::build_deck_tokens` to source facts from whatever project/organization you are pitching (it does not have to be another exemplar in this monorepo).
- Every slide referencing a live-sourced fact token needs a `source` citation — `src/diligence_audit.py` enforces this; extend `FACT_TOKEN_PREFIXES` if your fork's token naming differs.
- `infrastructure/rendering/{slide_deck,pptx_deck}.py` are shared, generic infrastructure — do not fork those; only the project-local `manuscript/` and `src/` content should change.
