# How it works

*Slide 4 of 11 — template_template pitch, short deck — kind: `content`*

- src/template_template/introspection.py scans infrastructure/ modules, the pipeline DAG, and the public project roster.
- metrics.py turns that scan into a dictionary of ${variable} values; inject_metrics.py substitutes them into the manuscript text.
- Re-running the pipeline regenerates the paper from current repository state — the citation and the artifact cannot drift apart.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_short.pdf) · [PPTX](../../pptx/template_template_pitch_short.pptx)
**Deck content source:** [manuscript/deck_content_short.yaml](../../../manuscript/deck_content_short.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
