# The chain of custody: slide → QR → GitHub

*Slide 42 of 56 — template_template pitch, long deck — kind: `content`*

- Every slide in this deck carries its own QR code, linking to a standalone, real Markdown page for that exact slide under output/slides_standalone/.
- Once this output/ directory is committed and pushed, a photo of a projected or printed slide can be traced back to its precise source page on GitHub — not just to the deck as a whole. Locally, the generated page already exists; the QR only resolves once it is actually published.
- Mechanically, this is the same source-citation system with one more hop: a citation links out to evidence; the QR links to the slide's own generated page, which repeats that same citation.

---

**Source:** [projects/templates/template_pitch_deck/src/standalone_slides.py](https://github.com/docxology/template/blob/main/projects/templates/template_pitch_deck/src/standalone_slides.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
