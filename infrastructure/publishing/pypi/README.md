# PyPI publishing

`PyPIAdapter` previews the canonical platform package in fresh private output.
Explicit TestPyPI execution uploads admitted wheel/sdist bytes, retrieves the
exact same package/version and artifact hashes, then performs offline installed
functional smoke. A passing transfer receipt establishes only that operation.
Production promotion stays blocked pending its separate reviewed release contract.

```python
from pathlib import Path
from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

adapter = PyPIAdapter(PyPIConfig(test=True))
preview = adapter.publish(Path("."))
# Explicit network operation after sandbox publication authorization:
# transfer = adapter.publish(Path("."), dry_run=False)
```

Prepare uv, hatchling, twine and the source-owned locked runtime dependencies
before execution. Tools are never installed dynamically. Credentials use
`TEST_PYPI_API_TOKEN` (or the existing `TESTPYPI_TOKEN`) through the child
environment; captured diagnostics redact the token.

For an already admitted root wheel, `scripts/publish/verify_install.py` requires
`--wheel <path> --sha256 <original-hash>` and verifies it offline against current
platform metadata. There is no unpinned index fallback.

The obsolete destructive build, unbound upload and unpinned index verification
interfaces are retired. Public adapter/model imports are inert; executable
acceptance is loaded only when the adapter is explicitly invoked.

See [AGENTS.md](AGENTS.md) for boundaries and test commands.
