# AGENTS — tests/

- No mocks: real YAML fixtures, real rendered PDF/PPTX read back with
  `pypdf`/`python-pptx`, real repo introspection (`locate_repo_root`).
- Every new validator (`token_resolution`, `cliche_lint`, `diligence_audit`)
  needs a proof-of-detection test: confirm it fires on a deliberately-broken
  fixture, not only that the real content passes clean.
- `test_render_orchestration.py::test_render_all_decks_writes_real_artifacts`
  renders actual artifacts in a disposable project copy, preserving historical
  publication output bytes.
- Keep the suite fast; use `tmp_path` for anything that doesn't need to prove
  the real project's own content is clean.


The declared platform 4.0.1 SDK is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
