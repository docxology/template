# src/ — pitch-deck content, tokens, and validation

Content-domain logic only — no layout/drawing code (that lives in
`infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py`). Modules:

| Module | Responsibility |
|--------|----------------|
| `paths.py` | repo-root discovery |
| `deck_tokens.py` | live repo introspection → `{{TOKEN}}` values (test counts, coverage, DOI, exemplar roster) |
| `token_resolution.py` | `{{TOKEN}}` substitution, raises on any unresolved reference |
| `cliche_lint.py` | word-boundary-safe pitch-deck cliché denylist |
| `content_loader.py` | `manuscript/deck_content_*.yaml` → token-resolved `DeckContent`/`Slide` |
| `deck_audit.py` | shared token+cliche audit, used by both `scripts/10_audit_deck_content.py` and `scripts/20_render_decks.py` |
| `diligence_audit.py` | fact-token → `source`-citation coverage check; wired both into `scripts/30_audit_diligence.py` and directly into `render_orchestration.py` as a render-blocking gate |
| `standalone_slides.py` | per-slide standalone `.md` pages + deterministic per-slide QR deep-link URL computation |
| `coverage_chart_data.py` | live `docs/_generated/COUNTS.md` → per-exemplar `(name, test_count, coverage_pct)` rows, for `scripts/16_generate_charts.py` |
| `infra_facts.py` | live `infrastructure/` subpackage/file counts (reuses `infrastructure.documentation.counts_doc`), `INFRA_*` tokens |
| `chart_rendering.py` | matplotlib plotting logic (bar/scatter/donut) for `scripts/16_generate_charts.py` — moved here from the script once it exceeded the thin-orchestrator line/function threshold |
| `render_orchestration.py` | ties audit → diligence-gate → standalone-pages → QR-attach → render into one call per deck length |

See `../AGENTS.md` for the full architecture.
