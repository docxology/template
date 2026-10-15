# Platform 4.0 implementation program

This is the implementation and verification record for the authorized platform
upgrade. The starting source revision is
`f1914383a08f0f4195134ed33a359b7aacc4f978`. Intended release versions are not
published versions. A work package is complete only after its behavioral
acceptance and independent review, where required, have passed.

## Operating contract

- Python >=3.12; repository default 3.14; compatibility lanes 3.12–3.14.
- Deterministic offline core execution by default; explicitly selected live
  capabilities; no paid API execution.
- Existing process supervision, renderers, validators, scientific oracles, and
  private/public boundaries remain authoritative.
- Retire obsolete execution interfaces and migrate current callers. Preserve
  immutable historical registrations, deposits, and release evidence.
- One resolved execution plan; stable stage keys; truthful typed outcomes;
  source-bound reuse; no success for incomplete or missing required evidence.
- Each public exemplar has an independent intended version and acceptance
  binding to platform 4.0.2 and actual source content.
- Real sandbox transfer and retrieval precede reviewed production promotion.
  Missing providers, credentials, tools, or hardware are blockers.

## Hypotheses and falsification

| ID | Hypothesis | Negative control |
| --- | --- | --- |
| H1 | Canonical interface migration preserves behavior | Changed scientific result or artifact after caller migration |
| H2 | Shared plans eliminate selection drift | Full/single/matrix/Methods/menu disagree on effective source, selection, or order |
| H3 | Typed outcomes eliminate false completion | Paused, failed, timed-out, or incomplete run exits zero |
| H4 | Content-bound state prevents stale reuse | Source/config/plugin/lock/tool/input/output change still permits reuse |
| H5 | Domain/live acceptance detects structural false positives | Invalid producer, forged transcript, failed kernel/tool/provider gets a passing receipt |

## Work packages

| ID | Size | Dependency | Status | Acceptance |
| --- | --- | --- | --- | --- |
| P4-HYGIENE | Medium | baseline | in-progress | migrated callers, future-only backlog, live documentation, focused behavior checks |
| P4-C1 | Medium | baseline | in-progress | correct Methods paths, strict declarations, plugin keys/contracts, source/evidence validation |
| P4-C2 | Medium | C1 | in-progress | original child outcomes and complete expected-stage set; real process failure matrix |
| P4-C3 | Medium | C2 | in-progress | recursive fingerprints, implementation identity, fail-closed checkpoint/cache versions |
| P4-C4 | Major initiative | C1–C3 | in-progress | shared execution plan, entrypoint parity, once-only shared tests, approval/deadline contracts |
| P4-C5 | Medium | C2/C4 | in-progress | core/live mode, offline default, required-evidence readiness |
| P4-VERSION | Medium | C1–C3 | in-progress | root/runtime/wheel/sdist parity, intended exemplar versions, runtime/lock/CI migration |
| P4-EXEMPLARS | Major initiative | C1–C5/version | in-progress | all declared domain/capability cases, isolated nonempty tests and >=90% coverage |
| P4-REHEARSAL | Medium | exemplar acceptance | pending | fresh clone, installed wheels outside sources, all required formats and live cases |
| P4-PUBLISH | Medium | rehearsal | pending | actual sandbox transfers/retrieval; reviewed production artifacts and destinations |
| P4-RELEASE | Medium | all required cases | pending | exact revision evidence, hosted checks, remote/export parity, immutable new versions |

Major initiatives are decomposed into bounded Minor/Medium active backlog
rows. This table is a program roadmap, not a replacement backlog format.

## Execution and state interfaces

`ExecutionPlan` is immutable serializable data, not executable closures. It
binds stage keys, dependencies, argv, artifact contracts, capabilities, policy,
selection, effective definition, and implementation fingerprints. Execution
binds runners after compilation. A targeted single-stage run validates its
prerequisite artifacts without implicitly running the full dependency closure.

Stage/run states distinguish succeeded, cached, skipped, failed, timed-out,
paused, blocked, rejected, aborted, and interrupted. Cache reuse requires
current inputs/implementation and validated outputs. Skip acceptance requires a
fresh confined receipt bound to the run, stage, command, and permitted reason.
Required live capabilities cannot be waived by optional-stage skip policy.

Invocation errors exit 2 before execution. Executed aggregate exit precedence
is interruption 130, timeout 124, failure/rejection/abort 1, pause/block 75,
complete 0. Diagnostics and original child exit codes remain available.

Fingerprint sorted declared trees and conservative infrastructure/project
source plus configurations, effective definitions/plugins, locks, and tool
identities. Exclude runtime/control/log/report residue from artifact identity.
Recheck source before execution and success evidence. Never cache cleanup,
publication, or live side effects. Unknown cache schemas are misses; unknown
checkpoint schemas refuse resume without deleting valuable output.

Approval/rejection binds to the exact run, stable stage, plan, and reviewed
artifact/diff. Approval advances once; rejection prevents execution. Shared
infrastructure verification runs once before project workers. Preserve output
locks and descendant cleanup; compose finite supervision budgets.

## Exemplar intended release targets

The roster remains owned by `infrastructure.project.public_scope`; this table
records the authorized migration targets at the starting revision.

| Exemplar | Intended version | Required specialized evidence |
| --- | --- | --- |
| template_active_inference | 0.4.0 | analytical oracle, pymdp, Lean, invariants, notation and manuscript bindings |
| template_advanced_literature_review | 0.2.0 | unpaid phases, screening/calibration, provenance, local model, licensed fulltext |
| template_autoresearch_project | 0.4.0 | independent scores/noise and keep/reject/defer on fixed offline data |
| template_autopoiesis | 2.0.0 | real child archetypes, honesty recomputation and child failure controls |
| template_code_project | 3.0.0 | optimization oracles, variables, declared formats, local reviews/translation |
| template_data_descriptor | 0.2.0 | invalidity exits, checksum/schema/license and non-CSV sandbox replay |
| template_eda_notebook | 2.0.0 | fresh selected-interpreter kernel and independent output equality |
| template_experiment_tree | 0.2.0 | frozen transitions, retained negatives, coherent unpublished metadata |
| template_formal | 0.2.0 | strict typing, network faults, Lean/TLC including expected violations |
| template_literature_meta_analysis | 0.2.0 | unpaid enabled retrieval/fulltext/local model and recomputed analyses |
| template_madlib | 0.2.0 | current schema, deterministic branch/injection/authoring parity |
| template_newspaper | 2.0.0 | editions, print geometry/fonts/overflow and real raster evidence |
| template_pools_rules_tools | 2.0.0 | executed bundled pools/rules/tools and complete exports |
| template_prose_project | 0.5.0 | actual local model transcript and reviewed-input custody |
| template_autoscientists | 2.0.0 | bounded multi-step live coordination, matched budgets and honest nulls |
| template_gold_refinement | 0.2.0 | independent refinement/token/claim/figure checks and selected local reviews |
| template_methods_paper | 2.0.0 | compiled units/procedures, illegal-input controls and Methods parity |
| template_redacted_report | 0.2.0 | real pinned raster replay and public invented-fixture redaction controls |
| template_registered_report | 0.2.0 | current registration schema, preserved old hashes and independent statistics |
| template_search_project | 0.2.0 | unpaid retrieval/BibTeX/fulltext/local synthesis/cache provenance |
| template_sia | 0.2.0 | real local proposal/sandbox mutation, held-out scoring and verified rollback |
| template_storybook | 0.2.0 | regenerated pages/contact sheet/alt text/manifest and print PDF |
| template_template | 2.0.0 | independently regenerated final architecture/DAG/source metrics |
| template_textbook | 0.2.0 | fully authored reference, zero stubs, runnable labs and scaffold capability |
| template_pitch_deck | 2.0.0 | every length PDF/PPTX pair, diagrams/citations/QRs and deterministic ZIP |

## Verification ledger

Scoping established source contracts only. Implementation tests, installed
package checks, all-project coverage, renders, live services, sandbox transfers,
and production publication each require their own evidence. Store volatile
runtime receipts in ignored output directories; preserve concise command/result
summaries here when a package is verified. Never promote a local snapshot into
hosted or external evidence.

### Dated integration assessment: 2026-10-02

The user authorized comprehensive implementation and integration to main.
The following observations concern the current uncommitted implementation tree
with root checks on Python 3.14.4 unless identified otherwise. They are scoped
local evidence; source edits after a check
require proportionate refresh. No new main commit, hosted acceptance, root tag,
release, or external publication is established by this assessment.

