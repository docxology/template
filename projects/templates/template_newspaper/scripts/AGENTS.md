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
