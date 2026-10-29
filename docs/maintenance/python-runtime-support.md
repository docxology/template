# Python runtime support

Platform 4.3.0 requires Python 3.14 or newer. The repository default and release
interpreter is Python 3.14. Required qualification covers Python 3.14 and 3.15
for infrastructure and every canonical public exemplar. Root acceptance requires
both supported minors on Linux and macOS. Declarations and profiling results do
not establish a successful runtime qualification.

The previous Python 3.10/3.11 support belongs to platform 3.x. Raising the floor
is a breaking platform change and does not relabel prior published releases.
Public exemplar packages retain independent versions. Their `[tool.template]`
metadata binds the current root SDK version through `platform_version` and lists both required Python
minor versions; package and manuscript metadata describe the intended next
release, while published citation/deposit sidecars remain historical evidence.

The Root `active-inference` development group is opt-in with
`uv sync --group active-inference` for its owning feature and native replay.
Ordinary core bootstrap does not activate that ML stack. The Active exemplar
retains its direct project dependency and complete required test selection;
core availability does not establish optional-feature qualification. Each
selected minor still needs compatible locked dependencies and actual execution.

A locked release can carry wheels for one supported minor only. PyYAML 6.0.3
publishes cp314 wheels and no cp315 wheel, so the installed matrix nominates the
locked sdist for that target minor instead of its registry requirement
(`infrastructure.project.locked_dependency_export` with `--minor`), builds the
wheel once into the warm cache, and still installs offline with `--no-build`
and exact hashes. The current 3.15 source builds are PyYAML, wordcloud and
regex; a release with neither a compatible wheel nor a locked sdist is refused
rather than silently built from an unpinned source. Pins that predate the cp315
wheel set (torch, triton, cuda-bindings, hypothesis in four exemplars) are
refreshed rather than bypassed.

Root `pyproject.toml` and `infrastructure._version.__version__` must agree. The
root release contract rejects a mismatched runtime version, a wrong tag, or a
missing release-intent changelog heading. For a coordinated root SDK version
transition, use the checked metadata plan in [release boundary](release-boundary.md);
it preserves third-party lock records. Dependency or Python changes that require
resolution need their own reviewed lock refresh. Verify each resulting independent
lock against its actual package metadata.

`infrastructure.core.runtime.python_compatibility.scan_python_314_compatibility`
parses the public source surface with the Python 3.14 grammar and rejects known
unguarded Python 3.15 APIs. The public `scan_python_312_compatibility` helper
retains its historical grammar and API checks; it does not declare current
Python 3.12 runtime support. The scanner is a bounded static check; interpreter-specific
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
