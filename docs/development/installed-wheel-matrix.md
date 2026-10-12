# Public installed-wheel acceptance matrix

`scripts/gates/installed_public.py` builds and executes genuine wheels for the
root platform and every source-owned public exemplar on Python 3.12, 3.13, and
3.14. The complete product is 78 cells. Set `P4_PYTHON312`, `P4_PYTHON313`, and
`P4_PYTHON314` to absolute already installed interpreter paths; the prepared
environment example in [`public-runtime-matrix.md`](public-runtime-matrix.md)
can supply them. Run the complete selection:

```bash
uv run --no-sync --offline python scripts/gates/installed_public.py \
  --project-workers 1 --timeout 600 \
  --python "3.12=$P4_PYTHON312" \
  --python "3.13=$P4_PYTHON313" \
  --python "3.14=$P4_PYTHON314"
```

Prepare the exact locked nonlocal dependency and build-tool cache explicitly
before execution. The required acceptance workflow's
[`Warm exact locked offline wheel dependencies for every scope and minor`](../../.github/workflows/platform-required-acceptance.yml)
step shows separate metadata exports and dependency environments for each scope
and runtime. An offline local preparation uses already cached packages; prepare
missing packages explicitly before restarting acceptance. It does not justify
resolving or installing dependencies during ordinary execution.

For a locked public PyPI package whose release has no registry wheels, use the
shared `infrastructure.project.locked_dependency_export` CLI after the canonical
export. It names only the same scope lock's exact sdist URL and original SHA256;
versions, extras, markers and unrelated wheel rows retain their bindings. Both
the online warmer and actual cold producer apply this transform before consuming
the export. For example, with the selected scope's frozen metadata directory and
the generated export:

```bash
python -m infrastructure.project.locked_dependency_export \
  --metadata-root "$P4_METADATA" --requirements "$P4_REQUIREMENTS"
```

Follow the workflow's preparation boundary: create a fresh private job-owned
`UV_CACHE_DIR`, seed a fresh builder only from the root's hash-locked
`installed-build` group, and warm dependencies with `--no-build-isolation
--no-deps --require-hashes` into a separate target outside the builder's imports.
Retain the same cache under the owner's custody through cold execution, which
still requires `--offline --no-config --no-build --require-hashes`. Do not restore
derived source-build cache entries into that preparation cache. The archive hash
authenticates source bytes; it does not authenticate mutable derived cached wheel
bytes. This cache ownership boundary is an explicit prerequisite, and a successful
dependency preparation alone establishes no full installed or native acceptance.

The runner creates separate private build and runtime environments for each
cell. Build tools come from the platform's locked `installed-build` group;
runtime dependencies come from a private read-only snapshot of the selected
scope's exact locked metadata. Its root/project layout preserves declared local
resolvers, and tools never reread mutable checkout metadata. Offline
installation uses exact exported hashes. Python and tools are never acquired,
the shared `.venv` stays intact, and concurrency is bounded to three projects.
Runtime waves are sequential. Missing installed tools or cached dependencies
produce typed blockers; execution, parity, dependency, and deadline failures
refuse acceptance.

Each project reuses the canonical exporter. Exact public source and declared
cross-root resource bytes must match before a source archive is admitted. A
fresh build produces one real wheel. Its native WHEEL/RECORD, complete current
Python implementation, packaged data, licences, and declared public resources
must match the source-owned scope. Unbound, private, stale, or omitted wheel
members refuse admission.

Every runtime environment installs wheels rather than editable projects. For a
declared local dependency, only a canonical public scope is admitted. Its
genuine wheel is built and admitted before the consuming cell in topological
waves. Advanced's namespaced Meta engine and the root platform are separate
providers. The dependency-only lock export excludes local source installations;
the actual admitted wheels supply those packages. Diagnostic selections include
their complete prerequisites. Cycles, private paths, package/version mismatch,
overlapping installed members, and missing provider wheels refuse acceptance.

To prepare only the genuine Meta provider used by source-suite runtime
acceptance, add `--project templates/template_literature_meta_analysis` to the
same command. Its root prerequisite is included automatically. Retained successful
cell details name the actual `wheel_artifact` path and SHA256. Select that
observation and install its exact wheel into each dedicated source-test
environment as shown in the runtime guide. The provider-only run records
`matrix_complete: false`; it never closes the complete installed-matrix lane.

The actual probe runs isolated Python outside source directories, with
`PYTHONPATH` and credential-shaped environment variables removed. The launcher
creates an empty private bytecode prefix before imports. Imported modules must
belong to the installed environment, admitted wheel bytes must match the
installed files, and the selected interpreter's exact binary identity is
rechecked. Platform-dependent probes bind actual distribution METADATA/RECORD
and loaded source through installed-distribution custody. They do not invent
checkout files inside site-packages.

The root probe executes its completion policy. The pools probe executes its
integration using package-owned fonds/rules/tools and invokes its bundled code
executor. The Autopoiesis probe executes all selected child tests and analyses
using the exported project as data while importing the genuine installed
generator. It binds the generator and platform distributions, independent
numerical comparisons, nonempty coverage and unchanged exported child sources.
Other package import probes establish the installed import boundary;
pipeline, scientific domain, native-format, model/provider, and publication
acceptance remain independent gates.

