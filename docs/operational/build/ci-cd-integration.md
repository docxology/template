# CI/CD Integration Guide

> **guide** for integrating with GitHub Actions and CI/CD systems

**Quick Reference:** [Common Workflows](../../reference/common-workflows.md) | [Build System](build-system.md) | [Troubleshooting Guide](../../operational/troubleshooting/)

This guide describes generic CI/CD integration patterns plus **what this repository actually runs** under [`.github/workflows/`](../../../.github/workflows/).

## Overview

CI/CD integration automates:

- **Testing** - Run tests on every commit
- **Validation** - Verify build system integrity
- **PDF Generation** - Generate PDFs in CI environments (often a **fork-added** workflow; see below)
- **Deployment** - Automate publication workflows
- **Quality Checks** - Run validation and quality checks

## CI in this repository (authoritative source)

Upstream CI is **`name: CI`** in [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml). Contracts and **`name:`** strings for branch protection live in:

| Doc | Contents |
| --- | --- |
| [`.github/AGENTS.md`](../../../.github/AGENTS.md) | Triggers, concurrency, dependency groups (`test-infra` vs `test-project`), combined project coverage semantics, macOS infra `continue-on-error`, stale / Dependabot / release summaries |
| [`.github/workflows/AGENTS.md`](../../../.github/workflows/AGENTS.md) | Per-job steps: `lint`, `verify-no-mocks`, matrices, conditional `fep-lean`, `validate`, `security`, `performance` |
| [`.github/workflows/README.md`](../../../.github/workflows/README.md) | Job graph synopsis and reproduce-CI shell snippets |

High-signal behavioral anchors:

1. **`test-infra`** — `uv sync --group rendering --group monitoring`; Ubuntu + macOS × Python 3.10–3.12; **≥ 60 %** on `infrastructure/`. pytest uses **`continue-on-error: true` on macOS**; treat **Ubuntu matrix legs as the authoritative merge gate**.
2. **`test-project`** — Adds `--group discopy`. Runs **one `pytest` invocation per `projects/*/tests/`** with **`--cov=projects/<name>/src`** and **`--cov-append`**, skipping `projects/fep_lean/tests/`, then **`coverage report --fail-under=90`** on the **combined** trace across measured project packages.
3. **`fep-lean`** — Runs **only when** [`hashFiles`](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsrun) guard finds `projects/fep_lean/lean/lean-toolchain` (`if:` in workflow). Otherwise skipped.
4. **Manual CI runs** — `workflow_dispatch` on **CI has no workflow inputs**. (The **`release`** workflow differs: **`workflow_dispatch`** expects a **`tag`** input.)

Other automation: **[`stale.yml`](../../../.github/workflows/stale.yml)**, **`dependabot.yml`**, **`release.yml`** (`v*.*.*` tags + tagged dispatch) — see [`.github/AGENTS.md`](../../../.github/AGENTS.md).

## GitHub Actions Setup

### Minimal single-job illustration (forks only)

Below is intentionally **narrow**—useful as a scaffold for forks. It **does not** replace [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) **(lint, no-mocks scan, multi-job DAG, manuscripts, Bandit/pip-audit, performance import gate, matrices).**

```yaml
name: CI (minimal illustration)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          cache-dependency-glob: "**/uv.lock"
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: uv sync
      # Adjust paths for your checkout layout:
      - run: >-
          uv run pytest tests/infra_tests/
          --cov=infrastructure
          --cov-report=xml
          --cov-fail-under=60
```

## Automated Testing

This template separates **Layer 1** (`tests/infra_tests/` → `--cov=infrastructure`) from **Layer 2** (**per-project `projects/<name>/tests/`** merged with **`--cov-append`**). Patterns below are generic; parity with Actions is [.github/workflows/README.md](../../../.github/workflows/README.md) “Reproduce CI locally”.

### Test Execution

**Basic test run:**

```yaml
- name: Run tests
  run: uv run pytest tests/ -v
```

**With coverage:**

```yaml
- name: Run tests with coverage
  run: |
    uv run pytest tests/ --cov=my_package --cov-report=xml --cov-report=html
```

**Parallel execution:**

