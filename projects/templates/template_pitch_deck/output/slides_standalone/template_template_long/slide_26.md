# What makes an exemplar 'public'

*Slide 26 of 56 — template_template pitch, long deck — kind: `content`*

- A single hand-edited registry (infrastructure/project/public_scope.py) lists every project name in public CI/documentation scope.
- Everything else under projects/ (working, ongoing, archive folders) stays local-only by construction, never accidentally published.
- An automated confidentiality audit fails CI if a private project path is ever tracked by mistake.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
