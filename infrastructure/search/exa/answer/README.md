# `exa/answer` — `POST /answer`

A grounded answer with citations, for question-first UIs.
`ExaAnswerInterface.answer(query, ...)`.

- `text=True` includes full source text on each citation.
- For structured-search flows that need retrieval control **and** grounded
  output, prefer `exa/search` + `output_schema` instead.

```python
resp = client.answer("what is retrieval-augmented generation?")
print(resp.answer, [c.url for c in resp.citations])
```
