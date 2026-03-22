# tests/

32 tests, zero mocks, 100% coverage on `src/`.

```bash
uv run pytest projects/area_handbook/tests/ -v
```

`conftest.py` adds the project root to `sys.path` for `from src.*` imports.