| Lane | Actual local observation | Boundary |
| --- | --- | --- |
| Root release handoff | All 53 selected release-admission and root-release controls passed. | These exercise fail-closed admission; they do not supply the missing complete candidate evidence or a hosted acceptance uploader. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Public static checks | The latest public Ruff and formatting sweeps passed; mypy passed 1,733 source files. Confidentiality, staged-secret and generated-artifact guards, strict drift, backlog, skills/exports and workflow syntax checks also passed their selected sweeps. | Subsequent source repairs still need their final declared checks; no whole-infrastructure coverage pass is inferred. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Execution diagnostics | Successive first-failure batches recorded 26, 64 and 101 passing cases before unrelated test-fixture assumptions stopped their batches. | These are failed diagnostic batches, not accepted full cohorts. Their completed cases cover incremental controls, artifact/matrix/worker boundaries, prepared plans and execution records; migrated fixtures require their actual reruns. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Approval/rejection controls | Two actual approval cases and an actual rejection/byte-preservation case passed after targeted repairs. A later deadline diagnostic recorded seven passing cases before a no-child exit-code assumption failed. | Exact-once execution and rejection evidence is scoped. The subsequent process-control row records the post-repair outcome; full infrastructure acceptance remains separate. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Outstanding process controls | All five targeted cases passed in 118.50 seconds: failed fresh/resumed attempts preserve prior checkpoint bytes, a frozen outer budget times out an actually launched child, and both capture modes clean up an early-exit parent's detached descendant. | These close the outstanding fixture/repair controls from the earlier failed diagnostics; the whole infrastructure coverage gate remains separate. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Coverage provenance | The counts writer refused stale measurement-support identity. | No replacement counts or provenance were fabricated. Genuine all-project measurements, refreshed provenance and the complete infrastructure coverage gate remain required. |
| Initial public coverage diagnostic | The release-profile sweep completed with 17 measured projects, eight failed measurements and eight drifted values among the measured projects. | The writer refused to rewrite the incomplete snapshot. No fresh coverage provenance or whole-public acceptance is claimed; repair the failed cases and remeasure changed sources before refreshing provenance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Explicit offline preparation | `UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never uv sync --locked --group public-exemplars` passed. Sequential qualified-roster project setup with `uv sync --locked --project projects/<qualified-name> --extra dev` passed for all 25 public projects; Formal also selected `--extra formal-tools`. | Only already cached dependencies were used. This prepares current local environments; it does not establish three-runtime execution, coverage, installed wheels or live acceptance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Publication repair | Independent review closed the Pages credential/target/Git-authority and standalone-mirror held-file repairs. All 67 selected real local Git/filesystem controls passed, including divergent push refusal, inherited configuration/helper isolation and case-equivalent Git-control rejection. | Local conformance does not establish actual external sandbox transfer, exact removal parity, retrieval/reinstallation or production publication. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Packaging custody | Removed 94 newly staged Meta build copies from the index while retaining local files. Root-only build/dist ignores, forced-add guards and source exclusions passed all 64 selected guard/fingerprint controls; independent review closed. | Nested authored build/dist inputs and explicitly consumed package content remain fingerprinted; immutable publication evidence is preserved. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Native startup | All 31 actual startup controls passed in 85.47 seconds after fresh independent source review. Parent supervision begins before native launch; one admitted interpreter retains its PID through the audited seed transition and carries the original startup deadline. | Real pre-receipt and post-READY configuration controls, parent interruption, child exit 130 and non-reset deadlines were exercised. Normal-site behavior matches an independent direct invocation of the selected interpreter; this does not assert a universal `.pth` execution count. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Frozen registered-report records | All 92 isolated project cases passed in 6.71 seconds with 93.85% own-source branch coverage on the selected Python 3.12.13 environment; fresh independent source review closed. | New records are exclusive, held-file writes; existing valid records retain their exact bytes. Changed or tampered intent, links, special files and concurrent replacements refuse reuse. The historical frozen archive hash remained unchanged. This does not establish all supported-runtime cells. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Canonical promotion CLI | All 27 attestation and candidate controls passed in 1.46 seconds after migration to explicit subcommands; fresh independent source review closed. | Retired positional routes exit 2 before loading; validation retains authorization, redaction, expiry and candidate-source requirements. Offline validation does not supply actual owner authorization. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |
| Native-format conformance | All 55 selected native/readiness controls passed in 35.83 seconds after two fresh independent source reviews closed. | These are scoped parser, variant, process, deadline, artifact-custody and readiness controls. They do not establish a completed whole-public render run or full native visual/content acceptance; required unsupported controls remain blocked. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 --> |

Fresh independent shared-infrastructure review closed the reviewed typed
outcome/checkpoint, prepared-role, selected-runtime/hydration, startup `.pth`,
hook/report and original child-exit repairs. Runtime cohorts still need actual
completion against stable sources. Review does not replace executed acceptance.

The initial coverage sweep exposed concrete blockers. Active Inference lacked
the workspace runner's `pytest-benchmark` dependency; Formal failed collection
on an unregistered `timeout` marker; Prose failed collection because `requests`
was unavailable. AutoResearch's manuscript-source cases, Autoscientists' provider
worker cases, Search's changed-artifact diagnostic case and EDA's actual selected
kernel/deadline cases failed. EDA measured 89.38% coverage. SIA measured 79.15%, <!-- noqa: drift-counts -- dated diagnostic: 2026-10-02 -->
with eight Docker-backed skips and one deselection, and failed the required 90%
floor. Passing coverage percentages alongside failed tests do not authorize a
measurement. This selected-environment diagnostic does not establish the
three-runtime matrix. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 -->

Pages and standalone-mirror repairs preserve existing destination-only files
through update-only copies. That avoids destructive clearing but leaves exact
source-removal parity unresolved: stale destination files cannot be presented as
an exact export. `P4-PUBLICATION-REMOVAL-PARITY` requires a reviewed removal
manifest bound to the destination and actual diff, with immutable publication
evidence and unrelated destination-only records protected. Local credential and
file-custody controls do not close this separate requirement.

The old combined installed/formats backlog action is decomposed into independent
installed-matrix, actual rendering, and native-format receipt slices. The runtime
backlog now invokes `--acceptance-matrix` with explicit prepared environments
and the genuine admitted Meta provider wheel. The diagnostic `--profile release`
route and the structural public-template audit cannot close those required lanes.
Exact preparation and execution procedures live in
[`public-runtime-matrix.md`](../development/public-runtime-matrix.md) and
[`installed-wheel-matrix.md`](../development/installed-wheel-matrix.md).

The supervised native-format producer now emits fresh source-bound partial
receipts for actual core execution, exact artifact variants, native parsers,
tool versions, fonts and complete PDF rasters. Its strict reader independently
reconstructs those obligations and refuses inventory-only evidence. Full
visual/content acceptance remains blocked: generic PDF source/layout parity,
browser HTML, native DOCX/EPUB readers, projected slides and project-specific
pitch, newspaper and storybook controls still require independent implementations
and actual acceptance. `P4-NATIVE-FORMAT-RECEIPTS` retains those future actions;
see [`native-format-acceptance.md`](../guides/native-format-acceptance.md).

Native startup supervision is implemented and verified: the earlier
probe-to-second-launch gap was removed by retaining one
admitted interpreter through the seed transition. The parent bounds native
startup before a timer-armed receipt, and the seed retains the original admitted
deadline. This scoped result does not replace full infrastructure acceptance or
the separate supervised execution and descendant-cleanup contracts.

The required whole-public runtime and installed matrices, every declared native
format, current live unpaid capabilities, sandbox transfers and exact-revision
hosted/release evidence remain outstanding. The initial diagnostic encountered
an unavailable Docker engine; the post-reboot assessment below records its
subsequent recovery. Platform 4.0.0 remains an intended unreleased version until
every required exact-revision acceptance lane passes.

A fresh origin/main fetch still identified the starting revision
`f1914383a08f0f4195134ed33a359b7aacc4f978` during this assessment. That ancestry
observation is separate from the still-pending implementation commit and push.

### Post-reboot reassessment: 2026-10-02

Pre-reboot temporary logs were erased during the reboot. Their dated summaries
above remain historical observations; they are not retained raw receipts for the
current source. New runtime records use a persistent, ignored directory under
`output/readiness/`.

All supported Python environments were prepared from locked, cached dependencies
with downloads disabled. Preparation is distinct from the required runtime and
installed-wheel matrices. Normal Docker Desktop startup restored the actual
engine without resetting its storage. A loopback-only Ollama service exposes
already installed models; service availability does not establish model execution
acceptance.

The selected EDA execution diagnostic passed thirteen cases before its new actual
aliased-import control exposed a default audit-hook origin defect. The shared
repair normalizes only the module's own loaded origin; explicitly supplied
traversal paths remain rejected. Both new real child controls passed, and fresh
independent source review closed. The complete notebook execution module then
passed all forty-five cases in the selected Python 3.12 environment, including
actual fresh kernels and the aliased-import control. All three selected Autoscientists provider-worker controls
passed with actual HTTP requests and exact request/response-byte comparisons;
they are controlled provider fixtures, not live model acceptance.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 -->

