# Required acceptance profiles

The dashboard reads existing evidence. It does not execute checks, acquire tools,
contact providers, publish artifacts, or authorize promotion. A successful report
render says nothing about acceptance. Execution provenance remains the caller's
responsibility; the validator checks declared scope, measured results, versions,
source custody, and exact artifact bytes.

`candidate` requires the canonical public roster, all supported Python runtimes,
infrastructure coverage, documentation and Methods checks, macOS process/rendering
acceptance, clean installed packages, source/export parity, and actual sandbox
transfer with independent retrieval. Every public project requires its declared
runtimes and coverage, the complete current core execution plan, every enabled
render format, a domain oracle, an isolated installation, and its source export.
Each `[tool.template].required_unpaid_capabilities` declaration adds a required
live gate. An explicit empty list declares a deterministic-only project. Paid
capabilities are outside this profile.

`released` adds root and exemplar publication evidence, including actual tag,
published version, export/retrieval hashes and commit parity. A source-declared
draft without a DOI may instead record that it remains unpublished, together with
its intended version. This does not exempt its candidate checks. Intended versions,
tag hints and verified publication facts remain separate.

States are `pass`, `fail`, `blocked`, and `unknown`. Missing evidence is unknown.
A required tool blocker must have a bound receipt naming the tool and reason.
Malformed, stale, skipped-required, partial or unbound evidence fails. Candidate
acceptance permits preparing a production bundle; production publication still
requires the explicit review and approval policy. Full release readiness cannot
pass before its required publication evidence is supplied.

## Receipt and artifact custody

The receipt schema is `template-release-readiness-receipt-v2`. It contains the
current `platform_version`, `source_fingerprint`, exact canonical `roster`, and
a `gates` mapping. Each gate entry has a state, an executed `command` argv array,
a public repository-relative `artifact` path and its exact `artifact_sha256`.
Place acceptance artifacts under ignored `output/readiness/<run>/`. The old five
structural receipts are insufficient and unsupported.

Each artifact is an object with schema `template-required-acceptance-v1`, its
exact `gate`, `scope` (`root` or a qualified public project), `status`, independent
`version`, `platform_version`, `source_fingerprint`, and `source_identity`.
Project artifacts also bind `deliverables_identity`. Passing artifacts contain
kind-specific `details`; blockers contain nonempty `blockers` with `tool` and
`reason`. See `release_readiness_validators.py` for the executable detail schemas.

One snapshot reader confines all references to public scope, rejects symlinks,
reads each artifact once, and hashes the same bytes used for its facts. File
identities and public source custody are checked after aggregation. Public source
identity excludes only the actual project output roots and runtime caches; source
modules called `output`, `build`, or `dist` remain included. Stable deliverables
use the shared shippable-output inventory, including Git-ignore custody.

Legacy pipeline snapshots, generated counts and structural graphs remain useful
observations. They cannot establish that the expected plans, required live
capabilities or the whole public roster completed.

## Producing complete evidence

Use `required_profile(root, SnapshotReader(root), source_fingerprint(root))` to
derive the current gate IDs and bindings. Runtime details must include the exact
supported Python minor, nonzero passing counts, zero failures/errors/skips or
deselections, and the complete ordered `Requirement.test_files` selection.
Coverage details bind the raw branch-coverage JSON and its exact totals; its
measured file keys must cover all `Requirement.source_files`, with source-owned
coverage omissions already applied. Project-relative `src/` keys are normalized
to the canonical public project path.
Both runtime and coverage details bind an actual selected-interpreter
`runtime_artifact` probe with executable hash, supported minor/full version,
implementation, installed test packages, empty missing list and child exit0.
The details' `interpreter`, `implementation` and `python_full_version` must match
that exact probe. A successful count from a different environment cannot pass.

Source-owned local package dependencies also bind the runtime closure. Both gates
include `dependency_providers`, keyed by canonical non-root public scope, with
the current `package`, `version`, and exact `wheel_artifact` binding. The same
snapshot reader resolves the canonical pyproject declarations and every
transitive version constraint. `run_id`, `collection_artifact`, and the ordered
`case_artifacts` bind the complete actual pytest selection to the selected
runtime. Every collection and case receipt carries `dependency_custody[scope]`
with equal `before` and `after` observations of the installed distribution and
fresh executed bytecode. Its `dependency_artifacts[scope].metadata` and `.record`
bind copied bytes from the actual selected installed distribution. The validator
checks current wheel/source parity, exact consumed member hashes, METADATA, and
the installed RECORD; installers may rewrite RECORD and add their exact metadata
files. A checkout import, stale wheel, missing provider, or changed installed
member cannot grant runtime or coverage acceptance. Root infrastructure remains
the explicitly selected checkout plane in source-test cells; isolated root-wheel
acceptance is a separate required gate.

Pipeline acceptance binds the current compiled complete core plan, its digest,
ordered expected stage keys, and fresh successful outcomes. Cached, skipped,
partial, invented or reordered stage sets cannot establish fresh acceptance.
Native format checks parse the actual bound PDF, DOCX or EPUB bytes. Installation
checks require complete wheel `WHEEL`/`RECORD` metadata and the current Python
implementation bytes; an old wheel with an unchanged version cannot pass.

Source exports must contain the complete current public source and each declared
bundled resource, with exact member-byte parity. Every ZIP member path, including
directories, is validated. Optional project `.template-export.json` metadata must
use the exact public schema from `ExportManifest`, with no extra fields. Its
source project, exported basename, infrastructure version, resource declarations,
file hashes and source commit must agree with the bound outer manifest; that
manifest must include `source_commit` when embedded metadata is present. Root
exports have no embedded project metadata. Sandbox transfer and publication
receipts must reference the export already validated for the same scope, then
bind independently retrieved identical bytes.

Live receipts must explicitly report successful actual execution of the declared
unpaid capability and bind its execution artifact. Positive assertions require
actual true values; named negative controls bind the expected nonzero child exit
to a public artifact containing the same observed exit. A controlled transport
fixture, missing execution kind, or a failed capability receipt cannot grant a
live acceptance gate.

```bash
uv run python -m infrastructure.reporting.release_readiness --profile candidate --strict \
  --readiness-receipt output/readiness/run/receipt.json --format json
uv run python -m infrastructure.reporting.release_readiness --profile released --strict \
  --readiness-receipt output/readiness/run/receipt.json --out output/readiness/report.md
```
