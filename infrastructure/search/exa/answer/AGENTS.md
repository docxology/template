# `exa/answer` package (technical)

`ExaAnswerInterface` wraps `POST /answer` (`interface.py`). Returns
`AnswerResponse` (a synthesised `answer` plus `citations` as normalised
`ExaResult` records). Best for question-first UIs.

- Empty query raises `ExaError`.
- `text=True` asks Exa to include full source text on each citation.
- `system_prompt=` / `output_schema=` supported for source steering / structured
  answers. For new structured-search flows that need both retrieval control and
  grounded output, prefer `/search` + `output_schema` instead.

## Tests

```bash
uv run pytest tests/infra_tests/search/test_exa.py -q   # pytest-httpserver, no mocks
```
