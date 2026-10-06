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


The declared platform 4.0.0 SDK is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
