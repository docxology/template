# Local CI Reproduction — defense against free-tier compression

> Created 2026-05-20. Addresses World-Threat-Model RedTeam attack A8 (GitHub Actions CI matrix economic decay).

## Why this guide exists

The repo's CI matrix (Ubuntu/macOS × Python 3.10–3.12) runs on GitHub Actions free-tier minutes. macOS minutes cost 10× Linux. GitHub's free-tier policy has tightened twice since 2020. On a multi-decade horizon, **the inability to reproduce CI locally is a vendor-lock-in risk** — if the free tier compresses, the project either pays or moves CI providers.

This guide documents the **`act`-based local reproduction path**, which decouples the workflow YAML (the documentation of intent) from the GitHub Actions runtime (the current implementation).

## What this provides

- Run any GitHub Actions job locally without pushing
- Validate workflow changes without burning CI minutes
- Portability hedge: if CI moves to Forgejo, GitLab, sovereign-cloud, etc., the YAML is the documentation of intent and `act` is the runtime-independent verifier

## Prerequisites

```bash
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

`act` configuration lives in `.actrc` at repo root (created if missing by `ci_local.sh`):

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
| `lint` (ruff + mypy; also runs `check_tracked_projects.py` confidentiality guard) | ✅ Yes | Fully Linux-portable |
| `test-infra` (matrix: ubuntu py3.10/3.11/3.12 + macos py3.12) | ✅ Yes (ubuntu legs) | Set `--matrix python-version:3.X`; coverage gate runs inside this job |
| `test-project` (matrix: per-project × py3.10/3.12) | ✅ Yes | Per-project 90% coverage runs inside this job; macOS not exercised here |
| `security` (bandit + pip-audit) | ✅ Yes | Fully Linux-portable |
| `docs-lint` | ✅ Yes | Markdown lint, doc-tree integrity |
| `validate` (manuscript validation) | ✅ Yes | Pure Python |
| `performance` (import benchmarks) | ✅ Yes | Runs in container |
| `detect` / `detect-projects` (optional-project + public-exemplar discovery) | ✅ Yes | Fully Linux-portable; gates `fep-lean` and the Windows smoke job below |
| `actionlint` | ✅ Yes | Lints the workflow YAML itself |
| `health` (unified health report, informational) | ✅ Yes | Runs `infrastructure.core.health`; needs `lint` |
| `verify-no-mocks` | ✅ Yes | Fully Linux-portable; needs `lint` |
| `test-regression` (claim-binding pins) | ✅ Yes | Fully Linux-portable; needs `verify-no-mocks` |
| `fep-lean` (gauss + lake, conditional) | ✅ Yes | Linux-only, `if: needs.detect.outputs.fep_lean == 'true'`; heavy (60 min timeout) |
| `setup-hook-windows-smoke` | ❌ No | Runs on `windows-latest` — `act` only reproduces Linux containers; treat the real CI run as source of truth (same caveat as the macOS jobs above) |

## Fallback: pure-Python reproduction

If `act` is not available (Docker unavailable, etc.), the major CI checks can be reproduced via the equivalents documented in `CLAUDE.md`:

```bash
# Lint (CI mirror)
uv run python -m infrastructure.project.public_scope lint-paths | xargs uvx ruff check --fix
uv run python -m infrastructure.project.public_scope lint-paths | xargs uvx ruff format
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy

# Security
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/

# Tests
uv run python scripts/pipeline/stage_01_test.py --project template_code_project

# Pre-commit (all stages)
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files

# Confidentiality check
uv run python scripts/audit/check_tracked_projects.py
```

This is what `ci_local.sh` falls back to if `act` isn't present.

## Long-term portability

The workflow YAML at `.github/workflows/ci.yml` is **documentation of intent**, not a vendor binding. If CI providers change:

- **Forgejo Actions** consumes the same YAML format — drop-in replacement
- **GitLab CI** is a YAML rewrite — straightforward porting given the act-tested job decomposition
- **Sovereign-cloud / self-hosted GitHub Actions runners** consume the same YAML
- **Local-only / on-prem**: `act` is the path

The act-tested local reproduction means CI portability is **already proved** at every commit.

## Status

`scripts/shell/ci_local.sh` is created 2026-05-20. The act path is the default; pure-Python fallback covers the case where Docker is unavailable.

## Related

- [`README.md`](README.md) — guide hub
- [`scripts/shell/ci_local.sh`](../../scripts/shell/ci_local.sh) — the wrapper
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — the workflow being reproduced
- [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job names + thresholds
