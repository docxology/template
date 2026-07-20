# Python runtime support

## Current contract

The root package keeps `requires-python = ">=3.10"` throughout the `3.6.x`
minor-release line. Python 3.10 is the compatibility floor, Python 3.12 is the
default local and release interpreter, and Python 3.13 is an explicit
infrastructure readiness lane in CI.

The floor will not move in a minor release. Dropping Python 3.10 requires an
explicit breaking release boundary (normally `4.0.0`), coordinated changes to
package metadata, every lockfile, CI matrices, containers, and contributor
documentation, plus a published migration note. The decision may be revisited
after Python 3.10 reaches end of life, but EOL alone does not silently change
the package contract.

## Enforcement

- Ubuntu infrastructure tests run on Python 3.10, 3.11, 3.12, and 3.13.
- The public-project matrix retains Python 3.10 floor and Python 3.12 default
  lanes; the full infrastructure 3.13 lane provides forward-readiness evidence.
- `infrastructure.core.runtime.python_compatibility` parses the public source
  surface with the Python 3.10 grammar and rejects unguarded standard-library
  APIs introduced in Python 3.11.
- Backports remain explicit (`tomli`, `typing-extensions`) and guarded imports
  must preserve a Python 3.10 branch.

Run the focused local contract with:

```bash
uv run pytest tests/infra_tests/core/runtime/test_python_compatibility.py -q
uv run pytest tests/infra_tests/project/test_export_smoke.py -q
```

Hosted CI remains the authoritative proof for interpreter-specific dependency
resolution and the complete supported-version matrix.
