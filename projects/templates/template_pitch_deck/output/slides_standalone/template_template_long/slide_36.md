# Why gates instead of a style guide

*Slide 36 of 56 — template_template pitch, long deck — kind: `content`*

- A style guide is a request; a gate is a build failure — the difference between 'we ask reviewers to check citations' and 'the render script exits non-zero if one is missing'.
- Each gate here targets one specific failure mode it was built to catch: a stale token, a cliche phrase, an uncited fact, a non-reproducible artifact.
- None of these gates existed before this exemplar needed them — each was added because a real defect surfaced during this project's own development, not speculatively.

---

**Source:** [projects/templates/template_pitch_deck/src/diligence_audit.py](https://github.com/docxology/template/blob/main/projects/templates/template_pitch_deck/src/diligence_audit.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
