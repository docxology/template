# `src/` — agent notes

This is the **only place project logic may live** (alongside generic
`infrastructure/` at the repo root). Scripts in `../scripts/` are thin
orchestrators: they import from `src/` and handle I/O — they never implement
algorithms, validation, or rendering.

## Rules for agents

- **Logic goes here, not in scripts.** If you find yourself computing a value or
  validating structure inside a script, move it into a `src/` module and import it.
- **Edit config, not the engine, to change content.** Chapters/labs/questions are
  declared in `manuscript/config.yaml`. The engine (`textbook.config`,
  `textbook.toc`, `textbook.content`) reads that file. Adding a chapter means
  adding a config entry, then running `scripts/scaffold_chapter.py`.
- **The contract is `textbook.constants`.** `CITATION_KEYS`, `GLOSSARY_ANCHORS`,
  `REQUIRED_SECTION_HEADINGS`, `REQUIRED_TOKENS`, and `STUB_MARKERS` define what a
  valid chapter must contain. `textbook.content.validate_chapter` enforces it and
  `textbook.audit.run_manuscript_audit` (via `scripts/audit_textbook_quality.py`)
  runs it as a gate.
- **Determinism.** `models.py` is pure/numeric; `visualization/` and `mermaid/`
  produce byte-stable output (fixed seeds, fixed style). Do not introduce
  wall-clock, randomness without a seed, or environment-dependent output.
- **90% coverage minimum.** Any new function needs a real, no-mocks test under
  `../tests/`. Verify with:

  ```bash
  uv run --extra dev python -m pytest ../tests --cov=src --cov-report=term-missing
  ```

## Module map

- `textbook/` — config, toc, content engine, audit gate, constants, worked models.
- `visualization/` — matplotlib figure generators (`plots.py`, YAML-driven
  `gallery.py`, `registry.py`, `_scaffold.py`).
- `mermaid/` — diagram specs (`diagram_specs.yaml`), `diagrams.py`, `renderer.py`.
- `textbook_{paths,io,logging,visuals}.py` — shared utilities.

Do not modify `manuscript/config.yaml`, `references.bib`, `glossary.md`, or any
chapter/lab/question markdown when changing the engine; those are authored content.
