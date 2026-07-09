# Why partition it this way

*Slide 47 of 56 — template_template pitch, long deck — kind: `content`*

- Each subpackage boundary matches a real reuse boundary: rendering/, validation/, publishing/, provenance/ each solve one generic problem every exemplar needs, independent of any project's domain logic.
- A change inside one subpackage cannot silently reach into another without an explicit import — the boundary is enforced by the drift check, not just convention.
- This is the same two-layer split described earlier in this deck, now shown at the resolution of individual subpackages instead of the whole layer.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