Each cell's total finite budget includes supervised child cleanup, source/export
custody, and final success classification. The complete public source and stable
deliverables must still match when the matrix ends. Schedule a stable source
window; concurrent implementation or deliverable edits invalidate the receipt.

Ignored local evidence lives under a fresh `output/readiness` directory. It
contains source archives, manifests, genuine wheels, exact dependency exports,
supervised command/exit receipts, raw installed probes, and source-bound gate
artifacts. The top receipt uses `template-release-readiness-receipt-v2`;
installed/export gates use `template-required-acceptance-v1`; raw installed
probes use `template-installed-probe-v2`. The strict installed reader requires
all supported minor observations and their bound raw probes, specifications and
successful isolated child-process records. Current wheel admission alone cannot
authorize installed acceptance. Exit 75 means
blocked acceptance, exit 1 means failed acceptance, and exit 0 means all selected
cells passed. A diagnostic subset records `matrix_complete: false`.

Installed-wheel acceptance is separate from runtime test/coverage, pipeline,
native-format, live unpaid capability, sandbox transfer, and released publication
evidence. An installed matrix pass alone does not establish complete candidate
readiness or authorize production publication.

## Separate rendering and native-format evidence

The structural `scripts/audit/check_public_template_contract.py --strict` gate
checks authoring completeness. It does not build a wheel, execute an installed
package, regenerate a document, or establish a native-format acceptance receipt.

Prepare current source-bound analysis outputs through the canonical core pipeline
before a targeted render. For each qualified public project, regenerate configured
formats and run output validation using the prepared repository environment:

```bash
: "${P4_PROJECT:?Set to a canonical qualified public project name}"
uv run --no-sync --offline python scripts/pipeline/stage_03_render.py \
  --project "$P4_PROJECT"
uv run --no-sync --offline python scripts/pipeline/stage_04_validate.py \
  --project "$P4_PROJECT"
```

Repeat against the generated public roster, including each project's declared
format/edition/length variants and its canonical domain producers. Keep manuscript
hydration enabled. Then run the current rendered-publication audit:

```bash
uv run --no-sync --offline python -m infrastructure.validation.cli publication-audit \
  --all-public --strict --rendered --require-figure-accessibility --format json
```

This audit and actual rendering are required evidence. Native acceptance uses an
explicitly admitted installed SDK, prepared tools/providers and a fresh supervised
operation. The [required acceptance workflow](../../.github/workflows/platform-required-acceptance.yml)
prepares these inputs, runs `infrastructure.reporting.native_installed_launcher
--mode original`, then supplies a separate installed reader with the original
source, process and artifact context. Follow its `native-original` and `complete`
jobs; a bare `scripts/gates/native_formats.py` invocation does not supply that
admission context.

Advanced callers of the lower-level native producer must supply every required
CLI selection from independently prepared inputs:

| Selection | Required flags |
| --- | --- |
| Actual host | `--expected-platform Linux` or `--expected-platform Darwin` |
| Selected SDK and exact implementation input | `--sdk-package-root`, `--implementation-input`, `--implementation-sha256` |
| Prepared Mermaid runtime | `--mermaid-package-root`, `--mermaid-dependency-root`, `--mermaid-node-executable`, `--mermaid-chrome-executable` |
| Independently selected PDFium | `--pdfium-site`, `--pdfium-wheel` |

Add each declared local provider with repeated `--provider-wheel SCOPE=PATH` and
nominate the consumed Office fonts with repeated `--office-font-file PATH`.
For EPUB, supply both `--epubcheck-jar PATH` and `--java-executable PATH`.
The installed launcher accepts prepared `--office-font-directory` inputs and
constructs its owned SDK/provider selections. Alongside the host and four Mermaid
flags above, its required arguments are:

| Launcher context | Required flags |
| --- | --- |
| Original operation | `--mode original` |
| Exact source | `--source-root`, `--source-commit`, `--source-identity` |
| Prepared runtime/tools | `--python`, `--uv` |
| Fresh owned directories | `--current-root`, `--scratch` |
| Actual hosted origin | `--repository`, `--run-id` |

It does not acquire credentials or publish a release. `--timeout` retains the
finite admission, execution and observer budget. The lower-level producer's
`--project` subset is diagnostic and cannot establish the full native roster.

The supervised producer executes a fresh complete core selection, with cleanup
and shared infrastructure tests explicitly omitted, then binds exact artifact
variants, native parser observations, actual tool versions, fonts and complete
PDF rasters. Its receipt owns only format gates. A format gate can pass only
after the original conformance checks and full independent native acceptance
checks succeed with the held live reader operation. Decoding a receipt cannot
create that operation. Missing inputs or unsupported obligations remain blocked;
actual execution, custody or validation failures remain failed.

Current source declarations still report missing full-oracle obligations for
PDF, browser HTML, native DOCX/EPUB readers, projected slides, pitch pairs,
newspaper editions and storybook pages. Full format acceptance remains blocked
for those applicable declarations until every required oracle is implemented,
its original observations pass and independent readback succeeds. Existing files,
nonblank rasters and a passing structural audit cannot substitute for the required
source-content/layout, semantic, reader and visual negative controls. See
[`native-format-acceptance.md`](../guides/native-format-acceptance.md) for the
supervision and receipt boundaries. Runtime, installed/export, domain, live,
transfer and publication evidence remain independent requirements. Release
readiness must remain unknown, blocked, or failed until every applicable gate
passes the strict candidate profile.
