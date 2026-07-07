# FAQ

## Is the default modafinil corpus empirical evidence?

No. The committed fixture is synthetic and exists so the full pipeline can run offline. Live claims require live retrieval plus regenerated artifacts.

## Where do I change the topic?

Edit `manuscript/config.yaml`: `project_config.search.term`, query strings, relevance keywords, subfield keywords, and hypothesis definitions.

## Why are mocks forbidden?

The important behavior is data transformation: parsing records, de-duplicating papers, computing metrics, producing figures, and hydrating manuscript variables. Real fixtures and local HTTP servers test that behavior directly.

## How do I add a retrieval source?

Add a client under `src/literature/`, make its base URL injectable, test it with `pytest-httpserver`, then wire it through `src/literature/search_runner.py` and config toggles.

## How do I add a manuscript variable?

Add the value in `src/manuscript/variables/compute.py` (or the relevant extractor under `src/manuscript/variables/extractors/`), add or update a test in `tests/test_variables.py`, then reference `{{TOKEN}}` in manuscript source and rerun `scripts/05_inject_variables.py`.

## Which generated files can be committed?

None under project-local `output/`. Commit source, config, fixtures, tests, and docs. Generated output is disposable.
