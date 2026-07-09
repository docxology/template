# Layer 1 — infrastructure/

*Slide 17 of 56 — template_template pitch, long deck — kind: `content`*

- Generic, reusable modules: rendering (PDF/HTML/PPTX/DOCX/EPUB), validation, publishing, provenance, security.
- No project-specific logic lives here — a change to infrastructure/ affects every exemplar identically.
- This deck's own PDF/PPTX renderers (infrastructure/rendering/slide_deck.py, pptx_deck.py) are new additions to this same layer.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
