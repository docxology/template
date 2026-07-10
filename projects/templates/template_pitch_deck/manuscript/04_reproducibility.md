# Reproducibility {#sec:reproducibility}

`scripts/render_decks.py` is deterministic: given the same repository state
(`manuscript/deck_content_*.yaml`, the live tokens from `src/deck_tokens.py`, and the
live facts `src/deck_tokens.py` reads from `template_template`'s own files
and the public exemplar roster), two consecutive runs produce byte-identical
PDF and PPTX output. No wall-clock timestamps appear in slide content; the
only place a generation time is recorded is deck metadata, following the
`STEGANOGRAPHY_DETERMINISTIC`-style convention already used elsewhere in this
repository for reproducible builds.

```bash
uv run python scripts/render_decks.py
# → output/pdf/template_template_pitch_{short,medium,long}.pdf
# → output/pptx/template_template_pitch_{short,medium,long}.pptx

uv run pytest projects/templates/template_pitch_deck/tests/ \
  --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90

uv run python scripts/audit/check_template_drift.py
```

This project participates in the standard multi-project pipeline like any
other public exemplar (`./run.sh --project templates/template_pitch_deck --pipeline --core-only`)
and requires no LLM/Ollama stage — deck content is authored and
token-resolved, not generated at render time by a model call, which keeps
the artifact deterministic and the core pipeline Ollama-optional.