Package inspection also exposed undeclared platform imports and a generator
custody path that assumed a source checkout inside an installed wheel. Current
dependency declarations and genuine distribution custody are being repaired;
offline lock/sync success does not substitute for functional installed execution.
The two repaired Autoresearch manuscript producers and ten connected Search
composition cases passed their isolated post-reboot runs. Both source-only
platform identity controls passed, including genuine absence of installed
distribution metadata and rejection of a wrong checkout package name.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-02 -->

Independent review of the proposed publication-removal implementation found
retained rollback bytes sharing the restored destination inode, case-equivalent
ownership-record names, a successful exit for a blocked publication, and a
missing final whole-source revision check. A subsequent review found mutable
push destination authority. Repairs for all five findings passed fresh source
review; actual removal, rollback, transfer and destination controls still require
their post-repair runs. Publication-removal parity and external transfers are
still unverified.

Further connected review identified acceptance gaps: runtime-case evidence was
not checked for scopes with no local provider dependencies, standalone mirrors
omitted declared sibling resources, and TestPyPI verified an unpinned package
alias rather than uploaded bytes. Their repairs passed fresh source review.
Execution specs now carry their original hash into both child entrypoints;
exact project-root Python files also enter admission and executed-code checks.
The publication reader separates standalone tag/remote commit parity from the
monorepo origin bound to its canonical export. Actual complete runtime, native,
mirror and sandbox transfer acceptance remains required.

The first new installed custody diagnostic stopped before its intended startup
control because uv treated a hash character in a local wheel path as URL
fragment syntax. A genuine path experiment demonstrated that named package
references preserve the percent-encoded path. The admitted installer now binds
that name to validated wheel metadata. The connected installed/readiness cohort
passed all forty-seven cases, including actual unsafe-wheel startup controls,
original private-copy custody, strict installed-reader refusal and distinct
standalone/monorepo Git commits. This is scoped conformance, not the complete
installed matrix.

An initial collection refusal exposed a circular import through the canonical
PyPI adapter. Executable imports are now delayed until publication is invoked;
unused destructive/unbounded build and upload routes and their exports were
retired. Both source reviews closed. The next runtime cohort stopped at a module
fixture before cases because the function-scoped reference clock had not run.
That fixture now supplies an explicit disposable clock; production callers still
require their genuine candidate or explicit exported-execution clock. Its actual
cohort rerun remains required.

The public Ruff sweep, type checks across the current source surface, and
MEDIUM+ Bandit passed. A single formatting correction is applied and its local
check passes; the final full formatting and generated-document gates remain
required. All public exemplar environments passed refreshed locked offline
preparation. Explicit build-tool setup downloaded one missing cached publishing
dependency; no lock changed and normal execution remains offline. CI now prepares
the locked backend, actual Poppler tools, and the separate exact Autoresearch
runtime lock before its offline standalone controls. Independent CI review closed.

Fresh core review found compilation/launch gaps: constructor-cached approval
policy could survive a declaration edit, and pre-stage hooks could replace
approved inputs before the child ran. The repairs now freeze original declaration
and control identities, recheck admitted inputs after hooks and before each
attempt, and retain original failed-child outcomes if a later retry is refused.
Matrix execution now carries once-only shared verification, explicit resume and
an isolated shared runtime namespace. Fresh independent source review closed
these scoped repairs; their actual final runtime cohort is still required.
Cooperative TestPyPI parent reporting and finalization still need a supervised
deadline proving case; child deadlines alone do not establish that whole-operation
claim.

Main remains protected by the required hosted `CI Gate`. Integration must use
passing evidence for the implementation commit and a normal non-forced push.
The successful hosted baseline run does not establish acceptance of this dirty
implementation tree.

### Continued verification: 2026-10-03

All eighty-eight selected runtime-evidence, public-acceptance, prepared-provider
and required-readiness cases passed across the retained completed cohorts. The
unsafe timestamp-cache positive control now explicitly creates timestamp
bytecode: the ambient reproducibility epoch otherwise made Python create
checked-hash bytecode and invalidated the intended negative experiment. An
initial provider-setup error came from the controller replacing its prepared
PATH; the controller now preserves that PATH while applying credential-free
child policy. The remaining thirty-eight cases passed after that correction.
These are genuine scoped conformance results, not the whole-public runtime
matrix. <!-- noqa: drift-counts -- dated scoped receipts: 2026-10-03 -->

The actual native PDF cohort passed three cases and then failed a baseline byte
comparison. ReportLab's invariant mode still consumes the ambient
`SOURCE_DATE_EPOCH`, so independently regenerated control bytes disagreed with
the module-held fixture. The failure is retained; the source-owned deterministic
generator needs repair and an actual cross-clock proving run before acceptance.
<!-- noqa: drift-counts -- dated diagnostic: 2026-10-03 -->

The publication cohort passed thirteen real controls before its genuine offline
build failed artifact admission. UV produced the wheel and source archive but
also creates output-directory control metadata by default. Producer
configuration must preserve the strict two-artifact contract. No completed
publication cohort or sandbox transfer is inferred from that successful build.
<!-- noqa: drift-counts -- dated diagnostic: 2026-10-03 -->

The latest full public Ruff and formatting checks passed; mypy passed all
1,743 selected source files. The shared-runtime role and original declaration
witness have fresh independent source review. Final infrastructure coverage,
all-exemplar coverage, hosted checks and publication receipts remain separate
requirements. Cold release preparation and stale main-protection guidance are
also being corrected from verified workflow ordering and live protection data.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-03 -->

The deterministic PDF control generator now uses fixed PDF objects instead of
ambient-clock-dependent ReportLab metadata. Its thirty native/readiness cases
passed after the fixture began passing independently validated tool payloads to
the strict reader. A later shared audit repair changes the implementation
identity and requires the connected native cohort to be refreshed.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-03 -->

The real offline UV build now disables output-directory control metadata while
retaining exact wheel/source-archive admission. All eighteen TestPyPI custody
cases passed in the subsequent diagnostic. The actual standalone exporter then
exposed a before-payload bytecode gap: the final audit rejected a poisoned cache
only after its module had executed. The shared audit now compares the actual
code object with freshly compiled held source before execution. Ten real
current/stale cache controls and the actual selected-prefix exporter control
passed. Fresh independent source review closed; this is not sandbox transfer
acceptance or a completed publication cohort.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-03 -->

The renewed core cohort collected its complete selection and recorded eleven
passes before a resume control stopped before its hook. The retained report
identified an unresolved macOS Java launcher, which correctly cannot authorize
reuse. The actual installed Java backend was verified and will be nominated in
the renewed execution environment; the refusal predicate remains intact. Four
new test calls were also corrected to the canonical keyword-only HITL API and
independently reviewed. No completed core cohort is inferred from this failed
diagnostic.
<!-- noqa: drift-counts -- dated diagnostic: 2026-10-03 -->

Read-only standalone inventory found twenty-four declared public repositories
with existing main branches. The declared Experiment Tree repository returned
`NOT_FOUND`; its existence is not established. Thirteen exemplars retain
parent-relative Root sources, and Advanced Literature Review also retains a
sibling Meta Analysis source. A versioned installation projection must bind an
actual public Root commit and genuine provider identity before portable
standalone setup and full-suite acceptance. Source-export byte parity remains a
separate contract. The user explicitly authorized main pushes for Root and all
public standalone exemplars; no such push has occurred in this assessment.
<!-- noqa: drift-counts -- dated live/source inventory: 2026-10-03 -->

Four independent CI jobs no longer wait for lint, while every existing check
and CI Gate requirement remains present. Workflow graph checks pass;
independent review and exact-revision hosted timing/results remain required.
Active Inference's unused forwarding hydration script and its current guidance
were removed. Its canonical strict producer and generated method inventory
must be regenerated and validated before acceptance.

### Reassessment: 2026-10-05

The actual CI completion cohort passed all seventy-three cases, executing the
workflow's real Bash and jq aggregate. It rejects missing required jobs,
undeclared jobs, failed or cancelled results, and skips without their exact
source-owned reason. Fresh independent review closed this contract. This local
conformance does not establish hosted success or a measured timing improvement.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-03 -->

Active Inference's strict canonical hydration, method-inventory generation and
documentation contract completed successfully. Regenerated evidence reflects
the intended version and current source hashes. No draft allowance was used;
numerical, installed, rendered and live acceptance remain separate obligations.

The renewed core cohort recorded one hundred eighteen passes and two failures.
One genuine compiler child emitted a plugin informational log before its JSON
contract. Plugin parsing and merging now preserve their pure return values
without creating that logging side effect; a positive outside-checkout compiler
control complements the existing source-mutation controls. The other test
expected a generic failure for absent prerequisites; its assertions now require
the declared blocked state, exit seventy-five, missing-input diagnostic, and no
child execution. Fresh runtime verification is still required.
<!-- noqa: drift-counts -- dated diagnostic: 2026-10-03 -->

