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
before execution. The release workflow's
[`Prepare locked installed-matrix dependency cache`](../../.github/workflows/release.yml)
step shows separate metadata exports and dependency environments for each scope
and runtime. An offline local preparation uses already cached packages; prepare
missing packages explicitly before restarting acceptance. It does not justify
resolving or installing dependencies during ordinary execution.

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

This audit and actual rendering are required evidence. The supervised native
producer performs a fresh complete core selection, with cleanup and shared
infrastructure tests explicitly omitted, then binds exact artifact variants,
native parser observations, actual tool versions, fonts and complete PDF rasters:

```bash
uv run --no-sync --offline python scripts/gates/native_formats.py
```

The producer emits a fresh partial formats receipt and independently validates
narrower conformance. Full format acceptance remains blocked with exit 75 until
independent source-content/layout and visual negative controls exist for PDF,
browser HTML, native DOCX/EPUB readers, projected slides, pitch pairs, newspaper
editions and storybook pages (`P4-NATIVE-FORMAT-RECEIPTS`). Existing files,
nonblank rasters and a passing structural audit cannot grant those missing
controls. See [`native-format-acceptance.md`](../guides/native-format-acceptance.md)
for the exact supervision and receipt boundaries. Until full native acceptance
and the other required lanes pass the strict candidate profile, release
readiness must remain unknown, blocked, or failed.