```yaml
- name: Run tests in parallel
  run: |
    uv run pytest tests/ -n auto
```

### Coverage Requirements

For a single-package layout, **`pytest-cov`** can enforce gates directly:

```yaml
- name: pytest with cov floor
  run: >-
    uv run pytest tests/
    --cov=my_package
    --cov-fail-under=90
```

**This repo** aggregates multiple `projects/<name>/src` trees (`--cov-append` + `coverage report --fail-under=90`). See [.github/workflows/AGENTS.md](../../../.github/workflows/AGENTS.md).

### Test Matrix

**Test multiple Python versions:**

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
```

## Automated PDF Generation

### Optional PDF CI workflow (**not shipped** in default template)

Upstream PDF output is driven by `./run.sh` / `scripts/03_render_pdf.py` locally. The **`pdf-build.yml`** path referenced here is **an example schema**—add something like this under `.github/workflows/` on a fork **only if** CI PDF fits your LaTeX/pandoc budget:

```yaml
name: PDF Generation

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  generate-pdf:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install LaTeX
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          pandoc \
          texlive-xetex \
          texlive-fonts-recommended \
          texlive-latex-extra \
          fonts-dejavu

    - name: Install dependencies
      run: |
        uv sync

    - name: Generate PDFs
      env:
        AUTHOR_NAME: ${{ secrets.AUTHOR_NAME }}
        AUTHOR_EMAIL: ${{ secrets.AUTHOR_EMAIL }}
        AUTHOR_ORCID: ${{ secrets.AUTHOR_ORCID }}
        PROJECT_TITLE: ${{ secrets.PROJECT_TITLE }}
      run: |
        uv run python scripts/execute_pipeline.py --project {name} --core-only

    - name: Upload PDFs
      uses: actions/upload-artifact@v4
      with:
        name: generated-pdfs
        path: output/pdf/*.pdf
```

Replace `{name}` with a discovered project slug (consult [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)).

### PDF Validation

**Validate generated PDFs:**

```yaml
- name: Validate PDFs
  run: |
    uv run python scripts/04_validate_output.py --project {name}

    # Check for errors
    if [ $? -ne 0 ]; then
      echo "PDF validation failed"
      exit 1
    fi
```

## Deployment Workflows

### Release workflow (**hypothetical** third-party snippet)

Upstream shipping uses [.github/workflows/release.yml](../../../.github/workflows/release.yml) (**tag **`v*.*.*`**, **`softprops/action-gh-release`**). The excerpt below sketches an **alternate** CI pattern reacting to **`release: published`**—not what this repo’s file does:

```yaml
name: Release (illustrative)

on:
  release:
    types: [published]

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        uv sync

    - name: Generate PDFs
      run: uv run python scripts/execute_pipeline.py --project {name} --core-only

    - name: Create release package
      run: |
        mkdir -p release
        cp output/{name}/pdf/{name}_combined.pdf release/
        cp -r projects/{name}/output/figures release/
        tar -czf release.tar.gz release/

    - name: Upload release assets
      uses: actions/upload-release-asset@v1
      with:
        upload_url: ${{ github.event.release.upload_url }}
        asset_path: ./release.tar.gz
        asset_name: release.tar.gz
        asset_content_type: application/gzip
```

Paths above are placeholders; mirror your `output/` layout.

### Deployment to Repository

**Deploy PDFs to repository:**

```yaml
- name: Deploy PDFs
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./output/pdf
    destination_dir: pdfs
```

## Secrets Management

### Required Secrets

Configure these secrets in GitHub repository settings:

- `AUTHOR_NAME` - Author name for PDF metadata
- `AUTHOR_EMAIL` - Author email
- `AUTHOR_ORCID` - ORCID identifier
- `PROJECT_TITLE` - Project title
- `DOI` - Digital Object Identifier (optional)
- `CODECOV_TOKEN` — optional for Codecov uploads (public repos often work without); see [.github/README.md](../../../.github/README.md)

### Using Secrets

**In workflow:**

```yaml
env:
  AUTHOR_NAME: ${{ secrets.AUTHOR_NAME }}
  AUTHOR_EMAIL: ${{ secrets.AUTHOR_EMAIL }}
  AUTHOR_ORCID: ${{ secrets.AUTHOR_ORCID }}
```

## Caching Strategies

Upstream CI relies on **`astral-sh/setup-uv@v6` `enable-cache`** against **`**/uv.lock`**. Sections below illustrate manual cache blocks for other setups.

### Dependency Caching

**Cache uv dependencies:**

```yaml
- name: Cache uv dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
    restore-keys: |
      ${{ runner.os }}-uv-
