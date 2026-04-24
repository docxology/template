# CI/CD Workflows

## Overview

The `workflows/` directory contains GitHub Actions workflows that automate the continuous integration and delivery pipeline for the Research Project Template. These workflows ensure code quality, test reliability, and compatibility across environments.

## Directory Structure

```
.github/workflows/
├── AGENTS.md       # This technical documentation
├── README.md       # Quick reference
├── ci.yml          # Main CI/CD pipeline (8 jobs)
├── stale.yml       # Auto-label and close stale issues/PRs
└── release.yml     # Create GitHub Releases on version tags
```

## CI Pipeline (`ci.yml`)

### Triggers

| Trigger | Condition |
|---|---|
| `push` | Commits to `main` |
| `pull_request` | PRs targeting `main` |
| `schedule` | Weekly Sunday midnight UTC (CVE catch-up) |
| `workflow_dispatch` | Manual trigger with optional `project` input |

**Concurrency:** `cancel-in-progress: true` — stale runs are cancelled automatically when a new commit is pushed.

**Global env:** `UV_FROZEN=true`, `MPLBACKEND=Agg` (non-interactive matplotlib backend).

### Job Graph

`validate` and `security` depend on **`lint` only** (they run in parallel with the `verify-no-mocks` subtree). `test-infra`, `test-project`, and `fep-lean` depend on **`verify-no-mocks`**.

```
lint
 ├── verify-no-mocks
 │    ├── test-infra   (matrix: ubuntu+macos × 3.10/3.11/3.12) → codecov on 3.12/ubuntu only
 │    ├── test-project (same matrix; ignores projects/fep_lean/tests/)
 │    └── fep-lean     (ubuntu-only; skipped if no lean-toolchain)
 ├── validate        (needs: lint)
 └── security          (needs: lint)

test-infra + test-project → performance
```

### Job Details

#### 1. Lint & Type Check (`lint`)

- **Runner:** `ubuntu-latest` / Python 3.12
- **Tools:** `uvx ruff check`, `uvx ruff format --check`, `uv run mypy`
- **Scope:** `infrastructure/` and `projects/*/src/`

#### 2. Verify No Mocks Policy (`verify-no-mocks`)

- **Runner:** `ubuntu-latest` / Python 3.12
- **Script:** [`scripts/verify_no_mocks.py`](../../scripts/verify_no_mocks.py) (repository root)
- **Policy:** Absolutely no `MagicMock`, `mocker.patch`, `unittest.mock` in test files

#### 3. Infrastructure Tests (`test-infra`)

- **Matrix:** `ubuntu-latest`, `macos-latest` × `3.10`, `3.11`, `3.12` (6 combinations)
- **Coverage threshold:** 60% (`--cov-fail-under=60`)
- **Coverage file:** `.coverage.infra` (isolated from project coverage)
- **Exclusions:** Tests marked `requires_ollama` are skipped (`-m "not requires_ollama"`)
- **Codecov upload:** On Python 3.12 / ubuntu-latest only to avoid duplicate reports

#### 4. Project Tests (`test-project`)

- **Sync:** `uv sync --group rendering --group monitoring --group discopy` — same packages as a fresh local `uv sync` at the repo root for DisCoPy string-diagram tests: root **`default-groups`** are `dev`, `rendering`, and **`discopy`**, so `uv sync` already installs **DisCoPy**; this job adds **monitoring** (not in `default-groups`). **Hypothesis** comes from the **dev** group (parametric tests), not from `discopy` (see root `pyproject.toml` `[dependency-groups]` and `default-groups`).
- **Matrix:** Same as `test-infra` (6 combinations)
- **Coverage threshold:** 90% (`--cov-fail-under=90`) — enforces the project quality standard
- **Coverage file:** `.coverage.project` (isolated)
- **Scope:** One `pytest` invocation per `projects/*/tests/` directory (first pass collects coverage, later passes use `--cov-append`), then `coverage xml` + `coverage report`. **`projects/fep_lean/tests/` is skipped** in this job so `tests/conftest.py` from `code_project` and `fep_lean` are never loaded in the same process (duplicate plugin name); fep_lean runs in job **`fep-lean`** with real `gauss` / `lake` / `lean`.
- **Codecov upload:** On Python 3.12 / ubuntu-latest only

#### 4b. fep_lean — real Open Gauss + Lake (`fep-lean`)

