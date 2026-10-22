# Standalone installation projection

Canonical monorepo exports retain their original `pyproject.toml`, `uv.lock`,
and schema-2 `.template-export.json`. Some exemplars declare the platform through
`../../..`; Advanced also declares its sibling Meta project. Those checkout
paths describe the monorepo and cannot serve as standalone installation sources.

`infrastructure.publishing.standalone_install_projection` provides an explicit
`template-standalone-install-projection/1` transformation. It creates a fresh tree
and changes only admitted provider fields in `pyproject.toml` and `uv.lock` to
canonical public Git URLs with full existing commit pins. Third-party lock
package blocks, scientific source, manuscripts, resources, and executable modes
remain exact. Unsupported local source shapes and provider version disagreements
fail before destination creation.

The projection retains the original schema-2 manifest as immutable source
provenance. Its `.template-install-projection.json` records original and projected
file inventories, changed-file hash pairs, the whole original export digest,
unchanged third-party lock digest, and provider package/version/commit/tree and
metadata identities. The original schema-2 manifest describes the original
export; consumers of transformed trees must explicitly validate the projection.

`validate_standalone_installation` reconstructs the canonical original from the
actual committed platform checkout and recomputes every transformation. It
requires exact projected bytes, names, modes, and provenance. A copied or edited
manifest alone cannot authorize changed scientific bytes or different providers.

The platform provider must be a clean real checkout of `research-project-template`
at the version required by the exported project, with its full admitted HEAD,
canonical origin and committed metadata bytes. Advanced requires a clean `template-literature-meta-analysis` 0.2.0
standalone commit whose managed bytes are the exact Meta installation projection
from that same platform revision. Meta must therefore be prepared and committed
before the Advanced projection is created. Git URL rewriting, hidden changed
metadata, provider root links, and linked destination ancestors are refused.

Meta uses an explicit setuptools package/build contract without backend paths.
Installation inputs must match the reviewed Root projection. Only regular
committed publication evidence and the exact ownership inventory may remain
outside its package/build input trees. Native Git reads ignore replacement refs,
so local object substitution cannot alter the contents or epoch bound to a
published commit identity.

Use `scripts/publish/sync_standalone_mirrors.py --install-projection` to opt into
projected mirror synchronization. Without this flag, ordinary schema-2 source
exports retain their existing byte contract. Advanced additionally requires
`--meta-provider` and `--meta-commit` together; supplying either in source-only
mode is invalid. The script derives the platform provider from the clean source
checkout, reports separate source-export and projection hashes, and remains a
dry run unless `--commit` is supplied.

Mirror synchronization reconstructs the projected export from current admitted
sources before destination updates and again before promotion. Existing
destination guards, exact reviewed source-removal plans, retained quarantine,
immutable publication evidence, committed managed-byte validation, branch
checks, and explicit push-destination admission still apply. See
[publication removals](publication-removals.md).

Local commit, origin, and byte checks establish source custody. They do not prove
public remote retrievability or successful installation. Before a standalone
push is treated as accepted, verify actual provider commits through public
retrieval, run `uv sync --locked` on the resulting isolated project, and execute
its own nonempty tests, coverage, domain producers, installed-package checks,
and declared render formats. Record remote commit and export-content parity
separately. Projection tests use invented committed public fixtures and an owned
local Git installation fixture; these prove the contract and UV encoding, not
the public acceptance of all exemplars.

Focused proving commands after source freeze:

```bash
.venv/bin/python -m pytest tests/infra_tests/publishing/test_standalone_install_lock.py tests/infra_tests/publishing/test_standalone_install_projection.py --no-cov -n 0 --timeout=240
.venv/bin/python -m pytest tests/infra_tests/publishing/test_standalone_mirror.py tests/infra_tests/publishing/test_standalone_export.py --no-cov -n 0 --timeout=240
```