Independent review also identified interruption and timeout precedence gaps in
runtime evidence aggregation. Repairs retain original supervised child exits
before validating incomplete receipts, and distinguish a cell's own deadline
from a pytest child's exit. Genuine interrupted-child and selected-interpreter
controls must pass before this lane closes. Missing root case classification
continues to block whole-root acceptance.

### Dated implementation receipts: 2026-10-01

These dated records preserve scoped, uncommitted-tree results on Python
3.14.4 unless identified otherwise. They are historical observations, not
current measured counts; current counts belong in `docs/_generated/COUNTS.md`.
They do not establish the final all-project matrix, hosted checks, release
readiness, or publication.

| Lane | Verification | Result and boundary |
| --- | --- | --- |
| C1/C5 declarations and operating surface | Isolated Methods/orchestration/matrix/worker tests and mypy | 396 passed, 9 configured slow deselections; 36 source files type clean; public Methods source audit: 25 projects, zero errors/warnings. Subsequent root policy/cache changes require fresh integration checks. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Rendering/reporting facade migration | Focused renderer and report suites | 110 passed after migrating consumers to implementation modules. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Root/exemplar version contracts | Version, metadata, capability and readiness controls | 140 focused tests passed; 26 dependency locks pass offline checks; publication metadata distinguishes intended and published versions. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Notebook | Isolated real-kernel project suite | 109 passed; 92.26% own-source coverage. Kernel deadlines and invalid execution fail acceptance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Prose | Isolated project suite and actual local model producer | 181 passed; 92.13% own-source branch coverage. An actual supervised llama3.2:1b request completed with retained request/response/source/model bytes. Focused controls cover stale receipts, wrong-model/zero-generation, source changes and deadlines; remaining runtime/installed/format lanes still require acceptance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| SIA | Real Docker controls and isolated source suite | 124 passed with one actual-model deselection; 92.62% own-source coverage after custody/watchdog repair. Independent actual local-model + pinned Docker acceptance passed: two proposals rejected against the stronger baseline, frozen inputs and rollback verified, no host source application. An earlier malformed/truncated proposal failed safely and remains retained. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Textbook | Strict completeness/generated audit and isolated source suite | 49 authored configured sections, 30,189 words, zero draft markers; 297 passed, 96.27% coverage, 32 real Python examples; 34 plots and 13 Mermaid figures regenerated. All declared document formats remain to be accepted. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Descriptor/registered-report producers | Real invalid-domain CLI controls and project suites | 78 descriptor and 46 registered-report tests passed. Invalid producers return nonzero while retaining diagnostics. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Autopoiesis | Source suite and selected real child archetypes | 550 tests passed at 93.00% own-source coverage before final custody refinements; 248 subsequent child/grammar/honesty controls passed. All five selected archetypes executed actual tests and analyses with independent numerical comparison. The larger nominal grammar matrix and child PDF rendering are not claimed. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Active inference | Actual installed pymdp and Lean tracks | Repaired the pymdp adapter's `C`/`D` vector shapes; 12 actual state/policy rollouts agree with independent Bayesian and information oracles within recorded numerical tolerances. Actual Lean kernel/axiom checks and source-directory symlink controls pass. These tracks retain their explicit proof-binding limits; final rendered outputs and runtime matrix remain outstanding. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Formal | Isolated full suite with actual Lean/TLC controls | 307 passed, 91.81% own-source branch coverage after the frozen verified-jar repair. Concurrent jar corruption cannot change the bytes consumed by model children, and prevents final cache-custody acceptance. A fresh canonical live receipt remains required after the runtime-directory filter repair. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| AutoScientists | Isolated source suite and bounded actual local model coordination | 174 passed with one actual-model deselection; 95.77% own-source coverage. The actual matched-budget run made 12 model calls and found zero clean advantage over baseline. Its transitive implementation-custody repair requires a new live receipt; no model-improvement claim follows. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Pitch deck | Isolated source suite and disposable rendered pairs | 156 passed, 97.30% own-source coverage; six actual PDF/PPTX pairs rendered. Final source-bound format/visual/installed acceptance remains required. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Madlib | Isolated source suite | 198 passed, 99.31% own-source coverage; current schema and deterministic branch/injection controls pass. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Readiness | Required-profile and independent laundering controls | Required evidence profiles identify 344 gates. Missing receipts remain unknown; candidate preparation cannot authorize production. Independent checks refuse stale/mismatched evidence and archive traversal. This is contract evidence, not 344 passing acceptance lanes. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Checkpoint/report custody | Fresh independent real-process controls | Forged checkpoint prefixes refuse before child execution; reports refuse mismatched stable keys and aggregate exit codes while preserving original child codes. Independent execution-record/report cases: 16 passed. Checkpoint schema/record and report adversarial controls: 30 passed. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Confined artifact writer | Fresh independent file/concurrency controls | Ancestor descriptors are held without following links for text, binary, append, locking and removal. Independent controls passed, including exact binary bytes, symlink sentinels, private permissions, and 20 concurrent first-creation rounds without lost records. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Installed-wheel harness | Actual disposable install negative controls | 18 provider-closure controls passed with fresh independent review. Current wheel admission also rejects invented members, private files, old namespace layouts and changed metadata. Actual root and resource-pool wheel smoke runs succeeded outside source checkouts, but subsequent source changes make those receipts unsuitable for final acceptance. The final 78-cell installed-package matrix has not run. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Executed-code custody | Actual fresh-cache imports and poisoned-cache controls | All 44 helper controls passed in a fresh independent run after formatting, covering startup-code admission, ancestor replacement, timestamp-valid poison, removed modules, post-import cache mutation, absent/late audits and installed RECORD faults. Another independent guardian/audit/report cohort passed 38 cases. The hook compares actual executed code objects with current source without decoding cache payloads; it cannot recover original comment bytes from compiled code. The final all-runtime matrix remains outstanding. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Ancestor custody | Fresh independent real filesystem mutation | The initial audit reader could consume bytes from a detached ancestor after its lexical path was replaced. It now holds and rechecks the complete directory chain. All 16 standalone audit controls passed independently, including actual outer/inner directory replacement. Controller loaders received the same repair. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Interrupt cleanup | Fresh independent OS signals and process evidence | A stopped guardian plus actual SIGINT reproduced a surviving detached writer. Caller token sweeping now runs in an outer `finally`; four copied C4 controls passed after repair. Another four generic boundary controls passed, including SIGINT after timeout root kill: the retained traceback cannot trigger a masking Popen finalizer, `waitpid` proves explicit root reaping, and no writer survives. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Literature engine migration | Independent domain-output parity and full controlled suites | 24 real comparisons preserve Advanced's sampling and source-routing policy after adopting the declared namespaced Meta engine distribution; another 25 artifact/value/error comparisons passed for shared variables. Fresh full suites on Python 3.12.13 passed: Advanced 157 cases/94.30% branch coverage, Meta 1,237/95.62%, Search 330/96.20%. Another 92 shared acceptance/config/custody controls passed. Controlled HTTP/model fixtures establish conformance; actual free-provider/model receipts and the final runtime matrix remain required. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Resource-pool exemplar | Isolated full source suite | 306 passed with 94.77% own-source coverage, exercising bundled fonds, rules and tools. A portable namespaced source package satisfies the authoring contract without an unused flat namespace shim. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Matrix execution | Actual worker concurrency and deadline controls | Four actual controls passed for bounded CLI completion, overlapping distinct worker processes, same-project lock contention and refusal to launch an expired report. These scoped results precede the final executed-code audit integration; full fresh serial/parallel acceptance remains required. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Public static checks | Declared public source surfaces | Ruff passed all 81 lint paths; mypy passed 1,705 source files; MEDIUM+ Bandit passed with narrow, explained admitted-source execution annotations. Formatting, exports, skills, operations, API/roster/stage generation, confidentiality and artifact guards passed in the fresh selected health sweep. Documentation lint found two stale retired-interface references; those were corrected and await its rerun. Lexical mock checks covered 1,372 Python test files; the separate semantic inventory recorded zero dependency replacements. Final source changes require proportionate refresh. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |
| Fresh core integration | Real stage/cache/report/execution/Prose processes | All 72 selected cases passed in 695.44 seconds on Python 3.14.4, including original exits, missing receipts, poisoned cache refusal, source edits, bound approval/rejection, actual incremental entrypoints, supervised finalization and the real Prose callback. This is scoped integration evidence rather than the full infrastructure coverage or all-public matrix. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 --> |


Current repairs and observations retained on 2026-10-01:

