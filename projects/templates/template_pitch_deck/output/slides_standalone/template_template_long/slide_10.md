# Introspection

*Slide 10 of 56 — template_template pitch, long deck — kind: `content`*

- src/template_template/introspection.py discovers infrastructure/ subpackages, the pipeline.yaml stage DAG, and the public exemplar roster.
- The scan reads the filesystem and YAML directly — it does not depend on any external service or cached snapshot.
- Function-level entry points (discover_infrastructure_modules, discover_projects, load_pipeline_stages_from_yaml) each return typed, testable dataclasses.

---

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
