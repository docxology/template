# scripts/

Thin orchestrators for the pitch-deck pipeline, run in lexicographic order
by Stage 02 (`discover_analysis_scripts`):

| Script | Role |
|--------|------|
| `10_audit_deck_content.py` | Token resolution + cliché lint audit (fails closed) |
| `15_generate_diagrams.py` | Render all required Mermaid diagrams to PNG; fails closed without `mmdc`/Chrome |
| `16_generate_charts.py` | Render matplotlib charts (coverage bar, coverage scatter, infra subpackage donut) via `src/chart_rendering.py` |
| `20_render_decks.py` | The six-artifact render (delegates to `src/render_orchestration.py`) |
| `30_audit_diligence.py` | Fact-citation coverage audit |

`_bootstrap.py` is shared (not itself an analysis script — excluded from
Stage 02 discovery by its leading underscore).


The platform SDK pinned in this project's package metadata and lock is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