```

### Build Artifact Caching

**Cache build outputs:**

```yaml
- name: Cache build artifacts
  uses: actions/cache@v4
  with:
    path: output/
    key: ${{ runner.os }}-build-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-build-
```

### Python Cache

**Cache Python packages:**

```yaml
- name: Cache Python packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

## Best Practices

### Workflow Organization

1. **Separate jobs** - Test, build, and deploy separately
2. **Use dependencies** - `needs:` to order jobs
3. **Fail fast** - Stop on first failure (except where `continue-on-error` is deliberate—see infra macOS semantics above)
4. **Parallel execution** - Run independent jobs in parallel

### Error Handling

1. **Set timeouts** - Prevent hanging workflows
2. **Handle failures** - Use `continue-on-error` when appropriate
3. **Notify on failure** - Send alerts for critical failures
4. **Retry logic** - Retry transient failures

### Performance

1. **Use caching** - Cache dependencies and artifacts
2. **Parallel jobs** - Run independent tests in parallel
3. **Optimize steps** - Minimize setup time
4. **Clean up** - Remove unnecessary files

## Troubleshooting

### Common Issues

#### Issue: Tests fail in CI but pass locally

**Solution:**

- Match Python **`matrix`** / **uv sync** groups to [.github/workflows/AGENTS.md](../../../.github/workflows/AGENTS.md)
- **`PYTHONPATH=.`** is set for project pytest in **`test-project`**; mirror locally if imports fail
- macOS infra failures may be **`continue-on-error`**—check Ubuntu logs first
- Rotate **active `projects/`** roster; consult [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)

#### Issue: PDF generation fails

**Solution:**

- Verify LaTeX installation
- Check font availability
- Review error logs
- Test locally first

#### Issue: Coverage upload fails

**Solution:**

- XML path names differ (`coverage-infra.xml`, `coverage-project.xml` upstream)
- **`CODECOV_TOKEN`** optional on public repos
- Upload gated to Ubuntu + Python **3.12** matrix cells upstream

### Debugging

**Enable debug logging:**

```yaml
- name: Debug
  run: |
    echo "::debug::Debug information here"
    uv --version
    python --version
```

**Run with verbose output:**

```yaml
- name: Run tests
  run: uv run pytest tests/ -vv
```

## Integration Examples

### Example 1: CI pipeline parity

Treat [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) plus [`.github/workflows/README.md`](../../../.github/workflows/README.md) as the runnable reference—not the minimal YAML snippets in this guide.

### Example 2: Scheduled Builds

Upstream CI already fires weekly (`cron`) for CVE-ish drift; forks can add schedules similarly:

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday UTC
  workflow_dispatch:
```

### Example 3: Multi-Platform Testing

Upstream tests **Ubuntu + macOS** (Linux gate authoritative for infra flakes). Extend with **Windows** only if tooling supports:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]

runs-on: ${{ matrix.os }}
```

## Summary

CI/CD integration provides automated testing, optional PDF pipelines, deployment hooks, and quality validation.

Canonical paths for **this repo**:

- [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml), [`.github/AGENTS.md`](../../../.github/AGENTS.md), [`.github/README.md`](../../../.github/README.md)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Build System](build-system.md)
- [Troubleshooting Guide](../../operational/troubleshooting/)

---

**Related Documentation:**

- [Common Workflows](../../reference/common-workflows.md) — Workflow recipes
- [Build System](build-system.md) — Build pipeline internals
- [Best Practices](../../best-practices/best-practices.md)
- [.github/workflows/AGENTS.md](../../../.github/workflows/AGENTS.md) — Detailed CI semantics
