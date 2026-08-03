# AGENTS — scripts/

- These are **thin orchestrators**. Logic belongs in `src/newspaper/`, not here.
- Keep numeric prefixes so Stage-02 runs them in the right order (preflight →
  figures → render). Figures must precede the render.
- Use `_bootstrap.setup_paths()` / `get_logger()` so scripts work both standalone
  and under the orchestrator (graceful logger fallback when `infrastructure` is
  absent).
- Exit non-zero on real failure; never mask an error with `|| true`.
- Don't print the newspaper PDF as "done" without the render report confirming
  `all_pages_fit`.

## File inventory

| File | Role |
| --- | --- |
| [`_bootstrap.py`](_bootstrap.py) | Standalone/orchestrated path and logger setup. |
| [`00_preflight.py`](00_preflight.py) | Validate dependencies and load the edition. |
| [`10_generate_figures.py`](10_generate_figures.py) | Generate the deterministic figure set. |
| [`20_render_newspaper.py`](20_render_newspaper.py) | Render the newspaper and write the render report. |
