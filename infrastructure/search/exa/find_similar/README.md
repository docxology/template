# `exa/find_similar` — `POST /findSimilar`

Semantically similar pages for a seed URL. Same response shape as `/search`.
`ExaFindSimilarInterface.find_similar(url, ...)`.

- `exclude_source_domain=True` drops results from the seed URL's own domain.
- Supports the same domain/date filters and `contents` content modes as search.

```python
client.find_similar("https://arxiv.org/abs/1706.03762", num_results=5, exclude_source_domain=True)
```
