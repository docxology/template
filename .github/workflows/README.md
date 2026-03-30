# workflows/ — CI/CD Pipelines

GitHub Actions workflows for automated quality assurance, testing, and deployment. Enforces development standards across Python versions and environments.

For Dependabot, issue/PR templates, and the full GitHub integration picture, see **[`../README.md`](../README.md)** in the parent `.github/` folder.

## Workflows

| File | Trigger | Purpose |
|---|---|---|
| [`ci.yml`](ci.yml) | push/PR to `main`, weekly, manual | Full 7-job quality gate pipeline |
| [`stale.yml`](stale.yml) | Daily 01:00 UTC | Auto-label and close stale issues/PRs |
| [`release.yml`](release.yml) | `v*.*.*` tag push or manual | Generate GitHub Release with changelog |

## CI Pipeline (`ci.yml`)

### Job Graph

```
lint (Ruff + mypy)
 └── verify-no-mocks
      ├── test-infra  · ubuntu+macos × 3.10/3.11/3.12 · ≥60% coverage
      ├── test-project · ubuntu+macos × 3.10/3.11/3.12 · ≥90% coverage
      ├── validate    · manuscript markdown + project imports
      └── security    · pip-audit + bandit MEDIUM+
test-infra + test-project
 └── performance     · total import time ≤ 5 s
```

### Quality Gates

| Gate | Threshold |
|---|---|
| Ruff lint | zero violations |
| Ruff format | zero diffs |
| mypy | no errors |
| No-mocks policy | zero mock usage |
| Infrastructure coverage | ≥ 60% |
| Project coverage | ≥ 90% |
| Bandit MEDIUM+ | zero findings |
| Import time | ≤ 5 s total |

### Local CI Simulation

```bash
# Lint
uvx ruff check infrastructure/ projects/*/src/
uvx ruff format --check infrastructure/ projects/*/src/
uv run mypy infrastructure/ projects/*/src/

# Infrastructure tests
uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-datafile=.coverage.infra --cov-fail-under=60 \
  -m "not requires_ollama"

# Project tests
uv run pytest projects/*/tests/ \
  --cov=projects --cov-datafile=.coverage.project --cov-fail-under=90 \
  -m "not requires_ollama"

# Security
uv run pip-audit
uv run bandit -r -ll infrastructure/ scripts/ projects/ \
  --exclude projects_archive,projects_in_progress
```

## Stale Workflow (`stale.yml`)

| Item | Stale after | Closed after |
|---|---|---|
| Issues | 60 days | + 14 days |
| PRs | 30 days | + 14 days |

Exempt labels: `pinned` · `security` · `in-progress` · `blocked` · `do-not-close`

## Release Workflow (`release.yml`)

Triggered on `v*.*.*` tag push or `workflow_dispatch`. Generates commit-based changelog since previous tag; creates GitHub Release via `softprops/action-gh-release@v2`. Tags containing `-rc`/`-beta`/`-alpha` are auto-marked as pre-release.

## Troubleshooting

```bash
# Fix linting
uvx ruff check infrastructure/ projects/*/src/ --fix
uvx ruff format infrastructure/ projects/*/src/

# View CI run logs
gh run list --workflow=CI --limit=5
gh run view <run-id> --log-failed

# Re-run failed jobs
gh run rerun <run-id> --failed

# Debug specific test
uv run pytest tests/infra_tests/test_foo.py::TestClass::test_method -s --pdb

# Coverage HTML report
uv run pytest projects/*/tests/ --cov=projects --cov-report=html --cov-datafile=.coverage.project
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
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          cache-dependency-glob: "**/uv.lock"
      - uses: actions/setup-python@v5
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