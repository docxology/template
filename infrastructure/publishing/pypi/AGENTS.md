# `infrastructure/publishing/pypi/`

Build, upload, and verify Python packages to PyPI or TestPyPI.

## Public API

```python
from infrastructure.publishing.pypi import (
    PyPIAdapter,
    PyPIConfig,
    PyPIResult,
    build_dist,
    upload_dist,
    verify_install,
)
```

### `PyPIAdapter`

High-level façade: build → upload → verify in one call.

```python
adapter = PyPIAdapter(config=PyPIConfig(dry_run=True))
result: PyPIResult = adapter.publish(project_dir=Path("projects/my_project"))
```

`dry_run=True` is the default at every layer — accidental imports cannot trigger
real uploads.

### `PyPIConfig`

| Field | Default | Env override |
| --- | --- | --- |
| `dry_run` | `True` | — |
| `test` | `False` | — (set `True` for TestPyPI) |
| `token` | — | `PYPI_TOKEN` / `TESTPYPI_TOKEN` |
| `repository_url` | auto | derived from `test` flag |

### `PyPIResult`

Dataclass returned by every operation: `success`, `package_name`, `version`,
`dist_files`, `url`, `error`.

### Lower-level helpers

| Symbol | Module | Role |
| --- | --- | --- |
| `build_dist` | `build.py` | `uv build` — produces `dist/` wheel + sdist |
| `upload_dist` | `upload.py` | `twine upload` with token auth |
| `verify_install` | `verify.py` | `pip install --dry-run` from index or dist file |

## Files

| File | Purpose |
| --- | --- |
| `__init__.py` | Re-exports public symbols |
| `models.py` | `PyPIConfig`, `PyPIResult` dataclasses |
| `build.py` | `build_dist()` — invokes `uv build` in subprocess |
| `upload.py` | `upload_dist()` — invokes `twine upload` with token |
| `verify.py` | `verify_install()` — smoke-tests installability |
| `adapter.py` | `PyPIAdapter` — orchestrates build → upload → verify |

## Credentials

Tokens are read from environment variables only — never logged:

- **PyPI**: `PYPI_TOKEN`
- **TestPyPI**: `TESTPYPI_TOKEN`

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_pypi.py -v
```

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md) — publishing module overview
