# Style Guide - Literature Meta-Analysis Exemplar

## Source Code

- Keep pure computation in `src/`; scripts only orchestrate.
- Keep retrieval clients injectable: tests must be able to point clients at local `pytest-httpserver` URLs.
- Keep fallback imports explicit and narrow when a module should run both inside and outside the template monorepo.
- Keep random behavior seeded through config or constants. The default seed is `42`.
- Prefer typed dataclasses and small pure functions for records, assertions, variables, and metrics.

## Tests

Forbidden in project tests:

- `unittest.mock`
- `MagicMock`, `Mock`, `AsyncMock`, `patch`, `create_autospec`
- `mocker.patch`
- Assertions that only prove a function was called

Use real `Paper` objects, JSON/JSONL fixtures, `tmp_path`, and `pytest-httpserver` instead.

## Documentation And Claims

- Name exact producers: `src/analysis/pipeline_runner.py`, `src/literature/search_runner.py`, `src/manuscript/variables/`, etc.
- Link generated repo facts instead of hardcoding counts.
- Label synthetic fixture outputs as synthetic.
- Do not claim a live bibliometric result unless the corpus came from a live retrieval run and artifacts were regenerated.

## Paths

Use full project paths in commands from the repository root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
uv run python projects/templates/template_literature_meta_analysis/scripts/02_meta_analysis_pipeline.py
```

## Error Messages

Errors should name the missing input, the stage that should create it, and the command to regenerate it. Prefer:

```text
output/data/corpus.jsonl is missing; run scripts/01_literature_search.py for live retrieval or scripts/generate_fixture_corpus.py for the offline fixture.
```

over a generic `file not found`.