- **Conditional:** Job is **skipped** unless `projects/fep_lean/lean/lean-toolchain` exists (`hashFiles` guard in `ci.yml`). When fep_lean lives under `projects_in_progress/`, the guard evaluates to empty and the job is skipped. Promote with `mv projects_in_progress/fep_lean projects/fep_lean` to activate.
- **Runner:** `ubuntu-latest` / Python 3.12 only; job `timeout-minutes: 45`
- **Depends on:** `verify-no-mocks`
- **Working directory:** `projects/fep_lean` for pytest; `projects/fep_lean/lean` for Lake warm-up
- **Toolchain:** elan + pinned `lean-toolchain`, `lake build` warm-up
- **Open Gauss:** clone [math-inc/OpenGauss](https://github.com/math-inc/OpenGauss), `./scripts/install.sh --plain --noninteractive --skip-system-packages`, `gauss doctor`
- **Tests:** `uv run pytest tests/ --timeout=1200 --cov=src --cov-fail-under=89` with `COVERAGE_FILE: ../../.coverage.fep_lean`
- **Scaling:** Full catalogue × Lean is expensive; if runtime grows past the job budget, split slow integration tests behind a pytest marker or shard topics in a follow-up workflow.

#### 5. Validate Manuscripts (`validate`)

- **Runner:** `ubuntu-latest` / Python 3.12
- **Steps:**
  1. `infrastructure.validation.cli markdown projects/*/manuscript/` — validates all active project manuscripts
  2. Dynamic project import check — discovers and imports every `projects/*/src` to catch broken imports

#### 6. Security Scan (`security`)

- **Runner:** `ubuntu-latest` / Python 3.12
- **pip-audit:** `continue-on-error: true` (upstream DB can be transiently unavailable)
- **bandit:** `-ll` (MEDIUM+ severity), covers `infrastructure/`, `scripts/`, `projects/`; excludes `projects_archive/` and `projects_in_progress/`

#### 7. Performance Check (`performance`)

- **Runner:** `ubuntu-latest` / Python 3.12
- **Depends on:** `test-infra` + `test-project`
- **Threshold:** Total import time for `infrastructure.core` + all active project `src` modules ≤ 5 seconds
- **Per-module timing** reported to stdout for trend analysis

### Quality Gates

| Gate | Threshold | Enforced by |
|---|---|---|
| Ruff linting | zero violations | `lint` job |
| Ruff formatting | zero diffs | `lint` job |
| mypy type check | no errors | `lint` job |
| No-mocks policy | zero mock usage | `verify-no-mocks` job |
| Infrastructure coverage | ≥ 60% | `test-infra` job |
| Project coverage | ≥ 90% | `test-project` job |
| fep_lean coverage | ≥ 89% | `fep-lean` job (skipped if `projects/fep_lean/lean/lean-toolchain` absent) |
| Bandit MEDIUM+ | zero findings | `security` job |
| Import time | ≤ 5 seconds total | `performance` job |

---

## Stale Workflow (`stale.yml`)

Runs daily at 01:00 UTC using `actions/stale@v9`.

| Item | Stale after | Closed after |
|---|---|---|
| Issues | 60 days inactive | + 14 days |
| Pull Requests | 30 days inactive | + 14 days |

**Exempt labels:** `pinned`, `security`, `in-progress`, `blocked`, `do-not-close`

---

## Release Workflow (`release.yml`)

Triggers on `v*.*.*` tag push or `workflow_dispatch` (with tag input).

1. Generates a commit-based changelog excerpt since the previous tag
2. Creates a GitHub Release using `softprops/action-gh-release@v2`
3. Enables GitHub's built-in PR-based release notes (`generate_release_notes: true`)
4. Auto-marks as pre-release if tag contains `-rc`, `-beta`, or `-alpha`

---

## Local CI Simulation

```bash
# Reproduce lint locally
uv sync
uvx ruff check infrastructure/ projects/*/src/
uvx ruff format --check infrastructure/ projects/*/src/
uv run mypy infrastructure/ projects/*/src/

# Reproduce infrastructure tests locally
COVERAGE_FILE=.coverage.infra uv run pytest tests/infra_tests/ \
  --cov=infrastructure \
  --cov-fail-under=60 \
  -m "not requires_ollama"

# Reproduce project tests locally (matrix job ignores fep_lean). Root `default-groups` include
# `discopy` and `rendering`; CI also installs `monitoring` — use:
#   uv sync --group monitoring
# or full explicit parity: uv sync --group rendering --group monitoring --group discopy
uv sync --group monitoring
COVERAGE_FILE=.coverage.project uv run pytest projects/*/tests/ \
  --ignore=projects/fep_lean/tests/ \
  --cov=projects/code_project/src \
  --cov-fail-under=90 \
  -m "not requires_ollama"

# fep_lean only — requires gauss, lake, lean on PATH (see projects/fep_lean/tests/AGENTS.md)
(cd projects/fep_lean && COVERAGE_FILE=../../.coverage.fep_lean uv run pytest tests/ \
  --timeout=900 \
  --cov=src \
  --cov-fail-under=89 \
  -m "not requires_ollama")

# Reproduce security scan locally
uv run pip-audit
uv run bandit -r -ll infrastructure/ scripts/ projects/ \
  --exclude projects_archive,projects_in_progress
```

---

## Troubleshooting

### Linting failures
```bash
uvx ruff check infrastructure/ projects/*/src/ --fix
uvx ruff format infrastructure/ projects/*/src/
```

### Test failures
```bash
# Infrastructure
uv run pytest tests/infra_tests/ -v --tb=long -s

# Project
uv run pytest projects/*/tests/ -v --tb=long -s

# Single test
uv run pytest tests/infra_tests/test_foo.py::TestClass::test_method -s --pdb
```

### Coverage below threshold
```bash
# Infrastructure report
COVERAGE_FILE=.coverage.infra uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-report=html
open htmlcov/index.html

# Project report
COVERAGE_FILE=.coverage.project uv run pytest projects/*/tests/ \
  --cov=projects/code_project/src --cov-report=html
open htmlcov/index.html
```

### Performance check slow
```bash
# Profile imports
uv run python -c "
import cProfile, pstats, io
pr = cProfile.Profile()
pr.enable()
import infrastructure.core
pr.disable()
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
"
```

---

## See Also

- [`../README.md`](../README.md) — `.github/` human guide (workflows, Dependabot, templates)
- [`../AGENTS.md`](../AGENTS.md) — GitHub integration overview
- [`../../AGENTS.md`](../../AGENTS.md) — Root system overview and pipeline stages
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Codecov Documentation](https://docs.codecov.com/)