# `exa/contents` package (technical)

`ExaContentsInterface` wraps `POST /contents` (`interface.py`). Returns
`ContentsResponse`. Use for URLs you already have (DB, RSS, prior result `id`s)
or to refresh stale content via `max_age_hours`.

- Accepts a single URL or a sequence; empty input raises `ExaError`.
- Defaults to `highlights=True` when no content mode is given.
- **Content keys are top-level here** (`text`/`highlights`/`summary`), unlike
  `/search` and `/findSimilar` where they nest under `contents`. The interface
  handles this difference so callers never hit the documented mistake.

## Tests

```bash
uv run pytest tests/infra_tests/search/test_exa.py -q   # pytest-httpserver, no mocks
```
