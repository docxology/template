# GitHub Integration

## Overview

The `.github/` directory contains GitHub-specific configuration and automation for the Research Project Template. This includes continuous integration workflows, issue templates, PR templates, and other GitHub integrations that ensure code quality and collaborative development.

**Human entry point:** [README.md](README.md) (browsing on GitHub). **This file (`AGENTS.md`):** job names, paths, and thresholds for automation and agents.

## Publication

**Title**: *A template/ approach to Reproducible Generative Research: Architecture and Ergonomics from Configuration through Publication*
**DOI**: [10.5281/zenodo.19139090](https://doi.org/10.5281/zenodo.19139090)
**Record**: [zenodo.org/records/19139090](https://zenodo.org/records/19139090)
**License**: Apache 2.0

## Directory Structure

```text
.github/
├── AGENTS.md                    # This technical documentation
├── README.md                    # Quick reference
├── dependabot.yml               # Automated dependency updates
├── PULL_REQUEST_TEMPLATE.md     # PR checklist
├── ISSUE_TEMPLATE/
│   ├── config.yml               # Disable blank issues; add Discussions link
│   ├── bug_report.md            # Bug report template
│   ├── feature_request.md       # Feature request template
│   └── documentation.md         # Documentation update template
├── workflows/
│   ├── AGENTS.md                # CI/CD workflow documentation
│   ├── README.md                # Quick reference
│   ├── ci.yml                   # Main CI/CD pipeline (8 jobs; fep-lean conditional)
│   ├── stale.yml                # Auto-label and close stale issues/PRs
│   └── release.yml              # Create GitHub Releases on version tags
```

## Continuous Integration (CI/CD)

### CI Pipeline (`workflows/ci.yml`)

**Triggers:** push to `main`, pull requests targeting `main`, weekly scheduled run (Sunday midnight UTC), `workflow_dispatch`.
**Concurrency:** Running builds for the same ref are cancelled when a new commit arrives.

**Pipeline Jobs:**

| # | Job | Depends on | Python | Runner |
| --- | --- | --- | --- | --- |
| 1 | `lint` — Ruff + mypy | — | 3.12 | ubuntu |
| 2 | `verify-no-mocks` | lint | 3.12 | ubuntu |
| 3 | `test-infra` — 60% coverage | verify-no-mocks | 3.10–3.12 | ubuntu+macos |
| 4 | `test-project` — 90% coverage | verify-no-mocks | 3.10–3.12 | ubuntu+macos |
| 4b | `fep-lean` — Lean/Lake + Open Gauss (`gauss`) | verify-no-mocks | 3.12 | ubuntu |
| 5 | `validate` — manuscript markdown | lint | 3.12 | ubuntu |
| 6 | `security` — pip-audit + bandit | lint | 3.12 | ubuntu |
| 7 | `performance` — import ≤ 5 s | test-infra + test-project | 3.12 | ubuntu |

**Display name (branch protection):** the optional fep_lean job is reported as **`fep_lean (gauss + lake)`** (`ci.yml` `name:` on job id `fep-lean`). It runs only when `hashFiles('projects/fep_lean/lean/lean-toolchain') != ''` (otherwise skipped). When fep_lean lives under `projects_in_progress/`, the guard evaluates to empty and the job is skipped. Promote with `mv projects_in_progress/fep_lean projects/fep_lean` to activate CI.

Coverage is uploaded to **Codecov** after each test job (3.12/ubuntu-latest only).

The `verify-no-mocks` job runs [`scripts/verify_no_mocks.py`](../scripts/verify_no_mocks.py) at the repository root (not under `.github/`).

### Stale Workflow (`workflows/stale.yml`)

Runs daily. Issues → stale after 60 days, closed after 14 more. PRs → stale after 30 days, closed after 14 more. Exempt labels: `pinned`, `security`, `in-progress`, `blocked`, `do-not-close`.

### Release Workflow (`workflows/release.yml`)

Triggered by `v*.*.*` tag pushes. Generates a commit-based changelog and creates a GitHub Release via `softprops/action-gh-release@v2`.

## Dependabot (`dependabot.yml`)

[`dependabot.yml`](dependabot.yml) at the repository root: **GitHub Actions** (`package-ecosystem: github-actions`, `directory: /`) and **Python** (`package-ecosystem: pip`, `directory: /`) both read the root **`pyproject.toml`** / lockfile — compatible with **uv**. Weekly **Monday 09:00 UTC**, max **5** open PRs per ecosystem. Groups: **`actions-minor`** (Actions minor/patch), **`dev-tools`** and **`scientific-core`** (Python).

## Quality Gates

| Gate | Threshold |
| --- | --- |
| Ruff lint | zero violations |
| Ruff format | zero diffs |
| mypy | no errors |
| No-mocks policy | zero mock usage |
| Infrastructure coverage | ≥ 60% |
| Project coverage | ≥ 90% |
| Bandit MEDIUM+ | zero findings |
| Import time | ≤ 5 s |

## Branch Protection (Recommended)

Required checks must match the **`name:`** field of each job in [`workflows/ci.yml`](workflows/ci.yml). Matrix jobs expand to **Infra Tests (`<os>`, Python `<ver>`)** and **Project Tests (`<os>`, Python `<ver>`)** — require the combinations you care about (e.g. ubuntu-latest × 3.10/3.11/3.12), or use GitHub rulesets that treat required checks flexibly.

```yaml
required_status_checks:
  contexts:
    - "Lint & Type Check"
    - "Verify No Mocks Policy"
    - "Infra Tests (ubuntu-latest, Python 3.10)"
    - "Infra Tests (ubuntu-latest, Python 3.11)"
    - "Infra Tests (ubuntu-latest, Python 3.12)"
    - "Project Tests (ubuntu-latest, Python 3.10)"
    - "Project Tests (ubuntu-latest, Python 3.11)"
    - "Project Tests (ubuntu-latest, Python 3.12)"
    # Optional: only when fep_lean job runs (skipped if no lean-toolchain file)
    # - "fep_lean (gauss + lake)"
    - "Validate Manuscripts"
    - "Security Scan"
    - "Performance Check"
required_pull_request_reviews:
  required_approving_review_count: 1
```

## Issue Templates

| Template | Labels | Use for |
| --- | --- | --- |
| Bug Report | `bug`, `needs-triage` | Reproducible errors with log output |
| Feature Request | `enhancement`, `needs-triage` | New capabilities and improvements |
| Documentation Update | `documentation`, `needs-triage` | Incorrect or missing docs |

Blank issues are disabled. General questions should go to **GitHub Discussions**.

## Troubleshooting

```bash
# Fix linting locally
uvx ruff check infrastructure/ projects/*/src/ --fix
uvx ruff format infrastructure/ projects/*/src/

# Run tests locally (mirror CI)
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-datafile=.coverage.infra --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/*/tests/ --ignore=projects/fep_lean/tests/ --cov=projects/code_project/src --cov=projects/cognitive_case_diagrams/src --cov=projects/template/src --cov-datafile=.coverage.project --cov-fail-under=90 -m "not requires_ollama"

# Security scan locally
uv run pip-audit
uv run bandit -r -ll infrastructure/ scripts/ projects/ --exclude projects_archive,projects_in_progress

# Check workflow status via GitHub CLI
gh workflow list
gh run list --workflow=CI --limit=5
gh run view <run-id> --log
```

## See Also

- [`README.md`](README.md) — Contributor-oriented GitHub integration guide
- [`workflows/AGENTS.md`](workflows/AGENTS.md) — Detailed CI/CD workflow documentation
- [`../AGENTS.md`](../AGENTS.md) — Root system overview
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Documentation](https://docs.astral.sh/uv/)
