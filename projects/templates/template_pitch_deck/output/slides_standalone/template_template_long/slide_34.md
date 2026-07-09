# Independent gates, not one

*Slide 34 of 56 — template_template pitch, long deck — kind: `content`*

- No-mocks testing policy, CI-enforced: scripts/audit/verify_no_mocks.py fails the build if any test imports MagicMock, mocker.patch, or unittest.mock — a checked gate, not a style preference.
- Coverage floors are enforced per project (90%) and for shared infrastructure (60%), not averaged away across the monorepo.
- A byte-level reproducibility invariant: two renders of identical content in the same environment produce an identical PDF — verified by a real, passing test, not assumed across every OS/toolchain combination.

---

**Source:** [tests/infra_tests/rendering/test_slide_deck.py](https://github.com/docxology/template/blob/main/tests/infra_tests/rendering/test_slide_deck.py)

**Full deck:** [PDF](../../pdf/template_template_pitch_long.pdf) · [PPTX](../../pptx/template_template_pitch_long.pptx)
**Deck content source:** [manuscript/deck_content_long.yaml](../../../manuscript/deck_content_long.yaml)

*This page is generated — it exists so a QR code on the rendered slide can point somewhere real and citable on GitHub, not just at the deck as a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*
