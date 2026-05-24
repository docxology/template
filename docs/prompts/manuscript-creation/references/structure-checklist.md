# Manuscript structure checklist

Copy the closest exemplar under `projects/template_code_project/`, `projects/template_prose_project/`, or local `projects_archive/template_search_project/`.

## Typical files

- Main sections: `01_abstract.md` … (match exemplar numbering)
- Supplemental: `S01_*` when exemplar uses them
- `98_symbols_glossary.md`, `99_references.md`
- `config.yaml`, `references.bib`, `preamble.md`

## src/ modules (code-centric exemplar pattern)

- Domain algorithms in flat or small modules under `src/`
- `validation.py`, `visualization.py` as needed
- All public APIs typed and logged

## scripts/

- Import from `src/` and `infrastructure/`
- Write under `projects/<name>/output/`
- Fixed RNG seeds for stochastic steps

## Pipeline integration

After scaffold: `./run.sh --project <name> --pipeline --core-only` (or project tests first).
