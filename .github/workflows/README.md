# workflows/ — CI/CD Pipelines

GitHub Actions workflows for automated quality assurance, testing, and deployment. Enforces development standards across Python versions and environments.

For Dependabot, issue/PR templates, and the full GitHub integration picture, see **[`../README.md`](../README.md)** in the parent `.github/` folder.

## Workflows

| File | Trigger | Purpose |
|---|---|---|
| [`ci.yml`](ci.yml) | push/PR to `main`, weekly, manual | **12 jobs** (2 conditional via the `detect` job's outputs — `needs.detect.outputs.*`: **`fep-lean`** and **`setup-hook-windows-smoke`**; job-level `hashFiles()` is invalid and was removed; see [`AGENTS.md`](AGENTS.md)) |
| [`stale.yml`](stale.yml) | Daily 01:00 UTC | Auto-label and close stale issues/PRs |
| [`release.yml`](release.yml) | `v*.*.*` tag push or manual | Generate GitHub Release with changelog |

## CI Pipeline (`ci.yml`)

### Job Graph

`health`, `validate`, `security`, and `docs-lint` fan out from **`lint`**; `verify-no-mocks` gates the test matrix; **`performance`** waits on **`test-infra`** + **`test-project`**. See [`AGENTS.md`](AGENTS.md).

```mermaid
flowchart TB
    LINT[lint<br/>Ruff + mypy + exports audit] --> HEALTH[health<br/>informational JSON artefact]
    LINT --> VNM[verify-no-mocks]
    LINT --> VAL[validate<br/>markdown + api-ref check + imports]
    LINT --> SEC[security<br/>pip-audit + bandit -c bandit.yaml]
    LINT --> DL[docs-lint<br/>mermaid + links + consistency]
    VNM --> SHW[setup-hook-windows-smoke<br/>conditional · Windows]
    VNM --> TI[test-infra<br/>ubuntu × py310–312 + macOS × py312<br/>≥ 60% coverage]
    VNM --> TP[test-project<br/>9 exemplars × py310/py312 = 18 ubuntu jobs<br/>each ≥ 90% own src/]
    VNM --> FL[fep-lean optional<br/>gauss + lake · timeout 60m]
    TI --> PERF[performance<br/>import time ≤ 5 s]
    TP --> PERF

    classDef gate fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef matrix fill:#0f766e,stroke:#0f172a,color:#fff
    classDef terminal fill:#7c2d12,stroke:#0f172a,color:#fff
    classDef info fill:#334155,stroke:#0f172a,color:#fff
    class LINT,VNM gate
    class TI,TP,FL,SHW matrix
    class VAL,SEC,DL,PERF terminal
    class HEALTH info
```

### Quality Gates

| Gate | Threshold |
|---|---|
| Ruff lint | zero violations |
| Ruff format | zero diffs |
| mypy | no errors |
| `check-all-exports` | zero violations |
| No-mocks policy | zero mock usage |
| Infrastructure coverage | ≥ 60% |
| Per-project coverage (standalone) | ≥ 90% |
| Combined-union public-project coverage | ≥ 75% |
| pip-audit | blocking (ignore IDs from `.github/pip-audit-ignore.txt`; retries in CI) |
| Bandit MEDIUM+ (`bandit.yaml`) | zero findings |
| Docs lint | mermaid + cross-links + consistency + doc-pair coverage clean |
| Import time | ≤ 5 s total |

### Local CI Simulation

```bash
# Lint
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff check
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff format --check
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy

# Infrastructure tests
uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-datafile=.coverage.infra --cov-fail-under=60 \
  -m "not requires_ollama"

uv sync --group rendering --group monitoring --group discopy
COVERAGE_FILE=.coverage.project uv run python scripts/01_run_tests.py --project-only --all-projects --public-projects --non-strict --include-slow
uv run coverage xml -o coverage-project.xml

# Security (mirror CI — ignores file + bandit.yaml)
IGNORE_ARGS=()
while IFS= read -r raw || [ -n "$raw" ]; do
  [[ "$raw" =~ ^[[:space:]]*# ]] && continue
  line="${raw%%#*}"; line="$(echo "$line" | xargs)"
  [ -z "$line" ] || IGNORE_ARGS+=(--ignore-vuln "$line")
done < .github/pip-audit-ignore.txt
uv run pip-audit "${IGNORE_ARGS[@]}"
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/
```

## Stale Workflow (`stale.yml`)

| Item | Stale after | Closed after |
|---|---|---|
| Issues | 60 days | + 14 days |
| PRs | 30 days | + 14 days |

Exempt labels: `pinned` · `security` · `in-progress` · `blocked` · `do-not-close`

## Release Workflow (`release.yml`)

Triggered on `v*.*.*` tag push or `workflow_dispatch`. Verifies the requested tag exists, writes a git-log excerpt to the release body (`generate_release_notes: false`), and uses `softprops/action-gh-release@v3.0.0`. Tags containing `-rc`/`-beta`/`-alpha` are auto-marked as pre-release.

Current pinned GitHub Actions use the Node 24 action runtime. GitHub-hosted runners satisfy this; self-hosted runners must be Actions runner `v2.327.1` or newer.

## Troubleshooting

```bash
# Fix linting
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff check --fix
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff format

# View CI run logs
gh run list --workflow=CI --limit=5
gh run view <run-id> --log-failed

# Re-run failed jobs
gh run rerun <run-id> --failed

# Debug specific test
uv run pytest tests/infra_tests/test_foo.py::TestClass::test_method -s --pdb

# Coverage HTML report
uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=html
open htmlcov/index.html
```

## Adding New Jobs

```yaml
jobs:
  new-job:
    runs-on: ubuntu-latest
    needs: [lint]
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: astral-sh/setup-uv@v8.1.0
        with:
          enable-cache: true
          cache-dependency-glob: "**/uv.lock"
      - uses: actions/setup-python@v6.2.0
        with:
          python-version: "3.12"
      - name: Sync dependencies
        run: uv sync
      - name: Custom check
        run: uv run python scripts/custom_check.py
```

## See Also

- [`../README.md`](../README.md) — Full `.github/` guide (templates, Dependabot, CI overview)
- [`AGENTS.md`](AGENTS.md) — Full CI/CD technical documentation
- [`../AGENTS.md`](../AGENTS.md) — GitHub integration overview
- [`../../AGENTS.md`](../../AGENTS.md) — Root system overview
