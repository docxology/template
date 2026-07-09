# AGENTS — scripts/

- These are **thin orchestrators**. Content/validation logic belongs in
  `src/`; layout/rendering logic belongs in `infrastructure/rendering/`.
  Neither belongs here.
- Keep numeric prefixes so Stage-02 runs them in the right order (audit →
  diagrams → render → diligence audit).
- Use `_bootstrap.setup_paths()` / `get_logger()` so scripts work both
  standalone and under the orchestrator.
- Exit non-zero on real failure; never mask an error with `|| true`.
- `20_render_decks.py` must never claim success without the real six-artifact
  count matching (`src/render_orchestration.py::render_all_decks` raises if
  it doesn't).
