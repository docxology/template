# infrastructure/core/runtime/ - Runtime Helper Documentation

## Purpose

The `infrastructure/core/runtime/` package contains runtime helpers for environment setup, dependency checks, checkpointing, profiling, health, and retry behavior.

## Files

- `_python_env.py` - Python environment helpers, confined analysis-script paths,
  and fail-closed analysis subprocess environments
- `python_binding.py` - lexical selected interpreter and installed dependency
  declaration identity, with actual worker runtime observation and conservative
  canonical analysis cache/resume refusal (see README for proof boundaries)
- `_packages.py` - package detection helpers
- `_directories.py` - directory helpers
- `checkpoint.py` - pipeline checkpointing
- `environment.py` - environment validation
- `env_deps.py` - dependency helpers
- `prepared_runtime.py` / `prepared_dispatch.py` - existing selected root runtime, declared requirement availability, and finite audited CLI dispatch without acquisition
- `setup_checks.py` - Stage 0 check-only orchestration and aggregate `run_environment_setup_checks` service (used by `scripts/pipeline/stage_00_setup.py`)
- `python_compatibility.py` - Python 3.12 syntax/API floor scanner and tested-runtime contract
- `eta.py` - ETA helpers
- `function_profiler.py` - function profiling
- `health_check.py` - health checks
- `retry.py` - retry helpers

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)

## Checkpoint recovery

Checkpoint loading validates integer stage counters, finite nonnegative runtime
measurements, stage result shapes, and optional output digests before resume.
Malformed persisted fields produce an unavailable checkpoint instead of crashing
the pipeline. Failed serialization, digest reads, or writes leave the previous
valid checkpoint intact. New checkpoint files use private `0600` permissions.
The executor passes the resolved project directory so lifecycle projects keep
checkpoints alongside their own outputs.
