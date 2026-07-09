# Public vs. private, by construction

*Slide 28 of 56 — template_template pitch, long deck — kind: `content`*

- Only projects/templates/ is public and CI-gated; private working projects render locally through the same pipeline without ever being tracked.
- A dedicated audit (scripts/audit/check_tracked_all.py) enforces this on every push, not only at release time.
- The same separation pattern that lets a lab keep unpublished work private, while still exercising the identical tested pipeline, day to day.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
