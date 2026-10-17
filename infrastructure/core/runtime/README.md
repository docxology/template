# infrastructure/core/runtime/ - Runtime Helpers

Environment, checkpoint, retry, profiling, and dependency helpers.

`CodeProfiler` measures elapsed time with a monotonic clock and reports memory in
MB, retaining zero measurements. Benchmark iteration and warmup counts must be
exact integers (positive iterations, nonnegative warmup); requesting zero recent
metrics returns an empty list. Monitoring retains the caller's existing
`tracemalloc` session and records failures without replacing their exceptions.

Python 3.15's standard-library `profiling.tracing` can retain deterministic call
profiles without the process-memory access required by `profiling.sampling`.
These diagnostic profiles do not replace the supported Python 3.12–3.14 release
gates or authorize cache reuse, changed timeouts, or coverage exceptions.

## Files

- `_python_env.py` — Python environment helpers; Stage-02 scripts must resolve
  under the project `scripts/` tree and credential-like environment variables
  are redacted unless `ANALYSIS_ALLOW_SECRETS=1` is explicitly set.
- `python_binding.py` — explicit analysis interpreter, lexical venv prefix,
  binary/configuration and installed METADATA/RECORD declaration identity.
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

Analysis runs through the canonical audited Python stage worker. The selected
project `.venv/bin/python` is retained lexically so `sys.prefix` stays correct;
a present unusable venv blocks execution with 75. Execution performs no resolver
sync or acquisition. The worker observes its actual interpreter/version/site
roots before domain execution and checks them afterward, separately from the
controller's source/runtime fingerprint. Fresh private caches and a pre-import
CodeType audit bind public platform/project code and the held script bytes.

The selected installed dependency plane binds METADATA/RECORD declarations.
It does not prove all dependency member bytes. Consequently canonical analysis
capabilities and aliases cannot grant cache reuse, and a requested analysis
checkpoint requires a fresh run. Other eligible stages retain content-bound
reuse. Ignored `output/.pipeline/analysis/<run hash>/<stage hash>.json` receipts
retain original leaf exits, actual admitted worker evidence and controller
before/after identities; missing worker evidence cannot authorize completion.
Inherited core/live mode and the admitted build epoch reach each analysis
child. Exported non-Git execution requires explicit `SOURCE_DATE_EPOCH`.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)

## Prepared entry points and Stage00

Ordinary core/live execution uses an existing root `.venv/bin/python` or an
explicit absolute `TEMPLATE_ROOT_PYTHON`. Missing or broken preparation blocks
with 75 and never selects a substitute. The shell launcher first requires a finite nonce-bound actual CPython 3.12+
virtual-environment probe, then uses the mature public-source bytecode audit
and process guardian with private fresh caches. The functional probe does not
establish universal trust in a hostile nominated executable.
The probe, outer supervisor, and guardian use `-I -S`; they admit venv metadata
and package directories without executing `.pth` or `sitecustomize` startup
code. The actual CLI child retains normal `-I` site initialization inside the
guardian's deadline and descendant-cleanup boundary on Python 3.12–3.14.
Declared installed requirement names/versions establish availability, not
universal installed dependency-member custody.

Stage00 checks prepared Python, root requirements, pytest, build tools, source
structure, discovery, and setup-hook prerequisites. It does not clean coverage,
create output directories, sync packages, or run provisioning hooks. Structural
and malformed-check failures return 1; unavailable preparation returns 75.
Lexically present nonregular or linked setup-hook declarations fail strict
preflight, including a malformed fallback beside a valid preferred hook.
Run `uv sync --locked` and `bash scripts/shell/setup-system-deps.sh` explicitly
when preparation is authorized. `infrastructure.project.setup_hook.run_project_setup_hook`
remains an explicit provisioning API; ordinary pipelines call only its preflight.
