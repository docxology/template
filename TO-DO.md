# Repo TO-DO — future cross-cutting work

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests, source-bound evidence, and accurate documentation.

This file is the root repository backlog. It contains **future work only**:
cross-cutting infrastructure, CI, documentation, release, security, and
reproducibility improvements. Completed work belongs in
[`CHANGELOG.md`](CHANGELOG.md) or the dated review record; generated facts
belong to their generators; project-specific work belongs in each public
exemplar's local `TODO.md`.

IDs are stable. A row may be closed only after the implementation diff, the
relevant generated artifacts, the named acceptance commands, and the negative
controls all exist in the same verification pass. Do not turn this file into a
second changelog.

## Live baseline and constraints

Re-derive all counts before planning or closing work. The authoritative public
roster is [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md);
measured coverage and discovery facts are in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

- The public release matrix, root health gates, generated-document checks, and
  per-exemplar coverage gates were last verified on 2026-08-09. Reproduce the
  matrix with:

  ```bash
  uv run python scripts/pipeline/stage_01_test.py \
    --project-only --all-projects --public-projects \
    --profile release --receipt /tmp/public-matrix-receipt.json
  uv run python -m infrastructure.core.health --json --quiet
  ```

- The root package boundary is `3.6.0`/`v3.6.0`; the checkout remains under
  `[Unreleased]`. Release work must preserve the distinction between root
  package releases and separately published exemplar repositories.
- `tests/regression/` contains a real source-derived claim-binding lane. Every
  canonical public exemplar now has an explicit `bound`, `not_applicable`, or
  `external_data` state; the remaining work is to deepen source-derived pins
  and mutation controls rather than to expand a missing roster entry. This is
  an open reproducibility gap, not a reason to lower coverage or accept
  shape-only tests.
- Executable Bundle and Archival Publication are opt-in stages. Their current
  direct scripts and dry-run paths are useful foundations, but container
  cross-testing, data/licence policy, and a stable CI decision have not yet been
  closed.
- `STATUS.md` has a freshness gate, but a dated row is not the same thing as a
  reproducible verification receipt. Rows that claim a subsystem is healthy
  still need command, scope, owner, and artifact evidence.
- The documentation RedTeam audit currently reports advisory
  `gate-negative-control` findings. Treat the finding count as a re-derived
  audit input, not a hard-coded backlog fact; distinguish normative gate claims
  from historical, generated, and inventory prose before editing.
- Branch protection, sensitive-area review, and private-sidecar promotion are
  external authority boundaries. Repository code can validate their receipts
  and fail closed, but it cannot pretend that GitHub settings or an owner
  attestation exist.

## Priority and sizing rules

- **Minor:** one bounded surface; no new persistent schema or release gate;
  acceptance is normally a focused test, generator check, or documentation
  contract.
- **Medium:** multiple modules or one new machine-checkable contract;
  acceptance needs offline negative controls, generated-artifact review, and a
  focused CI/local reproduction.
- **Major:** a repository-wide claim, release boundary, public matrix, or
  long-horizon artifact contract; requires a design note, staged rollout,
  migration/rollback plan, and clean-checkout or hosted evidence.

## Active root backlog

