# Functional CI and optional hardening

The public template should be easy to install and use. Default CI checks that
contract on Linux/Python 3.14, without starting Docker, Lean, a browser, or a
native document acceptance matrix.

On main and manual runs, every public template builds a wheel and runs the real behavioral tests listed
in `.github/project-smoke.json`, in a separate pytest process. Most tests use a disposable project copy; tests
whose fixtures require genuine monorepo source/DATA run from their canonical
project and use their existing disposable fixtures. The selection
must cover the complete public roster and contain existing project-local tests.
Project-only pull requests select changed projects and their declared transitive
consumers. Shared or unknown paths, renames, deletions and ambiguous changes
select every public project. An unreadable Git change roster fails selection.

Infrastructure preserves the complete baseline smoke union, adds changed tests and
declared Source owners, and splits the selection into complementary file
shards with at most twelve modules in automatic mode. Selected process-heavy
modules retain dedicated jobs. At most sixteen routine cells run concurrently;
the separate contract matrix retains its eight-cell concurrency limit. More
cells increase the aggregate compute allowance. Measured seconds determine both
job count and placement, targeting 240 seconds per routine job within a 64-job
planning preference. Broad rosters expand beyond that preference when needed
to retain the twelve-module cap; hosted concurrency remains sixteen jobs. Without any applicable measurement, file capacity determines job count
and byte sizes only balance placement. Neither estimate proves a cell will fit its deadline. Explicit one-to-eight shard
requests retain their existing manual packing behavior.
Smoke keeps its 540-second child budget and ten-minute job limit;
contract jobs use the existing full-infrastructure 120-second per-test default,
retain explicit test-owned timeout markers, and have a separate 6600-second
whole-module ceiling below the existing Root acceptance budget. The explicit
pytest option applies to this test process; nested producer environments retain
their original timeout settings. Both lanes emit
nonce-bound original pytest selection/outcome receipts and JUnit diagnostics.
The shared bounded subprocess boundary includes startup in the original
deadline and cleans up owned process groups and detached descendants. A separate
request-bound process diagnostic preserves raw OS/effective exits, timeout and
custody status even when pytest cannot finish its receipts; it never grants
acceptance. The wheel typing contract uses the existing full-submodule checkout
to exercise actual authored native content in wheel and source distributions.
The final gate checks the exact combined union and rejects missing, duplicated
or overlapping members. Neither lane replaces complete release acceptance.

Lint/type checks,
Bandit, secret scanning and the public tracking boundary remain blocking. The
`CI Gate` requires every selected functional job to succeed. Guide-only pull
requests enumerate actual documentation test modules, retaining prepared
full-module jobs for the heavy documentation contracts, and skip only the
exemplar matrix. Main and manual events retain the full selection. Runtime
prompts, manuscripts, dependency text files and rendering artwork do not qualify
for this reduction. The aggregate accepts only that declared exemplar skip and
the unrequested coverage skip; missing, cancelled or failed required jobs fail.
Contract modules execute serially inside independent jobs so original collection
and outcome receipts remain verifiable; the contract matrix supplies concurrency.

The environment cache includes the resolved Python version, OS, architecture,
dependency group and root lock/package/Python-selector inputs. Every caller
still runs its declared locked reconciliation. Reused downloads or environments
are preparation inputs, never accepted runtime results.

Hardening retains four infrastructure shards for Linux on both supported Python
minors and macOS on Python 3.15. Linux uses `ubuntu-24.04`, matching the pinned
Noble APT admission rather than admitting a new runner distribution implicitly.
Original pytest worker identity comes from actual `Config.workerinput`; an
inherited `PYTEST_XDIST_WORKER` does not turn a fresh serial controller into a
worker. The Active project cells and public-matrix interpreter include the
existing `active-inference` group; default SDK installation is unchanged.

Linux hardening infrastructure and its separate slow lane run under the existing
[fresh execution-account profile](../../.github/actions/setup-ci-execution-user/README.md).
Prepare tools, browser binaries and the copied Active environment before
handoff. Invoke the selected `.venv/bin/python` directly and explicitly nominate
it for nested `uv` consumers; the account's credential-filter allowlist is not
expanded. Locked native exports likewise select their actual installed
interpreter rather than inheriting `.python-version`.

Infrastructure scheduling uses `load --maxschedchunk=1`. Ordinary modules retain
their stable file assignment. The complete parameter inventories in
`test_native_pdfium_runtime_guard.py`, `test_native_pdfium_verify_current.py` and
`test_native_source_wheel_guard.py` are distributed round-robin over the same four
shards, in canonical collected order. Every control retains its independent
Source, wheel, installation and fresh audit; no mutable authority or result is
shared to save time. Extra worker-local fixture setup trades bounded duplication
for balanced execution. Worker crashes must return their genuine failed exit
without artificial controller interruption. Worker counts, marker selections,
job and per-test clocks, explicit test-owned timeout markers and the 60% complete
coverage union remain unchanged.

Export Linux coverage under the same execution account, then always transport
the original readiness bytes before artifact upload. The runner uploads from
`TEMPLATE_CI_ARTIFACT_DIRECTORY`; macOS retains its original `output/readiness`
paths. Partial diagnostics never establish complete selection or coverage.
Keep evidence-class mutation fixtures separate from the loaded SDK and require
their initialized pinned Source closure instead of accepting skipped controls.

