# This deck audits itself

*Slide 41 of 56 — template_template pitch, long deck — kind: `content`*

- src/token_resolution.py fails the build on any unresolved double-curly-brace placeholder — the same discipline this slide's own template_template token was resolved by.
- src/cliche_lint.py and src/diligence_audit.py both run inside render_orchestration.py itself, before that deck length's own PDF/PPTX is written — a slide referencing a live-sourced token with no citation blocks that length's render, it does not just fail a separate, skippable check.
- None of these checks are generic infrastructure — they are this project's own src/, built specifically because a pitch deck is exactly the kind of document that tempts unverifiable claims.

---

**Source:** [projects/templates/template_pitch_deck/src/diligence_audit.py](https://github.com/docxology/template/blob/main/projects/templates/template_pitch_deck/src/diligence_audit.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
