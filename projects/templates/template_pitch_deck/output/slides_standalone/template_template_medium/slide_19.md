# Two-layer architecture

*Slide 19 of 37 — template_template pitch, medium deck — kind: `content`*

- Layer 1 (infrastructure/): generic, reusable — rendering, validation, publishing, provenance, testing utilities.
- Layer 2 (projects/{name}/src/): domain-specific — each exemplar's own algorithms, kept out of infrastructure/ by convention and enforced by drift checks.
- Thin orchestrator scripts (projects/{name}/scripts/) coordinate the two layers but implement no business logic themselves.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_medium.pdf) · [PPTX](../../pptx/template_template_pitch_medium.pptx)
**Deck content source:** [manuscript/deck_content_medium.yaml](../../../manuscript/deck_content_medium.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