- Serial C4 controls passed for once-only shared verification, parallel worker
  isolation, failure prevention, detached timeout cleanup, interruption, and
  summaries that preserve child exit `2`. The serial batch passed 11 cases;
  the separate public harness closure passed 71 cases. These remain scoped
  conformance evidence. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- An actual source-changing Python stage masked original exits `130`, `124`,
  and `7` as blocked/`75`. The repair preserves executed-run precedence and
  custody diagnostics. All 13 real stage controls passed after repair;
  final stage/provenance controls passed 23 cases, including late guardian
  custody refusal after verified exits. Fresh independent source review
  closed this bounded change. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- An actual Lean input ABA consumed temporarily substituted code while the
  canonical source hash returned to its original value. Native tools now
  consume held frozen source copies. Subsequent Formal and Active controls
  passed 34 and 26 cases respectively, including actual standalone startup,
  Lean/TLC and analytical oracles. The audited canonical Formal producer
  passed all six declared checks against frozen sources and verified jar
  bytes. Final full runtime and global acceptance remain separate
  requirements. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- A real notebook kernel accepted timestamp-valid cached code that wrote an
  unexpected marker without changing its numerical results. The repaired
  kernel consumes frozen admitted notebook/data/source bytes under a private
  audited cache. The actual producer regenerated a portable scientific
  summary; full interpreter paths and process evidence remain private under
  ignored `.pipeline/`, with previous receipt bytes retained by hash.
- The local-model controller initially refused before making any requests
  because its re-verification omitted its fresh cache prefix. After the narrow
  repair and independent review, a genuine matched-budget run made 12 model
  calls and recorded zero clean advantage. Its source identity predates the
  subsequent coverage-inventory repair; it is not final current-revision
  acceptance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- Docker Desktop's admitted engine endpoint returns `503` and its last startup
  error identifies a failed host-side log write. A bounded official application
  restart then failed to stop the application; current engine health remains
  unavailable. This is a current SIA blocker; earlier receipts do not establish
  current acceptance. Existing backend processes and VM, image, volume, and
  settings state were preserved.
- The full infrastructure run stopped with 187 passing cases and a crashed
  coverage-provenance test worker. A direct reproduction exhausted that
  test's 30-second allowance during repeated supervised Git inventory
  queries. The builder and validator now admit the public inventory once per
  invocation. The original 52 provenance controls passed without increasing
  that allowance; subsequent direct/batched hash-parity controls passed.
  The next full run passed 232 cases before a typed hook startup timeout
  was flattened into failure. Both full runs are failed diagnostic evidence;
  neither establishes full infrastructure coverage. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- Genuine installed root and EDA wheels with their exact locked dependencies
  exposed a missing script-worker path before kernel startup. The worker is
  lives in the installed namespace; an outside-checkout kernel
  positive and full project acceptance are required after the repair.
- Actual unchanged-path Java-override and pinned elan-backend byte mutations
  changed tool exit behavior while recorded stage reuse still succeeded.
  The repaired fingerprint binds selected executable/backend bytes and refuses
  unresolved indirect selections. Genuine post-repair tool controls and fresh
  independent review passed; full cache/resume integration remains required.
- Fresh hook review reproduced context-file writes through a linked
  `.pipeline/hooks` directory outside the nominated output. The writer now
  uses the existing held-directory confined writer with private permissions;
  three independent real filesystem controls passed. Real hook timeout and
  interruption checks remain required. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- Actual analysis leaves returning `124` and `130` were both aggregated as
  failure `1`. Analysis children also lacked their own audited selected-runtime
  admission. Typed aggregation and reuse of the held-source stage launcher
  are in progress. Deadline configuration now rejects nonpositive, nonfinite,
  invalid, and retired unlimited settings before producer execution; final
  child/runtime acceptance remains required.
- A later matched-budget local-model run passed within its recorded budgets,
  rechecked its actual source and artifact bytes, and again reported a null
  clean advantage. It predates the subsequent hook/tool identity repairs,
  so it remains a dated scoped receipt rather than final program acceptance.
- Canonical core/live execution now freezes deterministic build policy. Its
  clock is an explicit admitted epoch or the actual candidate Git commit time;
  exported non-Git trees need that explicit provenance. Invalid clocks and
  attempts to disable deterministic execution refuse before launch. Actual
  candidate/export clock and confined literature-cache controls passed 63
  cases. This does not assert universal operating-system network isolation.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- Analysis leaves now retain actual selected-interpreter admission, audited
  source, child attempts, and original exits. All 20 owned launcher cases
  passed, including real alternate-interpreter execution, timestamp-cache
  rejection, source substitution with restored final bytes, interruption,
  detached cleanup, and a changed installed package member. Declaration-only
  dependency metadata cannot authorize analysis caching or resume. A larger
  runtime/stage batch passed 62 cases and timed out in one copied-stage positive
  observer; that exact positive passed alone before its measured test budget
  was adjusted. Fresh aggregate/hook and whole-infrastructure runs are pending.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- A genuine tampered-leaf sequence correctly blocked with original exits zero,
  but a redundant post-write check deleted its failure report. The repair
  retains known false receipts and limits promotion rechecks to complete
  results. Independent source review closed; the actual aggregate rerun remains
  required.
- Lifecycle logging holds bounded absolute leaf hops and the final real
  directory identity through confined append. All 88 ordinary filesystem
  controls passed after one multi-round concurrency fixture exceeded its old
  ten-second observer. Only that fixture now permits 45 seconds; production
  ten-second locks are unchanged. A separate logging-race investigation was
  interrupted by automatic review and provides no accepted execution evidence.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- The obsolete source-import export smoke route is removed. Release preparation
  now warms exact locked nonlocal dependencies separately from the required
  complete three-runtime installed-wheel runner. Focused retirement/version/
  discovery/capability controls passed 56 cases, with 23 additional copy/export
  resource controls; independent shared-infrastructure review closed. No new
  hosted run or complete installed matrix is established by these checks.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-01 -->
- Canonical planning now admits actual bounded regular script files and exactly
  the supported direct method targets; ignored method arguments refuse. Public
  frozen-plan execution applies the same target admission without recomputing
  the DAG. Independent compiler source review closed; refreshed compiler and
  actual invalid-invocation checks remain required.
- Connected Stage-01 review found ordinary generic/custom test dispatch still
  resolving packages through `uv`. The prepared-interpreter and exact declared
  runner-version admission migration is in progress. Active Inference's inner
  verifier now selects one existing interpreter and composes its commands under
  the finite whole-verifier ceiling; actual refreshed acceptance remains
  required after the shared adapter migration.

The full infrastructure diagnostic run did not produce an acceptance receipt:
the default per-test timer interrupted a repeated real-process cache/report
case. That case now declares a finite 90-second test budget; its negative child
deadlines remain short. A prior first-failure diagnostic identified old
AutoResearch declaration fixtures; their canonical migration passed 77
targeted cases. The next full coverage run requires stable sources and current
worker audit integration.

A subsequent stable-source combined execution run passed 74 of 75 cases. The
single failure expected an older diagnostic phrase while the actual source-edit
case correctly returned blocked/75 and preserved child exit zero. Its assertion
now verifies that typed behavior. That combined run precedes the ancestor and
interrupt repairs, so it is scoped evidence rather than final acceptance.

The following loaded source-cell harness diagnostic was stopped after six
outer-deadline failures and five passing cases. Its 40-second whole-cell test
allowance expired while collection alone took 20–27 seconds. Actual cleanup
completed; this aborted run is retained as failed diagnostic evidence. Only
the demonstrated fixture allowances will change before a serial rerun;
production acceptance and short negative deadlines remain unchanged. Two
positive shared-infrastructure fixtures likewise exhausted their outer
allowances; the actual child-exit-2 supervised summary itself passed and
retained that child outcome beside aggregate failure.

Fresh independent review has exposed and driven repairs for detached approval
replay, source-directory exclusions, typed schema discriminators, selected-stage
approval policy, checkpoint false completion, wheel member admission and current
dependency-provider custody. The required readiness profile has 344 gates;
missing receipts remain unknown rather than authorizing release. The
container watchdog has passed whole-controller-tree termination controls.

### Frozen-source reassessment: 2026-10-05

The public main revision remains the starting revision above. No candidate
commit, hosted candidate check, standalone push, release tag, sandbox transfer,
or production publication is established by these local observations.

- The new actual wheel/sdist typing and execution-policy cohort passed all
  16 cases. Its isolated installed consumer rejects both an incorrect return
  annotation and a removed typing marker. Native Git replacement references
  cannot substitute the candidate commit clock or source tree. This is selected
  packaging and policy evidence, not complete installed-wheel acceptance.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->
- The refreshed full public Ruff check passed; strict mypy passed 1,749 source
  files with zero errors, and the declared medium-severity Bandit check passed.
  These checks do not supply infrastructure coverage or domain acceptance.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->
