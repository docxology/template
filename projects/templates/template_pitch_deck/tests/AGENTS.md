# AGENTS — tests/

- No mocks: real YAML fixtures, real rendered PDF/PPTX read back with
  `pypdf`/`python-pptx`, real repo introspection (`locate_repo_root`).
- Every new validator (`token_resolution`, `cliche_lint`, `diligence_audit`)
  needs a proof-of-detection test: confirm it fires on a deliberately-broken
  fixture, not only that the real content passes clean.
- `test_render_orchestration.py::test_render_all_decks_writes_real_artifacts`
  writes into this project's real `output/` — that's intentional (outputs are
  disposable/regenerable), not a bug.
- Keep the suite fast; use `tmp_path` for anything that doesn't need to prove
  the real project's own content is clean.
