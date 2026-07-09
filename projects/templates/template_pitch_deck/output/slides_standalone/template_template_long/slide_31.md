# What reproducible means here

*Slide 31 of 56 — template_template pitch, long deck — kind: `content`*

- Fixed RNG seeds and MPLBACKEND=Agg for headless, deterministic figure generation.
- Two consecutive pipeline runs against the same repository state produce byte-identical rendered output.
- Coverage and test counts are read from a generated report (docs/_generated/COUNTS.md), never hardcoded into prose that could go stale.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
