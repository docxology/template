# Metrics and injection

*Slide 9 of 37 — template_template pitch, medium deck — kind: `content`*

- metrics.py turns the introspection scan into a dictionary of ${variable} values — the same token convention used across every exemplar's manuscript.
- inject_metrics.py substitutes those values into manuscript/*.md, writing the resolved text to output/manuscript/ for rendering.
- Re-running the pipeline regenerates the paper from current repository state — the citation and the artifact cannot drift apart.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_medium.pdf) · [PPTX](../../pptx/template_template_pitch_medium.pptx)
**Deck content source:** [manuscript/deck_content_medium.yaml](../../../manuscript/deck_content_medium.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
