# AGENTS — manuscript/

- Two distinct things live here: the pitch-deck content
  (`deck_content_{short,medium,long}.yaml` + `config.yaml`'s `deck:` block)
  and the standard "about this template" manuscript (`00_abstract.md` …
  `99_references.md`). Do not conflate them — the deck artifacts are not
  this manuscript's own combined PDF.
- Every `{{TOKEN}}` referenced in `deck_content_*.yaml` must resolve via
  `src/deck_tokens.py::build_deck_tokens` — never hand-add a fact without a
  live-read source.
- Any slide bullet/title/stat/quote referencing a `PITCH_SUBJECT_*`/`EXEMPLAR_*`
  token needs a `source` citation on that slide (see `src/diligence_audit.py`).
- `config.yaml`'s `publication:` block stays empty until a real DOI/GitHub
  repo exists — never set a placeholder `github_repository` (it flips the
  PUBLISHING-STATUS block to a false "published" state).
