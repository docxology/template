# Tests

```bash
uv run pytest projects/traditional_newspaper/tests/ --cov=projects/traditional_newspaper/src --cov-fail-under=90
```

No mocks: real PNG writes, real filesystem checks, real `matplotlib.image.imread`.
