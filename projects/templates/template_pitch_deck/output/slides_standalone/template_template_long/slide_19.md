# Testing discipline

*Slide 19 of 56 — template_template pitch, long deck — kind: `content`*

- No mocks, anywhere: tests use real files, real YAML, real rendered output — never unittest.mock or MagicMock.
- 90% coverage floor on every exemplar's own src/; 60% floor on shared infrastructure/.
- A project fails its own gate the same way regardless of which exemplar it is — there is no per-project exception without an explicit, documented reason.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
