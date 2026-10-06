# `infrastructure/publishing/pypi/`

The public operating adapter uses `pypi_release.py` for canonical root package
admission and exact sandbox transfer. `publish(project_root, dry_run=True)`
performs a fresh prepared build and source-byte admission without transfer.
`dry_run=False, test=True` additionally retrieves original hashes and executes
an isolated installed functional probe. Failed verification cannot return an
upload-success result. Production promotion is blocked pending its separately
reviewed exact-source contract.

| File | Purpose |
| --- | --- |
| `adapter.py` | Canonical local preview and fixed TestPyPI transfer |
| `models.py` | `PyPIConfig`, `PyPIResult`; optional limited receipt |
| `../pypi_release.py` | Original-byte source/artifact custody, deadlines, exact remote retrieval and offline installed smoke |

`PyPIConfig` has `token`, `repository_url`, `test` and finite `timeout` fields.
`PyPIResult` exposes `status`, `package_name`, `version`, artifact names, `url`,
`error`, and an optional receipt. `ok` describes a successful operation or local
preview; it does not authorize a release. `blocked`, `timed_out` and failure
states are unsuccessful.

The destructive build, unbound upload, filename-inference, unpinned index
verifier and ineffective verification flags are retired. Public adapter/model
imports defer executable acceptance to explicit invocation, preventing cycles
with installed artifact, rendering and publication contracts.
The explicit wheel verifier takes original SHA-256 custody and canonical root
metadata, uses offline hash-enforced locked dependencies, and never installs
tooling dynamically. The thin CLI lives at `scripts/publish/verify_install.py`.

No mocks: use actual children and owned fixtures. Offline source controls:

```bash
uv run pytest tests/infra_tests/publishing/test_testpypi_custody.py
uv run pytest tests/infra_tests/publishing/test_pypi.py
```

No live registry operation belongs in those default modules. Hosted, live and
production program acceptance remain separate from local tests.