- Formal's complete selected-interpreter suite passed all 319 collected cases
  with zero skips or deselections, but its own coverage failed at 82.45%.
  The actual table and data were retained. Its launcher executes in genuine
  subprocesses and measured zero coverage in that invocation; meaningful
  controller and domain failure controls are required before the unchanged
  coverage gate can pass.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->
- All 13 selected notebook controls passed against unchanged source identities.
  Receipt refresh now runs on disposable authored-input copies; the direct
  launcher uses its owned private cache despite inherited bytecode-write
  settings. Timestamp-poison, selected-cache, independent-computation and
  import-alias controls passed. The whole notebook suite and supported-runtime
  matrix remain separate requirements.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->
- Both isolated original-deadline controls passed, including an actually
  entered project child and detached descendant. A subsequent complete
  orchestration diagnostic passed 162 cases before its short-budget assertion
  failed: aggregate timeout was correct, while timeout evidence belonged to the
  shared/runtime result instead of a selected project stage. Its original
  result was retained. The short control now separates shared-budget exhaustion
  from the unchanged actual-project cleanup experiment; the whole cohort needs
  a fresh run after this refinement.
  <!-- noqa: drift-counts -- dated diagnostic: 2026-10-05 -->
- The Root producer diagnostic recorded successful genuine collection followed
  by custody refusal because its bootstrap omitted the nominated candidate's
  infrastructure audit root. Admission now includes that root alongside the
  actual provider, preserving final verification. The added fresh-prefix poison
  control and the complete producer cohort require executed acceptance.
- The standalone projection diagnostic passed 38 cases before a real Git
  destination query failed. A command-created remote is not a locally configured
  remote for `get-url`. The repair uses the exact synthetic fetch/push rows from
  native verbose resolution and retains the configured-origin push guard. Owned
  diagnostics on both installed Git versions verified fetch and push rewrites
  without editing repository configuration. The full projection/publication
  cohorts still require fresh execution.
  <!-- noqa: drift-counts -- dated diagnostic: 2026-10-05 -->
- AutoResearch's genuine source-provider repairs passed all 17 selected cases.
  Explicit preparation of its exact locked third-party requirements then passed
  a second fresh offline installation. This closes the observed missing-cache
  preparation issue; it does not establish its full hydration/domain suite.
  <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

The earlier multi-project coverage controller was intentionally stopped after
six launched projects; queued projects were not executed. Search and the
selected SIA release-profile lane supplied passing scoped measurements, while
AutoResearch, notebook and Formal failures and an interrupted Autoscientists
run were preserved as diagnostics. The notebook's canonical receipt writer
invalidated that earlier source interval and has since been repaired. No
all-public coverage snapshot was regenerated from this partial run.

Root acceptance still lacks its reviewed complete case-classification policy.
Static marker inspection does not establish parametrized case identity, fixture
custody, tool applicability or unpaid provider eligibility. A genuine supervised
census, closed-world classification and separate required lane evidence are
needed; declaring `complete-offline` for the current Root would misrepresent
those obligations. The unresolved live, native-format, complete runtime,
installed-package and publication gates remain required.

### Continued capacity-limited verification: 2026-10-05

The repaired candidate-root audit and read-only Git destination controls passed
all eight selected cases, including actual fresh-cache poisoning and native
fetch/push rewrite rejection without repository-configuration changes. The
subsequent Root cohort passed six cases before a test confused a legitimate
`runtime-gate.json` with an actual interpreter probe. Both affected predicates
now name the exact runtime probe artifacts. Three repaired controls passed:
the missing-policy control uses a genuine owned isolated interpreter, proves it
never starts, and subsequently proves its marker works. Independent source
review closed; the complete Root cohort remains required.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

The new complete Formal diagnostic collected 363 cases. It recorded 327 passes,
11 failures and 44 errors, including repeated teardown errors, with 88.99% own
coverage. All 44 new launcher, source-contract and configuration controls passed.
Disk exhaustion interrupted fixture, database and tool writes; neither this run
nor its coverage satisfies acceptance. The orchestration rerun similarly
recorded 107 passes and two failures before disk exhaustion prevented final
worker-result persistence. Original results and diagnostics remain retained.
Healthy complete reruns are required without changing coverage floors or
execution deadlines.
<!-- noqa: drift-counts -- dated failed diagnostics: 2026-10-05 -->

The projection rerun passed 38 cases before the bounded guardian refused
implementation custody during startup. Its transport discarded the underlying
exception, so that failure cannot be attributed conclusively to disk exhaustion.
It remains unresolved and requires a fresh run with the original controls.
Owned disposable prepared runtime environments were removed after preserving
their inventories and preparation records; acceptance artifacts were retained.
Those environments must be prepared again before runtime-matrix execution.
<!-- noqa: drift-counts -- dated failed diagnostic: 2026-10-05 -->

Autoscientists now derives its implementation, source and runtime comparisons
from one fresh custody capture at each existing verification boundary. All
controller and worker checks before and after execution, fresh bytecode audits,
active-source rosters and deadlines remain. Independent source review closed.
Actual call-count, source-mutation, provider-byte and deadline controls and the
complete own-source suite are still required; no measured speed improvement or
live model acceptance is inferred from the refactor.

### Reviewed runtime and collection repairs: 2026-10-05

The current local Formal suite passed all 366 cases with 90.37% branch-aware
own-source coverage. The added file-backed SQLite controls exercise closed
connections, typed query errors, consumed transaction handles and persistence
after reopening. An earlier application placed the new test file outside the
canonical project path; that diagnostic collected only the original cases and
failed coverage. The exact reviewed file was moved into the canonical test tree,
and the successful run collected and executed the added controls.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

Pools passed all 306 cases with 94.68% own-source coverage. Search passed 28
focused provider-portability cases and Prose passed 11 focused claim-source
cases; those focused runs did not measure complete project coverage. The Root
provider cohort passed all 38 selected cases. Autoscientists passed eight
selected custody controls. Each retained result records its selected interpreter,
actual command, original child result and unchanged source identity. These are
local, scoped results, not all-runtime, installed-wheel, live or publication
acceptance. Evidence is retained locally under
`output/readiness/platform4-reviewed-batch-20261005/` and the associated dated
portability/custody folders.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

After independently reviewed collection repairs, all 59 Root regression and
source-origin controls passed. The canonical audited collect-only census then
collected 12,972 cases from 771 Root test files with original pytest exit zero,
zero collection errors/skips/deselections and no executed test reports. The
source identity remained current. This closes collection, while the reviewed
explicit case policy, public import closure, runtime lanes and public coverage
remain required. The complete census and original observations are retained in
`output/readiness/platform4-root-case-policy-20261005/attempt-02/`.
<!-- noqa: drift-counts -- dated collection and regression receipts: 2026-10-05 -->

The focused orchestration diagnostic under concurrent heavy suites passed both
original deadline controls but exhausted its positive-case budgets. Repeating
the positive cohort alone passed parallel fresh/resumed execution and the
effective two-project DAG case. Serial fresh execution still exhausted its
120-second whole budget; serial resume was not reached. Completed report
component observations were equal before and after execution, so the earlier
source-identity refusal remains unattributed. A bounded positive-case proving
budget correction is under review; production deadlines and the original
timeout/descendant negative controls are unchanged.
<!-- noqa: drift-counts -- dated failed and scoped receipts: 2026-10-05 -->

The healthy projection cohort remains incomplete after a pytest timeout during
an actual Git status boundary. A separate read-only Git boundary profile measured
1.18 seconds; it does not identify the cause of the whole-cohort timeout or prove
a speed improvement. No required gate is waived. Direct remote verification on
this date still found root main at the starting revision; the implementation is
local and unreleased.
<!-- noqa: drift-counts -- dated diagnostic: 2026-10-05 -->

### Public collection, ownership and execution follow-through: 2026-10-05

The subsequent audited public-only census collected 12,979 Root cases from 772
files with original pytest exit zero, no collection errors/skips/deselections
and no executed test reports. A genuine copied-conftest control exercised two
layouts and five live private import poisons; public collection admitted the
same public case and actual provider without importing those private sources.
Its first assertion-rewriting diagnostic failed the bytecode audit, then the
reviewed plain-assertion fixture passed. Retained originals remain separate in
`output/readiness/platform4-root-case-policy-20261005/attempt-03/` and
`output/readiness/platform4-reviewed-batch-20261005/`.
<!-- noqa: drift-counts -- dated collection and scoped receipts: 2026-10-05 -->

After independent review, serial fresh execution and resume passed under the
finite 180-second positive fixture budget. The actual control verified two fresh
shared checks, one domain execution per project and cached project stages on
resume. Original exit zero, source identity and source/Python/tool component
observations were retained. Production deadlines and both original deadline
negative controls were unchanged. This closes that selected serial case; the
older identity refusal remains unattributed and full orchestration acceptance
still requires a fresh run.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

