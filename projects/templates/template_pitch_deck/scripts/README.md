# scripts/

Thin orchestrators for the pitch-deck pipeline, run in lexicographic order
by Stage 02 (`discover_analysis_scripts`):

| Script | Role |
|--------|------|
| `10_audit_deck_content.py` | Token resolution + cliché lint audit (fails closed) |
| `15_generate_diagrams.py` | Render Mermaid diagrams to PNG (degrades gracefully without `mmdc`/Chrome) |
| `16_generate_charts.py` | Render matplotlib charts (coverage bar, coverage scatter, infra subpackage donut) via `src/chart_rendering.py` |
| `20_render_decks.py` | The six-artifact render (delegates to `src/render_orchestration.py`) |
| `30_audit_diligence.py` | Fact-citation coverage audit |

`_bootstrap.py` is shared (not itself an analysis script — excluded from
Stage 02 discovery by its leading underscore).
