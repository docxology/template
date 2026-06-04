# `exa/find_similar` package (technical)

`ExaFindSimilarInterface` wraps `POST /findSimilar` (`interface.py`). Returns the
same `SearchResponse` shape as `/search`; the query is a seed URL, not free text.
This is the one interface that reliably populates `ExaResult.score`.

- **Wire path is camelCase `/findSimilar`** — the kebab-case `/find-similar`
  returns HTTP 404 (verified live). Do not "normalise" it.
- Empty URL raises `ExaError`; defaults to `highlights=True`.
- `exclude_source_domain=True` drops pages from the seed URL's own domain.
- Content keys nest under `contents` (as for `/search`).

## Tests

```bash
uv run pytest tests/infra_tests/search/test_exa.py -q   # pytest-httpserver, no mocks
```
