# PyPI publishing

Build and upload Python packages to PyPI or TestPyPI (Stage opt-in).

## Entry points

| Symbol | Module | Role |
| --- | --- | --- |
| `PyPIAdapter` | `adapter.py` | Orchestrate build → upload → verify |
| `build_dist` | `build.py` | `uv build` — wheel + sdist |
| `upload_dist` | `upload.py` | `twine upload` with token auth |
| `verify_install` | `verify.py` | Smoke-test installability |

## Usage

```python
from pathlib import Path
from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

# Dry-run (default — no network upload)
adapter = PyPIAdapter(config=PyPIConfig(dry_run=True))
result = adapter.publish(project_dir=Path("projects/my_project"))
print(result.success, result.dist_files)

# Upload to TestPyPI
adapter = PyPIAdapter(config=PyPIConfig(dry_run=False, test=True))
result = adapter.publish(project_dir=Path("projects/my_project"))

# Upload to PyPI (requires PYPI_TOKEN in env)
adapter = PyPIAdapter(config=PyPIConfig(dry_run=False, test=False))
result = adapter.publish(project_dir=Path("projects/my_project"))
```

## Credentials

| Target | Env var |
| --- | --- |
| PyPI | `PYPI_TOKEN` |
| TestPyPI | `TESTPYPI_TOKEN` |

## Related

- [`AGENTS.md`](AGENTS.md) — module internals and file list
- [`../archival/`](../archival/) — multi-target archival mirror
