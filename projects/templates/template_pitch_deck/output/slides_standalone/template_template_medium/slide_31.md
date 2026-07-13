# Not a black box

*Slide 31 of 37 — template_template pitch, medium deck — kind: `content`*

- 25 importable subpackages, 687 tracked Python files total under infrastructure/ — a real inventory anyone can `git ls-files` themselves, not a claimed abstraction.
- The largest single subpackage, core, holds 113 files — still a minority of the whole, not a monolith wearing a modular label.
- Every number on this slide is computed live by src/infra_facts.py at render time, reusing the exact same counters docs/_generated/COUNTS.md is built from.
- The chart on the next slide shows a slightly narrower total — it only counts files inside an importable subpackage, excluding 2 top-level file(s) (infrastructure/__init__.py, mcp_server.py) that do not belong to any subpackage.

---

**Source:** [projects/templates/template_pitch_deck/src/infra_facts.py](https://github.com/docxology/template/blob/main/projects/templates/template_pitch_deck/src/infra_facts.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_medium.pdf) · [PPTX](../../pptx/template_template_pitch_medium.pptx)
**Deck content source:** [manuscript/deck_content_medium.yaml](../../../manuscript/deck_content_medium.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
