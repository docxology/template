# Injection

*Slide 12 of 56 — template_template pitch, long deck — kind: `content`*

- inject_metrics.py substitutes ${variable} values into manuscript/*.md, writing the resolved text to output/manuscript/ for rendering.
- Unresolved tokens are never silently dropped — a missing variable is a build failure, not a blank space in the PDF.
- Re-running the pipeline regenerates the paper from current repository state — the citation and the artifact cannot drift apart.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
