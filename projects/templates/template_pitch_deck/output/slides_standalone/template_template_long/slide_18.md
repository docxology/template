# Layer 2 — projects/{name}/src/

*Slide 18 of 56 — template_template pitch, long deck — kind: `content`*

- Each exemplar's own domain logic: template_template's introspection/metrics, a code-project's optimizer, this deck's own content loader and token/cliche validators.
- Kept out of infrastructure/ by convention, enforced by an automated project/infrastructure-boundary drift check.
- Thin orchestrator scripts (projects/{name}/scripts/) coordinate the two layers but implement no business logic themselves — a size/complexity gate enforces this directly.

---

**Source:** [projects/templates/template_template/src/template_template](https://github.com/docxology/template/blob/main/projects/templates/template_template/src/template_template)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
