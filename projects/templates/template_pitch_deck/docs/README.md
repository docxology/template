# docs/ — template_pitch_deck

## What this repo is

A reproducible, validated **pitch-deck generation exemplar**: one
token-resolved content source renders to six real artifacts
(short/medium/long × PDF/PPTX), with every fact traced live to the repository,
cliché linting, citation-coverage (diligence) auditing, and per-slide QR
deep-links. Rendering logic itself lives in the monorepo's
`infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py`; this
project owns content, validation, and orchestration. See the repo
[`README.md`](../README.md) and [`../AGENTS.md`](../AGENTS.md).

## Directory map

| Path | Role |
| --- | --- |
| `src/` | Content loading, `{{TOKEN}}` resolution, cliché lint, diligence audit, live-repo fact tokens, chart rendering, render orchestration |
| `manuscript/` | Deck content YAMLs (`deck_content_*.yaml`) + the standard about-this-template manuscript (`00_abstract.md` … `99_references.md`) |
| `scripts/` | Thin orchestrators: audit → diagrams → charts → render → diligence audit |
| `tests/` | Zero-mock tests; rendered PDF/PPTX read back with `pypdf`/`python-pptx` |
| `output/` | `pdf/`, `pptx/`, `figures/`, `slides_standalone/` (never hand-edited) |

## How to run / test

From the template monorepo root (per repo `AGENTS.md`):

```bash
export PATH="$PWD/node_modules/.bin:$PATH"
uv run pytest projects/templates/template_pitch_deck/tests/ \
  --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90 -v
uv run python projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py
uv run python projects/templates/template_pitch_deck/scripts/20_render_decks.py
uv run python projects/templates/template_pitch_deck/scripts/30_audit_diligence.py
```

## Documentation in this tree

- [`AGENTS.md`](AGENTS.md) — agent-facing layout, gates, and conventions.
- Manuscript-specific rules: [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md).

## Status

Publication-track exemplar: `manuscript/` is complete and gate-guarded; this
docs/ tree was added by the docs-audit pass of 2026-08-29.
