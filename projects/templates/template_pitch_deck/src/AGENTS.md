# AGENTS — src/

- Content-domain logic only. No layout/drawing code — that lives in
  `infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py`.
- Modules that import `infrastructure.*` must be declared in
  `../manuscript/layer_contract.yaml`'s `allow_infrastructure_imports` list
  (`content_loader.py`, `deck_tokens.py`, `render_orchestration.py` — see
  that file for why each is sanctioned).
- Never hand-type a fact into `deck_tokens.py` — every `PITCH_SUBJECT_*`/
  `EXEMPLAR_*` value must come from a live read of the repository.
- 90%+ test coverage required; no mocks — tests use real YAML, real rendered
  files read back with `pypdf`/`python-pptx`, real repo introspection.