Infrastructure smoke prepares genuine Poppler tools for raster controls. Its
selected compiler controls also install the recommended TeX fonts and verify
`pzdr.tfm`, which XeTeX hyperlink support requires. The auxiliary contract
additionally prepares the declared Pandoc/XeTeX document producers and readers.
Native portability and Auto prepare fresh caches with Source-locked build tools
in a backend-only environment. Online runtime preparation uses those tools
without build isolation or dependency resolution and installs into a separate
target, allowing exact locked sdists to build without polluting the backend.
Both preparation and native consumption nominate archives for the actual
selected interpreter's minor. Fresh consumers still require offline,
no-build and exact-hash installation; neither `uv sync` state nor a restored
environment proves those archives remain available to that consumer.

Run a project's same selection locally after locked root setup:

```bash
uv sync --locked --group installed-build
uv run python scripts/gates/ci_smoke.py --project templates/template_code_project
```

Advanced Literature Review also needs its declared Meta provider installed;
CI builds that provider wheel before its behavioral tests. Search Project's
bibliography test also performs a real Pandoc conversion; only that job uses the
existing pinned converter-only preparation, without native document prerequisites.
A project wheel
build is packaging evidence; these source-tree tests do not certify installation
outside the checkout, publication, native rendering, or scientific validity.

## Push-time checks and measurement provenance

As of 2026-10-13, normal pre-push checks retain security, public tracking,
no-mocks, behavioral smoke and documentation contracts. `COUNTS.md`
synchronization and dated coverage provenance checks run explicitly through
the `counts` health gate and the full-hardening documentation job, rather than
on every push. This permits
publishing a verification branch when a required local tool is unavailable.

Run the strict snapshot check with:

```bash
uv run python scripts/docgen/counts.py --check
```

Stale provenance remains a failure in those owning checks. Manually dispatch
**Public exemplar coverage** to measure the complete Source-derived public roster
in one run, with at most four projects executing concurrently. An optional exact
qualified `coverage-project` limits an investigative run to one public exemplar.
The reusable coverage job preserves each project's tools, locked profile, full
suite, coverage floor and original timeout. It checks the checkout commit before
and after measurement and uploads a separate artifact per project. The final
matrix gate requires every selected project to pass.

CI's existing optional `coverage-project` input calls the same reusable job.
For either route, retrieve the original measurement artifact and verify its
source commit, project input hash and complete passing measurement before
updating the snapshot and provenance together. Until then, retain the dated
measurement and report the outstanding verification. Release's exact-source
acceptance and coverage custody still apply independently.

## Further hardening

`platform-native-preflight.yml` runs for relevant native/dependency pull-request
changes and manual dispatch. After tool preparation, its cold installed operation
has at most 1800 seconds on one original clock, reserving a 30-second launch tail
and a 15-second supervised-worker tail so the inner owner returns and retains its
worker process, cleanup and guardian receipts before the outer watcher ends. It
prepares Code and its actual
Source-declared local providers, then runs that exemplar through the production
Original and independent Current route, including all enabled formats. The route
owns its fresh provider and reader admissions; the diagnostic does not repeat an
all-project preparation prelude. Its tool setup omits the unrelated Lean compiler.
The record explicitly declares incomplete release selection and cannot authorize
a tag or publication. Complete original, reader and handoff roles keep the full
public provider roster and the required acceptance clocks. This narrower scope
does not itself establish that the native diagnostic will fit its deadline.

Native core stages explicitly use the nominated cold interpreter, and terminal
readback requires the exact selected environment commitment. Stage launch
deadlines stay within the original clock. An unsuccessful Original stops further
original launches after its process and raw evidence are retained; the missing
remainder keeps the complete release selection failing. Fixed public phase,
PID and remaining-time diagnostics locate delays without authorizing acceptance.

The full required-acceptance workflow derives one Linux auxiliary cell for
each complete public project plus separate Root checks, with four concurrent
jobs and one serial 1,800-second operation per cell. This changes aggregate
scheduling and compute allowance from the former global operation; earlier
failures remain failures. Same-run live collection authenticates every unique
producer attempt and complete original graph. Darwin print, the six Root
host/runtime artifacts, common installed/runtime and full native-format
originals retain their separate owners. Installed cells use three bounded
dependency-aware workers. The independent installed candidate and fresh release
readers still require the complete Source-owned profile, all host/runtime
obligations, coverage floors and original case limits.

Use the manual **Optional Hardening** workflow for the former complete
infrastructure shards, Python 3.14/3.15 project suites, aggregate coverage,
platform breadth and extended documentation checks. Use the separate manual
**Platform required acceptance** workflow when original source/runtime custody,
native document replay or formal release acceptance is needed. Neither runs
on an ordinary main push. Existing full-suite coverage floors and release
custody requirements remain in those lanes.

Each project's README suggests its next hardening step. Focused CI passing
means the named functional selection passed. It does not close the recorded
exhaustive acceptance or historical measurement gaps. Coverage snapshots are
dated evidence and must be remeasured before promoting them to a current
full-suite claim. An explicit hardening run may still expose those gaps.
