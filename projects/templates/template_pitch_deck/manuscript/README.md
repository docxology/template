# manuscript/

Two distinct things live here, deliberately kept apart:

1. **The pitch-deck content itself** — `deck_content_{short,medium,long}.yaml`
   and `config.yaml`'s `deck:` block (theme, source_base_url, pitch_subject).
   Rendered by `../scripts/20_render_decks.py` via
   `infrastructure/rendering/{slide_deck,pptx_deck}.py` into
   `../output/{pdf,pptx}/`. **Not** part of the standard manuscript pipeline.
2. **A short descriptive paper about this template** — the standard
   `00_abstract.md` … `99_references.md` chapters, `preamble.md`,
   `references.bib` — exists so the repository's Stage 03 (infrastructure
   manuscript renderer) produces a standard PDF for this project, exactly
   like every sibling exemplar.

> Do not confuse the two. The six pitch-deck artifacts are not this
> manuscript's own combined PDF.

Sections: `00_abstract` · `01_introduction` · `02_deck_architecture` ·
`03_content_and_validation` · `04_reproducibility` · `99_references`.
