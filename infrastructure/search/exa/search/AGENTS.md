# `exa/search` package (technical)

`ExaSearchInterface` wraps `POST /search` (`interface.py`). Returns `SearchResponse`.

- Default content mode is `highlights=True` when no `text`/`summary`/`highlights`
  is requested. Content keys nest under `contents` on the wire (camelCase).
- `output_schema=` (+ `system_prompt=`) → synthesised JSON in `response.output`
  with field-level `grounding` (citations + confidence). Works on every `type`.
- Fail-fast guards (raise `ExaError` before the request): empty query, invalid
  `type` (see `config.VALID_SEARCH_TYPES`), and `category` `company`/`people`
  combined with `exclude_domains` or date filters (Exa returns HTTP 400).
- `None` kwargs are pruned from the payload (`models.prune`).

## Tests

```bash
uv run pytest tests/infra_tests/search/test_exa.py -q   # pytest-httpserver, no mocks
```
