# Python runtime support

Platform 4.0.2 requires Python 3.12 or newer. The repository default and release
interpreter is Python 3.14. CI validates Python 3.12, 3.13, and 3.14 for the
infrastructure and every canonical public exemplar; macOS adds a Python 3.14
smoke lane. All supported Ubuntu lanes run on pull requests as well as main.

The previous Python 3.10/3.11 support belongs to platform 3.x. Raising the floor
is a breaking platform change and does not relabel prior published releases.
Public exemplar packages retain independent versions. Their `[tool.template]`
metadata binds `platform_version = "4.0.2"` and lists the three tested Python
minor versions; package and manuscript metadata describe the intended next
release, while published citation/deposit sidecars remain historical evidence.

Root `pyproject.toml` and `infrastructure._version.__version__` must agree. The
root release contract rejects a mismatched runtime version, a wrong tag, or a
missing released changelog heading. Regenerate the root and project locks with
`uv lock` when changing dependency or Python metadata; use `uv lock --check`
against every independent project to verify freshness.

`infrastructure.core.runtime.python_compatibility` parses the public source
surface with the Python 3.12 grammar and rejects known unguarded APIs introduced
in Python 3.13/3.14. The scanner is a bounded static check; interpreter-specific
execution and dependency resolution still require the supported runtime matrix.

`scripts/gates/public_readiness.py` without `--acceptance-matrix` is a health
diagnostic using the actual controller interpreter and the declared test profile.
Its JSON marks `diagnostic_only: true`; profile exclusions and optional skips do
not grant required release acceptance. `--acceptance-matrix` instead selects
explicit installed interpreters and measures the complete source-owned test
selection and own-source branch coverage for each supported minor.

Advanced's source suites consume the declared canonical Meta engine from its
current admitted installed wheel. Bind that public artifact with
`--provider-wheel templates/template_literature_meta_analysis=/absolute/path/to/output/readiness/provider.whl`.
Install those exact admitted bytes into each selected dedicated environment
before the matrix. Every actual collection/chunk retains its before/after
provider custody and exact consumed METADATA/RECORD; an absent wheel or installed
provider is blocked, and stale or changed bytes fail.

Run focused local contracts with:

```bash
uv run pytest tests/infra_tests/core/runtime/test_python_compatibility.py --no-cov -q
uv run pytest tests/infra_tests/project/test_public_capabilities.py --no-cov -q
uv run pytest tests/infra_tests/publishing/test_root_release_contract.py --no-cov -q
uv lock --check
```

The release-readiness dashboard derives required acceptance from all canonical
public projects and their source-owned unpaid capability declarations. It uses
`pass`, `fail`, `blocked`, and `unknown`: missing execution evidence is unknown;
required tool blockers are blocked; invalid or stale evidence fails.
`--profile candidate --strict` requires all supported runtimes, coverage,
complete core plans, formats, domain controls, installed packages, exports,
unpaid capabilities, sandbox transfer/retrieval, and macOS acceptance.
`--profile released --strict` additionally requires actual version/tag/remote
and retrieved-artifact parity. Source-declared drafts can explicitly remain
unpublished. Strict exits are 0/pass, 1/fail, 75/blocked, and 2/unknown.

The v2 receipt binds current public source, independent project versions,
source-owned scope, and exact public artifact bytes through one observation.
Five structural snapshots or an arbitrary successful stage subset cannot grant
readiness. Candidate acceptance permits preparation; production publication
requires explicit approval. See
[`RELEASE_READINESS.md`](../../infrastructure/reporting/RELEASE_READINESS.md)
for the artifact contract and the producer provenance boundary.
