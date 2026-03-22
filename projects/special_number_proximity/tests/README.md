# tests/

```bash
uv run pytest projects/special_number_proximity/tests/ \
  --cov=projects/special_number_proximity/src --cov-fail-under=90
```

`conftest.py` sets `MPLBACKEND=Agg` and prepends `src/` to `sys.path`.
