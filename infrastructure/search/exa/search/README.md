# `exa/search` — `POST /search`

Exa's primary neural/keyword search. `ExaSearchInterface.search(query, ...)`.

- Defaults to token-efficient **highlights**; pass `text=`/`summary=` to change.
- Pass `output_schema=` (+ `system_prompt=`) for synthesised, grounded JSON in
  `response.output` (works on every `type`).
- `type`: `auto` (default) · `fast` · `instant` · `deep-lite` · `deep` · `deep-reasoning`.
- Guards: empty query, invalid `type`, and the `category` `company`/`people`
  filter conflict all raise `ExaError` before the request.

```python
client.search("rust async runtime comparison", num_results=10, include_domains=["docs.rs"])
```
