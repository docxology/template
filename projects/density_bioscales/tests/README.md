# tests/

Run from repo root:

```bash
uv run pytest projects/density_bioscales/tests/ --cov=projects/density_bioscales/src --cov-fail-under=90
```

`conftest.py` sets `MPLBACKEND=Agg` and prepends `../src` to `sys.path`.