The table below is the machine-readable index for the stable headings in this
file. A row remains active until its acceptance command and negative control
pass against the same source revision; external authority and unavailable-tool
states are explicit blockers.

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CLAIM-BINDING-MAJ-1` | partial | Major | Public roster and source-owned claim inventory | Finish the full-roster pins and mutation controls, then attach the release receipt | claim-binding receipt | `uv run pytest tests/regression/ -q --no-cov --timeout=120` | missing pin or changed producer must fail |
| `EXECUTABLE-BUNDLE-MAJ-1` | partial | Major | Claim receipt, lockfiles, container policy | Complete immutable bundle and offline-container verification; attach owner/tool receipts where unavailable | executable-bundle receipt | `uv run python scripts/runner/bundle_executable.py --help` | path escape, stale payload, or missing lock must fail preflight |
| `CLEAN-CHECKOUT-MAJ-1` | partial | Major | Release commands and generated receipts | Expand the two-run rehearsal to health, matrix, render, cleanliness, and optional bundle lanes | clean-checkout receipt | `uv run python scripts/maintenance/release_rehearsal.py --help` | dirty output or changed revision must fail the rehearsal |
| `RELEASE-METADATA-1` | partial | Medium | Typed release receipt schema | Bind command, scope, owner, date, health, and verification mode to generated evidence | release metadata receipt | `uv run python scripts/docgen/publication_records.py --check` | receipt without revision or owner status must fail |
| `STATUS-REFRESH-MED-1` | partial | Medium | Status ledger and release receipt | Add stable IDs and receipt links to every active status row, then run freshness and receipt checks | status evidence receipt | `uv run python scripts/gates/status_freshness.py --as-of 2026-08-09` | future, stale, or receipt-less status must fail |
| `PUBLIC-PUBLISH-MANIFEST-MED-1` | partial | Medium | Immutable payload manifest and provider API | Pass one preflight manifest through every provider and reject changed payloads | publication payload manifest | `uv run python scripts/audit/check_public_template_contract.py --strict` | symlink escape, duplicate path, credential, or changed content must fail |
| `TEST-DISCOVERY-PERF-MED-1` | partial | Medium | Isolated project matrix and impact planner | Measure quick feedback, add cache/resource/phase receipts, and prove the speed target without reducing release scope | test-impact and benchmark receipt | `uv run python scripts/audit/test_impact.py` | untracked or staged source changes must not be omitted |
| `MODULARITY-MED-1` | open | Medium | Module-line-count findings and import contracts | Split the three warning hubs, preserve re-exports, and attach size/import/no-mocks receipts | modularity receipt | `uv run python scripts/gates/module_line_count_check.py` | removed re-export or new oversized hub must fail |
| `COVERAGE-SNAPSHOT-MED-1` | partial | Medium | Per-project gates and source inventory | Re-run all public lanes and regenerate versioned coverage provenance from the final source tree | coverage provenance receipt | `uv run python scripts/docgen/counts.py --check` | new source/test file or changed tree identity must fail |
| `DOC-NEG-CONTROL-MIN-1` | partial | Minor | Documentation audit classification | Classify active, generated, inventory, normative, and historical advisories; gate only active normative claims | documentation audit receipt | `uv run python scripts/audit/audit_documentation.py --format json` | a normative gate claim without a real negative control must fail |
| `REGRESSION-SIGNPOST-MIN-1` | partial | Minor | Claim-binding manifest and live counts | Reconcile regression guidance with the current roster and generated receipt | regression contract receipt | `uv run pytest tests/regression/ -q --no-cov --timeout=120` | empty collection or stale roster must fail |
| `BUNDLE-ENTRYPOINT-MIN-1` | partial | Minor | Opt-in runner scripts | Document discoverable dry-run bundle and rehearsal commands without changing defaults | command discoverability check | `uv run python scripts/runner/bundle_executable.py --help` | default pipeline must not build or publish a bundle |
| `COVERAGE-GAPS-MIN-1` | partial | Minor | Generated coverage snapshot | Replace copied coverage-gap counts with links and source-derived status | coverage-gap receipt | `uv run python scripts/docgen/counts.py --check` | copied stale measurement must fail drift |
| `ARCHIVAL-TRACKER-MIN-1` | partial | Minor | Publication records and provider receipts | Reconcile archival tracking from live receipts and record unavailable providers distinctly | archival tracking receipt | `uv run python scripts/runner/archive_publication.py --help` | missing credential or provider must not report success |
| `SECURITY-OWNERSHIP-1` | blocked-external | Medium | Administrator branch-protection and CODEOWNERS receipt | Obtain administrator evidence for branch protection and required review; until then remain blocked | administrator authority receipt | `uv run python scripts/gates/security_scan.py --help` | local files must not imply remote protection exists |
| `SECURITY-PRIVATE-PROMOTION-1` | blocked-external | Major | Owner private-sidecar promotion receipt | Obtain owner authorization, redaction, and export evidence before any private promotion | owner promotion receipt | `uv run python scripts/audit/check_tracked_all.py` | private path or sidecar content must fail public guards |

## Major improvements

### `CLAIM-BINDING-MAJ-1` — complete quantitative claim binding

**Problem and impact.** The template claims reproducible research, but the
claim-binding lane is still a partial inventory. A figure/table can remain
shape-valid while a numeric manuscript statement drifts from the function and
inputs that produced it. The current sources of truth are split across
`tests/regression/manifest.json`, `tests/regression/pinned_values/`, project
manuscripts, figure registries, and evidence registries.

**Scope.**

1. Build a source-owned inventory of quantitative claims from the manuscript,
   figure/table registries, and evidence registries. Classify counts,
   proportions, coefficients, rates, p-values, effect sizes, and ratios
   separately from qualitative or interpretive prose.
2. Extend the regression manifest with an explicit state for every public
   exemplar: `bound`, `not_applicable` with a reviewer reason, or
   `external_data` with a source/license/hash boundary. Missing entries must be
   visible rather than silently omitted.
3. Add source-derived pins and verifiers in waves: finish the guaranteed
   `template_code_project` figure/table surface first, then add deterministic
   public exemplars without inventing values from rendered output.
4. Require every pin to carry manuscript location, producing function or
   command, input/config identity, tolerance rationale, pin date, and source
   revision. Add mutation controls that alter the producing calculation and
   prove the test fails.
5. Update the regression README, maintenance guide, generated manifest, and CI
   collection contract together. Keep interpretive/causal claims explicitly
   outside the numeric pinning contract.

**Out of scope.** Live literature retrieval, proving that an interpretation is
scientifically true, widening tolerances to suppress failures, and updating a
pin without a documented investigation of the changed result.

**Dependencies.** Current public-scope discovery, stable figure/evidence
registries, and the clean-checkout rehearsal below.

**Acceptance evidence.**

- A generator/check reports every current public project and every classified
  quantitative claim as bound or explicitly reviewed as not applicable/external.
- A deliberately mutated producer, missing pin, mismatched manuscript location,
  and stale source revision each fail with actionable diagnostics.
- `uv run pytest tests/regression/ -q --no-cov --timeout=120` passes with a
  non-empty collection, and the release receipt records the exact roster and
  revision.
- No project output tree is modified by the regression lane; no unit-level mock
  framework or semantic stand-in is introduced.

### `EXECUTABLE-BUNDLE-MAJ-1` — make the executable artifact a verifiable release lane

**Problem and impact.** `scripts/runner/bundle_executable.py` and
`archive_publication.py` provide opt-in foundations, but the bundle is not yet a
portable, container-verified reproduction contract. Without a tested manifest,
data policy, and stable runtime decision, the long-horizon artifact remains a
documentation promise.

**Scope.**

1. Freeze the bundle schema and decide which fields are byte-deterministic
   versus content-equivalent (timestamps, compiler metadata, font subsets, and
   provider receipts must be classified rather than silently normalized).
2. Make the bundle manifest enumerate source/config/data/lockfile hashes,
   licence or external-data obligations, claim verifiers, entry points, and
   the exact producing revision. Refuse path traversal, symlink escape,
   local-only project roots, missing required locks, and unreviewed external
   data.
3. Add a small convenience entry point (`--bundle-only` or an equivalent
   documented command) without changing the default core pipeline.
4. Build and run a representative public bundle in an isolated container with
   network disabled: execute tests, re-derive claim pins, render the primary
   artifact, and validate the manifest. Run a second build to check the chosen
   determinism contract.
5. Add a scheduled/manual CI lane with an explicit tool-unavailable result;
   never convert a missing container runtime into a silent green release gate.
   Keep live deposits credential-gated and dry-run by default.

**Out of scope.** GPU support, cross-project bundles, re-execution of optional
LLM stages, and real provider deposits in default CI.

**Dependencies.** `CLAIM-BINDING-MAJ-1`, the existing reproducible-PDF
contract, pinned project lockfiles, and an agreed external-data/licence policy.

**Acceptance evidence.**

- A clean temporary checkout builds the bundle without private symlinks or
  network access; the container runs the declared tests and claim verifiers.
- Missing locks, changed source, unsafe paths, stale data, and an invalid claim
  pin each fail before a provider or container command is launched.
- Two runs satisfy the documented byte/content-equivalence rule, and the
  manifest validator reports the same source revision, inputs, outputs, and
  claim outcomes.
- `archive_publication.py` produces a complete dry-run receipt from the bundle;
  non-dry-run paths still require an explicit owner and credentials.

### `CLEAN-CHECKOUT-MAJ-1` — add a release rehearsal from zero local state

**Problem and impact.** Final-tree tests and hosted CI can pass while a local
private symlink, warm cache, installed optional tool, generated output, or
untracked file supplies hidden state. The repository still needs a repeatable
proof that a fresh clone can reproduce its own release evidence.

**Scope.** Add a read-only or disposable-worktree rehearsal that records the
exact commit, interpreter/tool versions, environment profile, public roster,
and generated-artifact diff. The rehearsal must:

- clone or materialize the exact target revision into a fresh directory with no
  private lifecycle links;
- run locked dependency setup, root health, generated-doc checks, the public
  release-profile matrix, and a representative core render;
- run the claim-binding lane and, when enabled, the executable-bundle smoke;
- verify the worktree and public output roots are clean after each lane;
- emit a bounded JSON receipt with command, exit status, duration, skip reason,
  and artifact hashes; distinguish unavailable optional tools from failures.

Run the rehearsal on the primary local platform and the hosted Linux platform,
then repeat the deterministic portions twice to expose cache/time dependence.
Do not include credentials, real publication, or private project paths.

**Acceptance evidence.** A fresh-clone receipt is complete for the generated
public roster, both platform lanes agree on required outcomes, repeated runs
agree on deterministic fields, and a deliberate missing-project/private-symlink
fixture fails closed. The receipt is linked from release validation without
hard-coding its counts into prose.

## Medium improvements

### `RELEASE-METADATA-1` — close the metadata and release-boundary receipt

**Current state.** Repository-side metadata and installer checks are present,
but live DOI/GitHub metadata freshness and branch-protection confirmation remain
external. Keep this ID because release/security documentation already references
it.

**Scope.**

- Define one credential-free metadata receipt containing repository identity,
  root package version/tag, DOI/repository links, release commit, installer pin,
  check date, and source URLs; redact tokens and credentialed URLs.
- Make the offline release contract validate receipt schema, version/tag
  consistency, and expiry without requiring network access. Its named
  negative-control fixtures are a malformed receipt, a tag/version mismatch,
  an expired receipt, and a credential-bearing URL. A live refresh may update a
  receipt only through an explicit maintainer command.
- Record the administrator-owned branch-protection result separately rather than
  marking it green from repository files. Keep the required-check list sourced
  from `.github/workflows/ci.yml` and the branch-protection checklist.

**Acceptance evidence.** A stale, mismatched, malformed, or credential-bearing
receipt fails offline; a network outage produces an explicit external-check
blocker; a refreshed receipt names the exact release commit and check date; no
mutable installer command remains in maintained setup guidance.

### `STATUS-REFRESH-MED-1` — turn subsystem freshness into evidence receipts

**Current state.** `scripts/gates/status_freshness.py` checks dates and future
values, but it cannot tell whether a green row's command actually ran or whether
its artifact is the one being described.

**Scope.** Extend the status contract, keeping `STATUS.md` human-readable, with
stable row IDs and machine-readable fields for verification command, working
scope, owner, as-of date, receipt/artifact path, and health decision. Add a
validator/generator that resolves commands and paths, rejects future or stale
dates, rejects a healthy row without evidence, and distinguishes `manual`,
`external`, `optional-tool`, and `automated` verification. Preserve historical
dates; do not rewrite them to make the ledger green.

**Acceptance evidence.** A fixture with a missing command, missing receipt,
future date, stale date, wrong project path, or mismatched health decision fails
with a stable diagnostic. A valid current ledger passes the health gate and
renders a compact evidence index. The publishing row remains explicitly
credential-blocked until a real deposit is authorized and performed.

### `PUBLIC-PUBLISH-MANIFEST-MED-1` — make non-dry-run payloads explicit

**Problem and impact.** The publication threat model still calls for a stronger
path manifest at the boundary where local artifacts and credentials become
external deposits. A dry-run receipt must describe the exact payload that a
future `--commit` invocation would send.

**Scope.** Centralize publication payload enumeration for
`scripts/publish/`, `scripts/runner/archive_publication.py`, and the provider
adapters. The manifest must enforce an allowed output root, symlink confinement,
public-project identity, duplicate/path collision checks, source/config/output
hashes, metadata redaction, provider target, and dry-run/commit mode. Pass an
immutable manifest object into providers rather than re-walking the checkout.

**Acceptance evidence.** Offline tests prove that a local-only project,
symlinked private file, stale generated artifact, duplicate path, token-shaped
metadata, changed payload after preflight, and unexpected provider target all
fail before network I/O. A valid dry-run receipt's path/hash set is identical to
the set handed to a provider in an instrumented local adapter. Existing
credential and publication tests remain green without live secrets.

### `TEST-DISCOVERY-PERF-MED-1` — shorten repository-wide feedback safely

**Problem and impact.** The repository now has explicit test profiles and
isolated project processes, but the pre-push documentation contract still
re-collects every canonical exemplar serially and is a large fraction of local
feedback time.

**Scope.** Instrument the docs-contract phases
(`check_template_drift`, API/reference generation checks, roster/counts/
publication checks, and the one project-surface test) and record phase timing.
Parallelize only independent read-only phases or isolated project collection;
reuse the central worker policy and unique temporary roots. Any cache must be
keyed by commit/tree hash, interpreter, lockfile, profile, and tool version and
must be invalidated for a dirty staged tree. Preserve one deterministic serial
diagnostic mode and the current fail-closed semantics.

**Acceptance evidence.** A same-machine baseline and post-change benchmark are
checked into a machine-readable report, with no correctness gate removed. A
deliberately changed exemplar, generated doc, or project marker invalidates the
fast path and is detected by the serial oracle. Project `conftest.py` package
collisions remain impossible, and failure output identifies the phase/project
that failed.

### `MODULARITY-MED-1` — split warning hubs without changing import surfaces

**Problem and impact.** Three infrastructure modules remain warning-sized
coordination hubs. Their public imports are stable, but their mixed discovery,
receipt, and validation responsibilities make focused testing and review slower
than necessary.

**Scope.** Split the three measured warning hubs at responsibility boundaries,
preserve re-export/import compatibility, keep scripts thin, and add module-size
and import-surface regression receipts. Rename environment-isolation test
helpers that are called `Fake` when they are real probes or injected hosts so
the no-mocks inventory describes intent accurately.

**Acceptance evidence.** The module-line-count gate reports no new warning hub,
public imports and behavior are unchanged, and the focused infrastructure and
no-mocks suites pass. A temporary oversized module and a removed re-export must
fail their respective controls.

### `COVERAGE-SNAPSHOT-MED-1` — make coverage-gap guidance source-bound

**Problem and impact.** `docs/development/coverage-gaps.md` is a useful manual
classification of shims, optional-tool paths, and first-party logic, but its
verification date and module rows can lag behind the current root and exemplar
gates. Stale gap prose encourages line chasing or hides a real branch gap.

**Scope.** Generate or validate the coverage-gap inventory from the documented
coverage oracle and current source tree. Classify entry-point shims separately
from first-party logic, record the command/profile/interpreter/date, link each
target row to a test or an explicit rationale, and retain a term-missing excerpt
for actionable branches. Add a freshness check without turning every low
coverage CLI shim into a false defect.

**Acceptance evidence.** The gap document passes from a clean checkout, stale
dates or nonexistent modules fail, every below-floor first-party row has a
named next test or an explicit external-tool reason, and the generated counts
remain owned by `docs/_generated/COUNTS.md`.

## Minor improvements

### `DOC-NEG-CONTROL-MIN-1` — triage documentation gate advisories

**Current state.** The advisory audit finds `gate-negative-control` prose that
claims a verifier, schema, or rule enforces behavior without naming a known-wrong
fixture. Some findings are genuine weak certification claims; others are
historical, generated, inventory, or normative prose that should be classified
instead of rewritten mechanically.

**Scope.** Process findings in bounded batches. For normative live guidance,
name the exact negative-control fixture, diagnostic, or command. For historical
or generated prose, add a role/allowlist classification or change the audit
scope. Do not suppress a finding merely to reach zero, and do not add fake tests
whose only purpose is to satisfy wording.

**Acceptance evidence.** Each changed finding has a file/line rationale; the
remaining advisory set is categorized and reproducible; active gate claims name
real negative controls; `uv run python scripts/audit/audit_documentation.py
--format json` reports zero volatile-fact and undocumented-symbol findings.

### `REGRESSION-SIGNPOST-MIN-1` — reconcile the regression documentation surface

**Problem and impact.** `tests/regression/manifest.json`,
`tests/regression/README.md`, and `docs/maintenance/regression-testing.md`
describe different maturity levels and historical example rosters. That makes
it easy for a contributor to add a pin in the wrong location or mistake
collection coverage for complete claim coverage.

**Scope.** Update the two guides from the live manifest and public roster,
document the explicit `bound`/`not_applicable`/`external_data` states from
`CLAIM-BINDING-MAJ-1`, and add a consistency check for required paths, schema
version, and “next step” language. Keep historical rationale in the maintenance
record, not the active backlog.

**Acceptance evidence.** A generated/check mode fails on a missing test file,
stale project roster, undocumented manifest state, or claim path that does not
exist. The guides contain no obsolete “first slice only” claim after the check
passes.

### `BUNDLE-ENTRYPOINT-MIN-1` — make the opt-in bundle discoverable

**Scope.** Add the smallest safe convenience surface for the existing bundle
runner: help text, menu/command documentation, explicit output path, and a
negative control for a missing or local-only project. Keep it opt-in and do not
silently add container builds or archival publication to the default pipeline.

**Acceptance evidence.** `--help`, the documented dry-run command, and the
missing-bundle/missing-project failures agree across `run.sh`,
`infrastructure.orchestration`, `docs/RUN_GUIDE.md`, and the runner scripts;
the default `--core-only` plan is unchanged.

### `COVERAGE-GAPS-MIN-1` — remove stale manual snapshots

**Scope.** As an interim measure before `COVERAGE-SNAPSHOT-MED-1`, refresh the
coverage-gap document's verification date and rows from one recorded oracle,
remove claims about tests or modules that no longer exist, and link low rows to
the current test or explicit rationale. Do not copy generated percentages into
the root backlog.

**Acceptance evidence.** The documented oracle runs successfully, the source
and test paths named by the document exist, the root counts check passes, and a
second reviewer can reproduce the row classification from the recorded command.

### `ARCHIVAL-TRACKER-MIN-1` — keep external archival state honest

**Scope.** Refresh `docs/maintenance/software-heritage-archival.md` only from
credential-free queue/browse evidence. Separate accepted, pending, verified,
not-submitted, rate-limited, and intentionally excluded repositories; never
claim that automatic harvesting is the same as a verified receipt. Keep private
repositories and forks out of the public tracker.

**Acceptance evidence.** Every listed repository has an as-of date and one
allowed status, submitted/verified rows have a receipt or source evidence, and
the tracker contains no secrets, private paths, or unsupported “complete” claim.

## External release prerequisites

These are intentionally tracked separately from code-completable improvements.
The repository can validate a supplied receipt, but only an authorized owner or
GitHub administrator can complete them.

### `SECURITY-OWNERSHIP-1` — administrator-owned branch protection

- **Action:** Configure `main` to require the documented lint, health,
  no-mocks, infrastructure/project, regression, manuscript, security,
  documentation, and performance checks; require one approving review and
  sensitive-path CODEOWNER review; disallow force-push and branch deletion.
  The known-wrong control is a test PR with a failing required check or a
  sensitive-file change without the required review, which must be blocked.
- **Evidence:** Administrator records the settings and a test PR demonstrates
  that required checks block merge and CODEOWNERS are requested. Conditional
  jobs remain non-required.
- **Boundary:** Repository files and a green local run do not prove GitHub
  settings. Use [`docs/security/branch-protection-checklist.md`](docs/security/branch-protection-checklist.md).

### `SECURITY-PRIVATE-PROMOTION-1` — owner-authorized private promotion

- **Action:** For any private sidecar promotion, record the exact source commit,
  identity/authorization, redaction, secrets, routes, protocol boundaries,
  export tests, reviewer, and risk acceptance in the private change record.
- **Evidence:** Run the offline attestation and candidate checks from
  [`docs/security/promotion-runbook.md`](docs/security/promotion-runbook.md);
  require a clean candidate tree, matching `HEAD`, confidentiality,
  generated-artifact, publication-preflight, and export evidence.
- **Boundary:** This public repository must not implement private authentication
  or copy private project paths into its docs, manifests, or tracked trees.

## Sequencing and dependency graph

1. `COVERAGE-GAPS-MIN-1`, `REGRESSION-SIGNPOST-MIN-1`, and
   `DOC-NEG-CONTROL-MIN-1` establish accurate inputs and contributor guidance.
2. `STATUS-REFRESH-MED-1`, `RELEASE-METADATA-1`,
   `PUBLIC-PUBLISH-MANIFEST-MED-1`, and `TEST-DISCOVERY-PERF-MED-1` can proceed
   in parallel once their current baselines are recorded.
3. `CLAIM-BINDING-MAJ-1` consumes the corrected regression and generated-doc
   contracts; it is the evidence dependency for `EXECUTABLE-BUNDLE-MAJ-1`.
4. `CLEAN-CHECKOUT-MAJ-1` is the final integration rehearsal for any new
   release gate. `SECURITY-OWNERSHIP-1` and
   `SECURITY-PRIVATE-PROMOTION-1` remain external acceptance prerequisites.

## Backlog operating rules

- Re-derive measured facts instead of copying old counts into prose.
- Keep private or rotating project names out of public docs; use the generated
  active-project roster.
- Prefer real files, subprocesses, deterministic fixtures, and negative
  controls over mocks, fakes, or existence-only assertions.
- Keep business logic in `infrastructure/` or project `src/`; scripts remain
  thin orchestrators.
- Preserve project coverage floors, the confidentiality invariant,
  generated-artifact guard, provenance boundaries, and explicit optional-tool
  skips.
- When an item is complete, move its historical evidence to `CHANGELOG.md` or
  the dated review record and remove the row from this file in the same cleanup
  pass.
