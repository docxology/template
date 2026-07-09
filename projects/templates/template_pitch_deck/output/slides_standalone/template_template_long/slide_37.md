# What happens when a gate fails

*Slide 37 of 56 — template_template pitch, long deck — kind: `content`*

- scripts/10_audit_deck_content.py exits non-zero on the first unresolved token or cliche hit — the render script never runs against unaudited content.
- scripts/30_audit_diligence.py exits non-zero if any fact-bearing slide lacks a source citation — a deck can be complete and still fail to ship.
- Fail-closed, not fail-open: an audit that cannot run is treated as a failure, never silently skipped and reported as a pass.

---

**Source:** [projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py](https://github.com/docxology/template/blob/main/projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
