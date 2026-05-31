# tasks/

Validate layout with:

```bash
uv run python -m infrastructure.sia.cli validate tasks/mini_classify
```

Each task must expose `data/public/`, `data/private/`, and `reference/` per the SIA contract.
