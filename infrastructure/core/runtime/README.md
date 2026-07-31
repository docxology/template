# infrastructure/core/runtime/ - Runtime Helpers

Environment, checkpoint, retry, profiling, and dependency helpers.

## Files

- `_python_env.py` — Python environment helpers; Stage-02 scripts must resolve
  under the project `scripts/` tree and credential-like environment variables
  are redacted unless `ANALYSIS_ALLOW_SECRETS=1` is explicitly set.
- `_packages.py`
- `_directories.py`
- `checkpoint.py`
- `environment.py`
- `env_deps.py`
- `setup_checks.py`
- `python_compatibility.py`
- `eta.py`
- `function_profiler.py`
- `health_check.py`
- `retry.py`

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