Root teardown no longer deletes generic persistent project names. A read-only
guard preserves preexisting files, directories, links and new leak evidence;
disposable cleanup belongs to the fixture that owns its temporary tree. Logging
now detaches and closes exact executor-owned handlers on completion/refusal,
constructor failure and the runner's banner error path. A direct module sink
retains ordinary Python progress, while its owned root sink prevents duplicate
observability records. Unrelated handlers remain available. Preview-only callers
must close their executor; simultaneous executors in one process need a separate
contextual logging contract.

All 57 selected Root controls passed: strict case-policy/collection admission,
workspace preservation and real logger lifecycle in pytest and ordinary Python.
The five changed production modules passed strict typing. Original child exit
zero, no outer timeout/custody refusal and unchanged source identity are retained.
The new policy library does not supply the complete reviewed production case
inventory, canonical census/readback, exact lane execution or required readiness
envelope; those remain necessary before Root runtime acceptance can pass.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

Search's thin review entrypoint now uses the shared process guardian, finite
whole/stage deadlines, typed original process observations and confined current
run records. The selected cohort passed 115 cases and failed one existing
missing-summary control. All newly added descendant, interruption, tampering,
selection and confinement cases passed. A subsequent unchanged-producer probe
reproduced exit 124 while waiting for guardian READY under its internal startup
cap, with the actual source unchanged. This is a startup failure, not a completed
missing-summary producer. Its original diagnostics remain retained; a shared
finite startup-budget repair and refreshed connected acceptance are required.
No full Search coverage or installed-runtime acceptance follows from this run.
<!-- noqa: drift-counts -- dated failed and scoped receipts: 2026-10-05 -->

Direct remote verification still identifies Root main at the baseline revision.
The implementation remains local on the candidate branch; no hosted candidate
check, main push, standalone promotion or release is implied by these receipts.

### Required final gates

- Real process outcomes, timeout descendants, interruption, hook failures, and
  malformed/stale/wrong-run skip receipt controls.
- Pause/approve/execute-once and reject/no-execute; approvals excluded from
  deliverable fingerprints.
- Source/input/output/config/plugin/lock mutations and concurrent source edits
  invalidate reuse or completion.
- Actual serial/parallel worker parity, shared gate exactly once, output/log
  isolation, worker reuse, and same-project contention.
- Full public lint/type/no-mocks/security/documentation/export/confidentiality
  gates; infrastructure >=60% and each exemplar >=90% own-source coverage.
- All public projects on 3.12–3.14 and supported macOS runtime behavior; fresh
  clones and installed packages outside source checkouts.
- Fresh independent shared-infrastructure/security review.
- Required free/local live capabilities and actual sandbox publication with
  retrieval/reinstallation. Missing tools/providers/credentials remain blocked.
- Production remote commits, export hashes, retrieved assets, DOI roles, URLs,
  and exact-revision root release evidence.

No root tag or release is authorized by a partially green local ledger.

### Source traversal, worker selection and retry follow-through: 2026-10-05

Fresh independent source reviews closed the bounded readiness traversal,
guardian startup budget, actual launched-process fixtures, notebook provider
selection, standalone Meta command, and canonical Root census/readback changes.
Their actual local results remain scoped to the identified input trees and
selected interpreters; no hosted check, main push, three-runtime acceptance,
installed-wheel matrix or publication is established by these observations.

| Lane | Actual local observation | Boundary |
| --- | --- | --- |
| Readiness traversal | All 54 connected traversal/fingerprint/snapshot controls passed in 14.16 seconds; source stayed unchanged. A controlled 6,000-file runtime tree retained exact old-policy hash parity. Current complete source traversal measured 4.83 seconds initially and 4.14 seconds on repeat. | Timing depends on cache/order and host; no universal speedup or weakened generic fingerprint policy is inferred. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| Guardian and process cleanup | The fresh connected run recorded 163 passing cases and one failed old retry fixture in 258.12 seconds. All repaired ordinary and detached descendant controls established real startup/native-live evidence before cleanup. | This remains a failed full cohort; its original records and the earlier 160-pass/3-failure cohort are retained. Production and original matrix deadlines were preserved. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| Coverage retry supervision | After repairing the fixture, both targeted controls passed in 24.18 seconds. An actual first-attempt conflict consumes eight seconds; the real second attempt starts under the original whole deadline, returns original 124, and its observed live child is dead. | This proves supervision with controlled child diagnostics; it does not establish recovery from an independently corrupted real coverage database. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| Search missing-summary regression | The unchanged original regression passed in 6.48 seconds after the guardian repair, with original exit zero and unchanged own source. | Full project coverage, installed execution, unpaid retrieval and publication remain separate. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| EDA standalone/source cache controls | All six selected real controls passed in 78.33 seconds on Python 3.12.13. Both launcher and worker bind the actual SDK before own source; fresh kernels produce independently verified computations, and actual timestamp-valid poison caches are ignored by audited execution. | Earlier invocation and worker-shadow failures are preserved. Copied provider/source fixtures are not genuine installed-wheel or all-runtime acceptance. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| Advanced literature provider controls | The whole run recorded 156 passes and two new test-name normalization failures, with 94.30% own branch coverage. The independently reviewed correction accepts genuine canonical distribution-name spelling while preserving exact provider/version/record/source checks. | Current corrected full-suite execution remains required; the failed measurement is not a passing receipt. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 --> |
| Canonical Root census | The first connected attempt failed its shared fixture: a plain reader compared its loaded-baseline bytecode context directly with the audited worker context. The reviewed repair retains exact source/distribution/runtime equality and requires the original worker's fresh audited binding. | Actual repaired controls, complete production case policy, exact lane execution and required readiness wiring remain required. Collection alone cannot authorize runtime acceptance. |


### Execution integration and provider review: 2026-10-05

The current real execution-contract cohort completed with 263 passing cases and
three failures in 1264.23 seconds, original exit one, no outer timeout or custody
refusal, and an unchanged source identity. The actual serial/parallel resume,
original matrix deadlines, descendant cleanup, project DAG, cache and owned-log
controls passed. The three failures involved two stale test API calls and a
noncanonical shared-gate fixture; independently reviewed fixture migrations
preserve pre-execution refusal, exact HITL approval and original child exit two.
Fresh repaired execution remains required. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

Meta's standalone command controls passed all eleven cases; the three Root CLI
controls passed. The connected census then recorded 37 passes and one failure:
its 30-second timeout occurred before the controlled descendant launched. This
is failed collection-control evidence, not descendant-cleanup acceptance. The
reviewed proving fixture now requires actual import, live-token and native
cleanup evidence inside a finite whole deadline; production deadlines remain
unchanged. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

The same-revision public static attempt passed ten of eleven gates. Bandit found
two unsafe XML reader calls in the new Meta test controls; the reviewed migration
uses its already declared and locked defusedxml dependency. Search's report now
consumes one confined held source snapshot, rejects source changes including an
A-to-B-to-A observation, and distinguishes regular files from directories. Its
historical review JSON remains byte-identical. Reviewed Auto, Pitch and Template
SDK bootstraps separate executable SDK selection from genuine whole-source DATA.
All newly applied slices still require fresh runtime and coverage evidence.
<!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

A read-only component profile of the retained genuine census found two SDK
captures at one reader boundary. The reviewed optimization removes the duplicate
observation and a discarded checkout-only source scan; installed RECORD/source
parity and distinct worker/coordinator checks remain. The measurement does not
explain the earlier cold admission time or establish a general speedup.

The actual declared standalone destinations resolve to public main repositories
except Experiment Tree, whose repository remains absent. Pitch Deck's declared
repository uses its existing hyphenated name. No candidate commit, hosted
candidate result, main update, standalone push or 4.0 release is established yet.

### Original deadlines and reviewed consolidation: 2026-10-05

The refreshed canonical census controls passed all 39 cases in 393.43 seconds.
Meta's actual whole suite passed 1,244 cases with 95.62% own branch coverage; the
six selected Pitch/Template provider controls passed. These are local selected
interpreter results, not complete three-runtime or installed publication evidence.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

A later execution cohort recorded 68 passes and one worker crash at the original
90-second shared-gate case. The parent interrupted the exact owned pytest after
it remained stalled; pytest returned original two. The original cache case then
failed its unchanged 120-second deadline both before and after the reviewed
metadata repair. All original failure logs and cleanup records remain retained.
<!-- noqa: drift-counts -- dated failed receipts: 2026-10-05 -->

The metadata repair passed seven genuine controls and preserved the original
350-member payload digest. Its observed generator entry/continuation count fell
from 702 to two; elapsed instrumented component observations were 1.05 and 0.07
seconds. End-to-end cache acceptance still failed. A subsequent native observer
found repeated full source checks; the reviewed consolidation now uses complete
call-local tree rows while keeping every later execution, cache/resume and
completion observation fresh. No broad speed or completed-run claim follows
from either component profile.
<!-- noqa: drift-counts -- dated diagnostic and scoped receipts: 2026-10-05 -->

