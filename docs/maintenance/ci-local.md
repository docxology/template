## Default functional checks

Default [`ci.yml`](../../.github/workflows/ci.yml) uses Linux/Python 3.14 for public
lint/type/data/security checks, pipeline smoke, and focused behavioral tests plus
wheel builds for every public template. Its required `CI Gate` demands success
from all functional jobs. No full-suite coverage or native acceptance is implied.
The complete matrix described below belongs to manual optional hardening;
coverage union, dependency vulnerability auditing and semantic replacement
inventory are requirements of that lane. Native/formal release acceptance also
remains a separate manual lane. See [CI scope and local commands](../development/ci.md).

# Local CI and release checks

Use the commands below to choose a development check, reproduce CI, or complete
release acceptance. Each route states what it verifies and what must follow.

## Choose a route

This is the local command map for the existing entry points. Run commands from
repository root after preparing the locked environment and the prerequisites
below. Public projects and lint/type paths come from `public_scope`; the full
static registry remains owned by `infrastructure.core.health`.

| Intent | Existing entry point | Result |
| --- | --- | --- |
| Inspect supported direct local lanes | `./scripts/shell/ci_local.sh --no-act --list` | Shows available fallback lanes without running them. |
| Inspect the public roster | `uv run --no-sync --offline python -m infrastructure.project.public_scope project-names` | Reads the canonical public roster; no copied project list. |
| Inspect CI lint/type scope | `uv run --no-sync --offline python -m infrastructure.project.public_scope ci-paths` | Emits the existing `lint_paths` and `source_paths` together. |
| Focused development example | `uv run --no-sync --offline pytest tests/infra_tests/project/test_public_scope.py` | Runs the owning subsystem tests; choose the test path for the subsystem changed. |
| Full repository static diagnosis | `uv run --no-sync --offline python -m infrastructure.core.health --json` | Runs the complete existing health registry, including no-mocks. |
| Deterministic public project tests | `uv run --no-sync --offline python scripts/gates/public_readiness.py --json` | Uses the canonical public roster and records each isolated test result. |
| Exact-revision release acceptance | Follow [Platform 4 required acceptance](platform-4-upgrade.md) and [root required acceptance](root-required-acceptance.md). | The dedicated workflow collects every required original lane and its independent readback. |
| Inspect retained acceptance or publish | Follow [release boundary](release-boundary.md). | Status inspection, acceptance, publication and retrieved-asset verification retain separate outcomes. |

For **ordinary development**, start with the owning tests or a supported local
lane; `--no-act --dry-run` shows the fallback plan. Focused results provide
feedback. They do not replace complete coverage, health, no-mocks, core,
native or source-custody requirements. The remaining sections explain how to
reproduce declared workflow jobs and the fallback's limits.

For **release acceptance**, finish implementation, documentation, version
metadata and generated outputs before freezing the exact source revision.
Use the existing required-acceptance workflow and release handoff. Root 4+
publication reuses the handoff's authenticated installed matrix after a fresh
installed current reader validates it; the source/wheel/runtime bindings and
all original cells remain required. Publication and retrieved-asset checks still
run separately. A local dashboard or focused pass cannot authorize publication.

## Why this guide exists

Default functional CI uses Linux and Python 3.14. Manual Optional Hardening
retains the complete Ubuntu × Python 3.14/3.15 and macOS × Python 3.15
infrastructure matrix. Local reproduction helps diagnose these jobs and reduces
dependence on hosted runner availability and pricing.

This guide documents the **`act`-based local reproduction path**, which decouples the workflow YAML (the documentation of intent) from the GitHub Actions runtime (the current implementation).

## What this provides

- Run any GitHub Actions job locally without pushing
- Validate workflow changes without burning CI minutes
- Portability hedge: if CI moves to Forgejo, GitLab, sovereign-cloud, etc., the YAML is the documentation of intent and `act` is the runtime-independent verifier

## Prerequisites

```bash
# Python and all deterministic public-exemplar dependencies
uv sync

# Pinned Mermaid CLI used by strict documentation and PDF checks
npm ci
# Python gates auto-discover node_modules/.bin/mmdc; add it to PATH only for
# direct mmdc invocations:
export PATH="$PWD/node_modules/.bin:$PATH"

# macOS / Linux
brew install act           # or: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Docker must be running (act uses container images to mimic GH runner environments)
docker info >/dev/null     # should succeed
```

## Running CI locally

