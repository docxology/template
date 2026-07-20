# Local CI Reproduction — defense against free-tier compression

> Created 2026-05-20. Addresses World-Threat-Model RedTeam attack A8 (GitHub Actions CI matrix economic decay).

## Why this guide exists

The repo's infrastructure CI matrix (Ubuntu × Python 3.10–3.13 plus a macOS 3.12 smoke) runs on GitHub Actions free-tier minutes. macOS minutes cost 10× Linux. GitHub's free-tier policy has tightened twice since 2020. On a multi-decade horizon, **the inability to reproduce CI locally is a vendor-lock-in risk** — if the free tier compresses, the project either pays or moves CI providers.

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
# Run the full default workflow (everything on push to main)
./scripts/shell/ci_local.sh

# Run a specific job (job IDs match .github/workflows/ci.yml)
./scripts/shell/ci_local.sh -j lint
./scripts/shell/ci_local.sh -j test-infra
./scripts/shell/ci_local.sh -j test-project
./scripts/shell/ci_local.sh -j security

# Run every canonical public exemplar in isolated subprocesses
./scripts/shell/ci_local.sh --no-act -j public-readiness

# Dry-run (show what would execute without running)
./scripts/shell/ci_local.sh --dryrun

# List all available jobs
./scripts/shell/ci_local.sh --list
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
| `test-infra` (matrix: ubuntu py3.10/3.11/3.12/3.13 + macos py3.12) | ✅ Yes (ubuntu legs) | Set `--matrix python-version:3.X`; coverage gate runs inside this job |
| `test-project` (matrix: per-project × py3.10/3.12) | ✅ Yes | Per-project 90% coverage runs inside this job; macOS not exercised here |
| `security` (bandit + pip-audit) | ✅ Yes | Fully Linux-portable |
| `docs-lint` | ✅ Yes | Markdown lint, doc-tree integrity |
| `validate` (manuscript validation) | ✅ Yes | Pure Python |
| `performance` (import benchmarks) | ✅ Yes | Runs in container |
| `detect` / `detect-projects` (optional-project + public-exemplar discovery) | ✅ Yes | Fully Linux-portable; gates `fep-lean` and the Windows smoke job below |
| `actionlint` | ✅ Yes | Lints the workflow YAML itself |
| `health` (blocking static-health report) | ✅ Yes | Runs `infrastructure.core.health`; needs `lint` and the shared Mermaid/Chrome setup action |
| `verify-no-mocks` | ✅ Yes | Fully Linux-portable; needs `lint` |
| `test-regression` (claim-binding pins) | ✅ Yes | Fully Linux-portable; needs `verify-no-mocks` |
| `fep-lean` (gauss + lake, conditional) | ✅ Yes | Linux-only, `if: needs.detect.outputs.fep_lean == 'true'`; heavy (60 min timeout) |
| `setup-hook-windows-smoke` | ❌ No | Runs on `windows-latest` — `act` only reproduces Linux containers; treat the real CI run as source of truth (same caveat as the macOS jobs above) |

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

# Run every fallback lane; any missing tool or failed command aborts
./scripts/shell/ci_local.sh --no-act
```

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
missing exemplars. Its project-local uv environments are pinned to Python
3.12, and JSON reports record that baseline. Use
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
uv run python -m infrastructure.validation.cli publication-audit \
  --all-public --strict --rendered --format json
```

The refresh records a `current-output-snapshot`; it does not fabricate
stage-level provenance for the test subprocesses.

## Long-term portability

The workflow YAML at `.github/workflows/ci.yml` is **documentation of intent**, not a vendor binding. If CI providers change:

- **Forgejo Actions** consumes the same YAML format — drop-in replacement
- **GitLab CI** is a YAML rewrite — straightforward porting given the act-tested job decomposition
- **Sovereign-cloud / self-hosted GitHub Actions runners** consume the same YAML
- **Local-only / on-prem**: `act` is the path

The act-tested local reproduction means CI portability is **already proved** at every commit.

## Status

`scripts/shell/ci_local.sh` is created 2026-05-20. The act path is the default;
the direct-command fallback covers a documented, fail-closed subset when
Docker is unavailable.

## Related

- [`README.md`](README.md) — guide hub
- [`scripts/shell/ci_local.sh`](../../scripts/shell/ci_local.sh) — the wrapper
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — the workflow being reproduced
- [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job names + thresholds
