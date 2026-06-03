# `exa/contents` — `POST /contents`

Clean parsed content for URLs you already have (from a DB, RSS, or prior search
`id`s). `ExaContentsInterface.get(urls, ...)`.

- Content keys (`highlights`/`text`/`summary`) are **top-level** here — unlike
  `/search`, where they nest under `contents`.
- `max_age_hours=0` forces a livecrawl; `-1` never livecrawls (cache only).

```python
client.contents(["https://example.com/post"], text={"maxCharacters": 20000})
```