```bash
# Run default functional CI (the push workflow)
./scripts/shell/ci_local.sh

# Run a default functional job
./scripts/shell/ci_local.sh -j lint

# Select the manual exhaustive workflow explicitly when using act
act workflow_dispatch -W .github/workflows/hardening.yml -j test-infra
act workflow_dispatch -W .github/workflows/hardening.yml -j test-project
act workflow_dispatch -W .github/workflows/hardening.yml -j security

# Run every canonical public exemplar in isolated subprocesses
./scripts/shell/ci_local.sh --no-act -j public-readiness

# Dry-run (show what would execute without running)
./scripts/shell/ci_local.sh --dryrun

# List default push jobs (or direct fallback lanes when act is unavailable)
./scripts/shell/ci_local.sh --list

# List jobs in manual Optional Hardening
act workflow_dispatch -W .github/workflows/hardening.yml --list
```

See [`scripts/shell/ci_local.sh`](../../scripts/shell/ci_local.sh) for the wrapper details.

## What about macOS jobs?

`act` runs Linux containers; macOS-specific jobs can't be fully reproduced locally on Linux. The workaround:

1. On macOS, `act` still runs Linux containers (since macOS containers aren't generally available). The macOS-specific job behavior must be tested by:
   - Running the actual commands directly in your macOS shell (most CI steps are not actually macOS-specific)
   - Treating "the macOS job passes in real GH Actions CI" as the source of truth
2. The Linux-only path (which is the realistic long-term default if free-tier compresses) is fully reproducible via `act`

## Configuration

User-owned `act` configuration may live in `.actrc` at repo root. When it is
absent, `ci_local.sh` passes these runner mappings directly and does not mutate
the checkout:

```
# Use the medium-sized Linux runner image (closer to GH Actions ubuntu-latest)
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04

# Secrets file (optional; act reads .secrets if present)
# DO NOT commit a real .secrets — gitignore it
```

Add `.secrets` to `.gitignore` if you need to test secret-dependent jobs locally.

## Coverage of jobs

| CI job | Reproducible via act? | Notes |
| --- | --- | --- |
| `lint` (ruff + mypy; also runs the four-pool `check_tracked_all.py` confidentiality guard) | ✅ Yes | Fully Linux-portable |
| `test-infra` (matrix: ubuntu py3.14/3.15 + macos py3.15) | ✅ Yes (ubuntu legs) | Four complete shards per environment; set `--matrix python-version:3.X`. Linux 3.14 shards retain coverage data; `coverage-infra` owns the complete-union threshold |
| `coverage-infra` | Hosted artifact boundary | Merges all four same-revision Linux 3.14 shard selection/data artifacts, validates the complete disjoint case union and enforces ≥60%. Reproduce it using the actual hosted artifacts; the existing unpartitioned local infrastructure command remains available |
| `test-project` (matrix: per-project × py3.14/3.15) | ✅ Yes | Per-project 90% coverage runs inside this job; macOS not exercised here |
| `security` (bandit + pip-audit) | ✅ Yes | Fully Linux-portable |
| `docs-lint` | ✅ Yes | Markdown lint, doc-tree integrity |
| `validate` (manuscript validation) | ✅ Yes | Pure Python |
| `performance` (import benchmarks) | ✅ Yes | Runs in container |
| `detect` / `detect-projects` (optional-project + public-exemplar discovery) | ✅ Yes | Fully Linux-portable; gates `fep-lean` and the Windows smoke job below |
| `actionlint` | ✅ Yes | Lints the workflow YAML itself |
| `health` (blocking static-health report) | ✅ Yes | Runs `infrastructure.core.health` independently of `lint`, with the shared Mermaid/Chrome setup action |
| `verify-no-mocks` | ✅ Yes | Fully Linux-portable; runs independently of `lint` and gates the test jobs |
| `test-regression` (claim-binding pins) | ✅ Yes | Fully Linux-portable; needs `verify-no-mocks` |
| `test-integration` (run.sh + secure_run.sh + pipeline CLI) | ✅ Yes | Fully Linux-portable; needs `verify-no-mocks`; mirrors `test-regression` (CI-WIRING-1) |
| `fep-lean` (gauss + lake, conditional) | ✅ Yes | Linux-only, `if: needs.detect.outputs.fep_lean == 'true'`; heavy (60 min timeout) |
| `setup-hook-windows-smoke` | ❌ No | Runs on `windows-latest` — `act` only reproduces Linux containers; treat the real CI run as source of truth (same caveat as the macOS jobs above) |
| `test-infra-slow` (`pytest.mark.slow` lane, manual Optional Hardening only) | ✅ Yes | `uv run pytest tests/infra_tests/ -m slow` locally; heavy real-render suite (pandoc + TeX Live), no coverage upload |

## Fallback: fail-closed direct commands

If `act` is unavailable, `ci_local.sh` runs a declared subset of direct CI
commands. The fallback is not presented as full workflow reproduction:
platform matrices, service containers, and dependency auditing still require
`act` or GitHub Actions. Unsupported `--job` values exit nonzero instead of
reporting a vacuous success.

```bash
# Inspect the exact fallback lanes without executing them
./scripts/shell/ci_local.sh --no-act --list
./scripts/shell/ci_local.sh --no-act --dry-run

# Run one supported lane
./scripts/shell/ci_local.sh --no-act --job lint
./scripts/shell/ci_local.sh --no-act --job health
./scripts/shell/ci_local.sh --no-act --job verify-no-mocks

# Run the complete direct subset; any missing tool or failed command aborts
./scripts/shell/ci_local.sh --no-act
```

The default direct subset runs **health → tests → precommit → public-readiness**.
The complete health registry already runs lint/type/format, Bandit MEDIUM+, both
no-mocks policies, exports, operations, generated-artifact, confidentiality and
module-size checks. The retained pre-push hook also checks mirror shape. The
standalone `lint`, `verify-no-mocks`, `security` and `confid` lanes remain
available through `--job`; the default avoids their repeated scans. Test
profiles, coverage requirements, hook stages and named-lane commands are
unchanged. This local subset still does not replace hosted matrices, dependency
auditing or required release acceptance.

The `tests` lane runs the full infrastructure scope and the selected project's
`quick` profile; `TEMPLATE_CI_PROJECT` can select a different project. The later
public-readiness lane runs every public exemplar with the `release` profile,
which includes slow tests. These selections have separate coverage checks.
Hooks may fix files between them, so the earlier result does not certify the
later source snapshot. Use the named `tests` lane for quick feedback and the
existing public-readiness lane for the complete deterministic public roster.

The health lane overlaps independent subprocess gates with a bounded default
worker pool. For a reproducible serial diagnostic run, use the underlying
command directly with `--workers 1`; its machine-readable report includes both
aggregate gate time and whole-sweep wall time.

To close a health-latency change, run the owning benchmark command from a clean
checkout. It executes both modes itself and writes the fail-closed manifest:

```bash
uv run python scripts/maintenance/benchmark_health.py \
  --parallel-workers 4 \
  --output /tmp/health-benchmark.json
```

Each owned health result records its worker count, commit, clean-tree state,
report digest, and a SHA-256 digest of the exact gate argv/threshold registry.
Caller-supplied reports cannot produce acceptance. The manifest passes only
when both executions match the current clean checkout and gate digest, both
modes run and pass the complete canonical registry in the same order, and
parallel wall time improves by at least 25%.

The pre-commit lane uses `uv run pre-commit`; it never silently skips a missing
global executable. Confidentiality uses the full four-pool
`scripts/audit/check_tracked_all.py` guard.

The `public-readiness` lane is the deterministic local matrix for all entries
in `infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES`. It invokes one
pytest process per exemplar, emits PASS/FAIL/SKIP records, and fails closed on
missing exemplars. It launches Stage 01 with its current interpreter and passes
that path as `UV_PYTHON`; Stage 01 independently admits each project's existing
runtime. JSON reports record the launcher interpreter and profile. Supported
Python matrices remain part of the dedicated acceptance routes. Use
`uv run python scripts/gates/public_readiness.py --json` when another tool
needs the report. Ollama tests are a separate opt-in lane:

```bash
uv run python scripts/gates/public_readiness.py \
  --include-ollama-tests --allow-skips --json
```

The matrix deliberately regenerates each exemplar's tracked test-result report.
Before a strict rendered publication audit, rebaseline those intentional output
changes and then audit again:

```bash
uv run python scripts/maintenance/refresh_artifact_manifests.py --all-public
uv run python scripts/maintenance/refresh_rendered_provenance.py --all-public
uv run python -m infrastructure.validation.cli publication-audit \
  --all-public --strict --rendered --format json
```

The manifest refresh records a `current-output-snapshot`; it does not fabricate
stage-level provenance for the test subprocesses. The rendered-provenance
refresh then re-renders, snapshots, validates, and binds that exact integrity
snapshot to the current stage implementation, source, configuration, outputs,
and manuscript-consumption evidence. Stage or commit the complete refreshed
evidence set before the strict audit, because receipt validation requires the
release paths to match Git's cached index.

## Long-term portability

The workflow YAML at `.github/workflows/hardening.yml` records current jobs and
dependencies. A future provider migration depends on the destination's
support for runners, actions, permissions and services.

`act` exercises supported Linux jobs locally; macOS/Windows jobs and hosted
acceptance retain their declared runs. Local reproduction claims apply to
the jobs and source revision actually exercised.

## Status

`scripts/shell/ci_local.sh` is created 2026-05-20. The act path is the default;
the direct-command fallback covers a documented, fail-closed subset when
Docker is unavailable.

## Related

- [`README.md`](README.md) — guide hub
- [`scripts/shell/ci_local.sh`](../../scripts/shell/ci_local.sh) — the wrapper
- [`.github/workflows/hardening.yml`](../../.github/workflows/hardening.yml) — the workflow being reproduced
- [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job names + thresholds