Autopoiesis's actual whole suite recorded 565 passes and two failures, with
94.71% own branch coverage. The failures exposed an eager plotting import in
pure materialization and a CPU-limit control that had not proved child launch.
The independently reviewed repair keeps lazy public figure exports and separates
the CPU allowance from the unchanged whole deadline. Real launch and native
SIGXCPU evidence are now required by the proving control; runtime rerun remains
necessary. Search's whole suite reached 93% collection progress with three
failures, then hit its original 1,800-second outer deadline. Original child exit
minus nine and unchanged own source were retained; no final coverage or complete
suite result was produced.
<!-- noqa: drift-counts -- dated failed receipts: 2026-10-05 -->

Fresh independent source review closed and the parent applied the complete
ordinary-CI partition, immutable public-reference reader, single-boundary source
observation and Autopoiesis import/resource repairs. CI preserves the original
case deadlines and marker policy, requires complete nonempty shard receipts and
actual merged branch coverage. Public reference binds real Git identity, admitted
public bytes and the existing pinned submodule; source-only review does not grant
runtime or publication acceptance. The complete Root policy, runtime profile and
bound exemplar consumers remain under review.

Direct remote verification still identifies main at the baseline commit; admin
enforcement requires CI Gate. No candidate commit, hosted candidate result, main
update, standalone push or root release is established by this entry. All earlier
failed observations remain part of the program record.

After the optional plotting import repair, the unchanged original cache regression
passed all four executions in 75.83 seconds under its original 120-second case
limit, with original exit zero, no outer timeout/custody refusal and unchanged
source. The prior failed runs remain retained. The selected Search diagnostic
recorded 30 passes and one failure in 143.58 seconds; the live positive and
forged-quote controls passed under the existing limits. Its remaining confined
leaf read returned actual POSIX ELOOP; a reviewed errno assertion preserves the
no-launch and external-file controls. This closes neither full Search coverage
nor the cause of its earlier whole-run timeout.
<!-- noqa: drift-counts -- dated scoped and failed receipts: 2026-10-05 -->

## Planning checkpoint: 2026-10-05

Implementation stopped at the requested scoping/handoff boundary. Remaining
root and public-exemplar work is decomposed into future-only TODO rows with
stable IDs, dependencies, proving artifacts, commands and negative controls.
Independent scoping review separated profile definition from aggregation,
pre-push portability from post-push remote receipts, and local domain/sandbox
verification from externally authorized promotion. Existing tool/provider and
private-promotion blockers remain active; prior completion prose moved to the
dated backlog history. No implementation proposal was applied at this checkpoint.

The last actual selected source-control cohort completed naturally with
38 passing and two failing cases in 174.10 seconds, original exit one, no outer
timeout or custody refusal, and unchanged source identity
`cc6b29da4966b1b147a80ed1ba657a2bb023c8e9e251a91a16e568b52a2eb816`. Both failures
are optional-plotting import controls: ordinary pipeline/interactive consumers
still load Matplotlib, and genuine no-site reporting import reaches a missing
PIL dependency through the rendering/transmission import chain. The aggregate
is failed; passing fingerprint/literature controls are scoped evidence only.
The original deadline cache case's earlier pass remains scoped to its tested
source and environment. <!-- noqa: drift-counts -- dated scoped receipt: 2026-10-05 -->

At this checkpoint, HEAD and a fresh remote main query both identify
`f1914383a08f0f4195134ed33a359b7aacc4f978`; the coordinated implementation remains
on `codex/platform-4` as staged/unstaged/untracked work. No new commit, push, PR,
tag, release, sandbox transfer or production publication has occurred.
Intended versions and source-reviewed changes are not published or fully
accepted versions. Root case policy, full runtime/installed/native/live
acceptance and publication receipts remain future work. The local handoff
preserves proposal identities and original failure logs outside public tracking.

## Continuation receipts: 2026-10-05 to 2026-10-06

This continuation worked on a Linux x86_64 replica of the handoff tree with
CPython 3.14.6 (and 3.12.13 where stated). Every count below is a local,
scoped receipt for the stated source; none is hosted CI, an installed-wheel
cell, a three-runtime matrix or publication evidence. Original failure logs
from earlier sessions remain retained outside public tracking.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

Closed locally (rows removed from `TO-DO.md`):

- `P4-BASELINE-CUSTODY-1`: the handoff branch, index, untracked public files,
  remote main and pending proposals were inventoried before any change; the
  handoff state is preserved as its own baseline commit, separate from this
  continuation's changes.
- `P4-REPORTING-OPTIONAL-IMPORT-1`: both optional-plotting controls pass with a
  genuine no-site fixture built from the installed PyYAML and Pillow files;
  the cache cohort passed 52 cases and the methods/outcomes/guardian cohorts
  passed 71, 66 and 76 cases.
- `P4-SEARCH-OFFLINE-TESTS-1`: the reviewed offline-enrichment proposal applied
  at its recorded hashes; the whole Search suite passed 447 cases with 91.95%
  own branch coverage on 3.12, and its Stage 01 cell passed on 3.14.
- `P4-AUTO-IMPORT-CPU-1`: the whole Autopoiesis suite passed 574 cases with
  92% own branch coverage, and its Stage 01 cell passed on 3.14.
- `P4-ROOT-NO-ACQUISITION-1`: the pin is applied last in producer and reader
  environments, Root prerequisite inventories may no longer declare the pinned
  key, and the Root no-acquisition, lane, guardian-environment, report
  finalization and verifier cohort passed 114 cases. An independent review
  found the pin could satisfy a declared prerequisite; admission now refuses it.
<!-- noqa: drift-counts -- dated scoped receipts: 2026-10-05 -->

Ordinary CI partition: escaped parametrization IDs had made every shard report
"no tests ran"; admission now accepts them while still refusing backslash and
NUL module paths. A serial shard-0 replay on an intermediate source recorded
3,255 passes, 29 failures and 6 errors; each failure was triaged to a stale
test contract, a container-only process/permission artifact or a timing
parameter, and the orchestration cohort then passed 561 of 563 cases before its
two remaining timing/zombie controls were repaired and passed alone. A complete
four-shard replay and coverage union on the final candidate was not executed in
this continuation and remains `P4-CI-PARTITION-ACCEPTANCE-1` work.
<!-- noqa: drift-counts -- dated scoped and failed receipts: 2026-10-05 -->

Exemplar Stage 01 cells passed on Python 3.14 for Code, Data Descriptor, Experiment
Tree, Gold Refinement, Madlib, Methods Paper, Newspaper, Pitch Deck, Pools/Rules/
Tools, Prose, Redacted Report, Registered Report, Search, Storybook, Textbook,
Autopoiesis, EDA Notebook, Meta, Template and AutoScientists. AutoResearch
passed 392 cases with 96.33% after its hydration requirement and alias-free
`pythonpath` repairs; before them, its run ended in an executed-code custody
refusal because pytest imported the platform through a `../../..` alias. Advanced passed
158 cases with 94.30% under the audited launcher only after its genuine Meta
wheel was installed and pinned providers became audit roots. SIA needs Docker
(79.15% without it). Formal and Active Inference execute real Lean controls
(Formal also TLC) that this host could not provision because its proxy refused
the toolchain download; Formal measured 87.80% with them deselected, and Active
Inference's verifier, after its top-level `conftest.py` stopped being
assertion-rewritten under the audit, passed every chunk before stopping at its
two Lean controls. The test-project job now
provisions the pinned toolchains (`P4-FORMAL-EXTERNAL-LANE-1`). Active Inference's tracked policy
comparison was produced by an expected-utility fallback that the current locked
pymdp no longer takes, so its replay control fails until the outputs are
regenerated in the locked environment (`P4-ACTIVE-OUTPUT-REFRESH-1`).
<!-- noqa: drift-counts -- dated scoped and failed receipts: 2026-10-05 -->

Own-environment coverage measurement (`counts.py --verify-coverage`) measured
22 of 25 exemplars in their prepared locked `.venv`s; 17 values drifted from the
recorded snapshot. Active Inference, Formal and SIA did not complete, so the
snapshot, `COUNTS.md` and coverage provenance were deliberately not rewritten;
the stale counts still fail `counts.py --check` and two documentation
consistency tests. The handoff state already carried these stale counts.
<!-- noqa: drift-counts -- dated scoped and failed receipts: 2026-10-06 -->

No commit, push, pull request, tag, release, sandbox transfer or publication
occurred in this continuation; the candidate is delivered for review as a
baseline commit plus a continuation commit on `codex/platform-4`.
