# Style Guide - Advanced Literature Review Exemplar

## Source Code

- Keep pure computation in `src/`; scripts only orchestrate.
- Keep phase logic (`src/multi_phase/`, `src/literature/multi_phase_search.py`) reading its configuration from `manuscript/config.yaml` → `project_config.search_phases`; never hard-code a phase name, temporal boundary, or query string.
- Never edit a symlinked module's content through this project's path (`src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`, `src/visualization/`, `src/config_loader.py`). Confirm with `git status` which repository the edit actually landed in — see `architecture.md`.
- Keep retrieval clients injectable: tests must be able to point clients at local `pytest-httpserver` URLs.
- Keep random behavior seeded through config or constants. The default seed is `42`.
- Prefer typed dataclasses and small pure functions for records, assertions, phase metadata, and manuscript variables.

## Tests

Forbidden in project tests:

- `unittest.mock`
- `MagicMock`, `Mock`, `AsyncMock`, `patch`, `create_autospec`
- `mocker.patch`
- Assertions that only prove a function was called

Use real `Paper` objects, JSON/JSONL fixtures (including per-phase corpora),
`tmp_path`, and `pytest-httpserver` instead. See `testing_philosophy.md`.

## Documentation And Claims

- Name exact producers: `src/multi_phase/search.py`, `src/literature/multi_phase_search.py`, `src/manuscript/variables/extractors/multi_phase.py`, etc.
- Link generated repo facts instead of hardcoding corpus sizes, per-phase paper counts, or coverage percentages.
- Label the tracked corpus snapshot as tracked evidence, not a live empirical claim, per `AGENTS.md` Contracts.
- Do not claim a live cross-phase validation result unless `scripts/01_multi_phase_search.py` was run live and downstream artifacts were regenerated.
- State which modules are symlinked vs. project-specific when documenting architecture — see `architecture.md`.

## Paths

Use full project paths in commands from the repository root:

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90
uv run python projects/templates/template_advanced_literature_review/scripts/02_meta_analysis_pipeline.py
```

## Error Messages

Errors should name the missing input, the stage that should create it, and
the command to regenerate it, and should say which phase (if any) is
affected. Prefer:

```text
output/data/phase_2_jwst_corpus.jsonl is missing; run
scripts/01_multi_phase_search.py to refresh all configured phases.
```

over a generic `file not found`.
