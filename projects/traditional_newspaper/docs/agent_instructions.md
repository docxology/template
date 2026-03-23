# Agent instructions — `traditional_newspaper`

Hard constraints for edits under `projects/traditional_newspaper/`.

## Module boundaries

- **Business logic** lives in `src/newspaper/` only (`layout_spec`, `sections`, `snippets`, `content`, `masthead`, `layout_figure`, `visualization`).
- **Scripts** in `scripts/` are thin orchestrators: path bootstrap, logging, call into `newspaper.*`, print absolute output paths on stdout for the analysis manifest.
- **No imports** from other projects under `projects/`. Infrastructure imports (`infrastructure.*`) are allowed where scripts already use them (for example logging).

## Determinism

- Masthead rendering uses a fixed default seed in `render_masthead_png` unless callers override; do not introduce unseeded randomness in figures used by tests or CI.
- Fixture copy in `content.py` must remain reproducible for a given seed.

## Testing

- Do not add `unittest.mock`, `MagicMock`, `mocker.patch`, or `@patch`.
- Prefer subprocess for script integration (see `tests/test_script_stats.py`, `tests/test_visualization_script.py`).
- Keep `MPLBACKEND=Agg` behavior compatible with `tests/conftest.py`.

## Analysis script order

- Project scripts run in **sorted basename order**. `visualization_wordcount_bw.py` must stay after `report_manuscript_stats.py` so `manuscript_stats.json` exists. `generate_section_banners.py` has no ordering constraint relative to stats.

## Manuscript

- Core folios `01_*.md` … `16_*.md` are required; optional tracked names are defined in `sections.MANUSCRIPT_OPTIONAL_FILENAMES` (S01–S03, `98_*.md`).
- Changing slice order or required files requires updating `sections.py`, `validate_inventory` expectations in tests, and manuscript docs together.

## Documentation

- Prefer explicit file paths in docs and comments over vague references.
- After structural changes, update [../AGENTS.md](../AGENTS.md) and the relevant doc in this folder.
