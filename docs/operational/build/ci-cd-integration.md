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
| [`.github/AGENTS.md`](../../../.github/AGENTS.md) | Functional CI, optional hardening, coverage, acceptance, and release workflow boundaries |
| [`.github/workflows/AGENTS.md`](../../../.github/workflows/AGENTS.md) | Current workflow jobs, dependency preparation, and gate requirements |
| [`.github/workflows/README.md`](../../../.github/workflows/README.md) | Job graph synopsis and reproduce-CI shell snippets |

High-signal behavioral anchors:

1. **Functional CI** — Main pushes, pull requests, and manual dispatch run on Linux with Python 3.14. `actionlint`, `lint`, and `detect-projects` prepare the checks; `test-infra` runs the selected functional shards and `test-contract` runs the selected complete contract modules. Documentation-only changes select documentation contracts.
2. **`test-project`** — Each selected public exemplar builds its standalone wheel and runs the focused behavioral tests declared in `.github/project-smoke.json`. Documentation-only changes skip this lane. These checks do not measure full-suite coverage or establish native release acceptance.
3. **Coverage and hardening** — Manual CI dispatch accepts an optional exact public `coverage-project` and calls `exemplar-coverage.yml` for that project's locked release-profile coverage. The **Public exemplar coverage** workflow can measure the full public roster. The broader cross-version/full-suite matrix and conditional `fep-lean` checks live in the separate, manual-only `hardening.yml`; formal release acceptance remains in `platform-required-acceptance.yml`.
4. **`CI Gate`** — The aggregate gate requires the selected functional lanes to succeed. It accepts the project-smoke skip only for documentation-only selection and the optional coverage skip only when coverage was not requested. The separate **`release`** workflow is manual-only and requires `tag`, `acceptance_run_id`, `acceptance_artifact_id`, and `acceptance_receipt_sha256` for an exact-tag acceptance handoff.

Other automation includes **[`stale.yml`](../../../.github/workflows/stale.yml)**, the [Dependabot configuration](../../../.github/dependabot.yml), and **[`release.yml`](../../../.github/workflows/release.yml)** (manual dispatch with the four required acceptance inputs above). See [`.github/AGENTS.md`](../../../.github/AGENTS.md).

## GitHub Actions Setup

### Minimal single-job illustration (forks only)

Below is a single-job scaffold for forks. The repository workflow in [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) also requires lint/types, source and security guards, selected infrastructure contracts, standalone project builds, focused project tests, and its aggregate gate.

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
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
        with:
          enable-cache: true
          cache-dependency-glob: "**/uv.lock"
      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
        with:
          python-version: "3.14"
      - run: uv sync
      # Adjust paths for your checkout layout:
      - run: >-
          uv run pytest tests/infra_tests/
          --cov=infrastructure
          --cov-report=xml
          --cov-fail-under=60
```

## Automated Testing

This template separates **Layer 1** (`tests/infra_tests/` → `--cov=infrastructure`) from **Layer 2** (per-project `projects/<name>/tests/`). Functional CI selects focused checks; the manual coverage and hardening workflows run the broader measurements. The local `scripts/pipeline/stage_01_test.py --project-only --all-projects` path runs each project with an isolated coverage datafile and combines results after all project gates pass. The examples below are generic; see [.github/workflows/README.md](../../../.github/workflows/README.md) for the current workflow commands and boundaries.

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

**This repo** measures each selected public exemplar independently in the manual coverage workflow and enforces its own **90%** floor. Functional project smoke has no full-suite coverage claim. The local all-project orchestrator uses separate subprocesses/datafiles, then combines them and applies the combined-union `coverage report --fail-under=75` gate for release-style sweeps. See [.github/workflows/AGENTS.md](../../../.github/workflows/AGENTS.md).

### Test Matrix

**Test multiple Python versions:**

```yaml
strategy:
  matrix:
    python-version: ['3.14', '3.15']

steps:
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
  with:
    python-version: ${{ matrix.python-version }}
```

## Automated PDF Generation

### Optional PDF CI workflow (**not shipped** in default template)

Upstream PDF output is driven by `./run.sh` / `scripts/pipeline/stage_03_render.py` locally. The **`pdf-build.yml`** path referenced here is **an example schema**—add something like this under `.github/workflows/` on a fork **only if** CI PDF fits your LaTeX/pandoc budget:

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
      uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

    - name: Set up Python
      uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
      with:
        python-version: '3.14'

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
        uv run python scripts/runner/execute_pipeline.py --project {name} --mode core

    - name: Upload PDFs
      uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
      with:
        name: generated-pdfs
        path: output/{name}/pdf/*.pdf
```

Replace `{name}` with a discovered project slug (consult [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)).

### PDF Validation

**Validate generated PDFs:**

```yaml
- name: Validate PDFs
  run: |
    uv run python scripts/pipeline/stage_04_validate.py --project {name}

    # Check for errors
    if [ $? -ne 0 ]; then
      echo "PDF validation failed"
      exit 1
    fi
```

## Deployment Workflows

### Release workflow (**hypothetical** third-party snippet)

Repository publication uses [.github/workflows/release.yml](../../../.github/workflows/release.yml), invoked only by manual dispatch with `tag`, `acceptance_run_id`, `acceptance_artifact_id`, and `acceptance_receipt_sha256`. It verifies the selected tag and exact acceptance handoff before publication. The excerpt below is a fork-specific illustration reacting to **`release: published`**:

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
      uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

    - name: Set up Python
      uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
      with:
        python-version: '3.14'

    - name: Install dependencies
      run: |
        uv sync

    - name: Generate PDFs
      run: uv run python scripts/runner/execute_pipeline.py --project {name} --mode core

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

Upstream CI relies on **`astral-sh/setup-uv` `enable-cache`** against **`**/uv.lock`**, pinned in the shared [`.github/actions/setup-python-env`](../../../.github/actions/setup-python-env/action.yml) composite action (not inlined per-job) — check that file for the current pinned SHA/version rather than hardcoding it here. Sections below illustrate manual cache blocks for other setups.

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
3. **Preserve failures** - Make every required lane report its original outcome and make the aggregate gate fail when a required lane fails
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

- Match the selected workflow’s Python runtime, locked dependency groups, and preparation steps from [.github/workflows/AGENTS.md](../../../.github/workflows/AGENTS.md)
- Reproduce the failing job’s actual command: functional project smoke and manual full-suite coverage use different runners
- Inspect the original failed lane and aggregate `CI Gate` result; functional CI runs on Linux
- Confirm the selected canonical public project name against [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)

#### Issue: PDF generation fails

**Solution:**

- Verify LaTeX installation
- Check font availability
- Review error logs
- Test locally first

#### Issue: Coverage upload fails

**Solution:**

- For the manual exemplar-coverage workflow, inspect its selected project, original measurement logs, and uploaded source-bound result artifact
- For optional hardening Codecov uploads, check the exact XML path and upload condition in `hardening.yml`
- **`CODECOV_TOKEN`** is optional on public repositories; an upload result does not replace the underlying coverage gate

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

Functional CI and hardening have no scheduled trigger. Forks can add an explicit schedule when they intend to run it:

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday UTC
  workflow_dispatch:
```

### Example 3: Multi-Platform Testing

Functional CI uses Linux. The optional manual hardening workflow declares its cross-platform matrix. Forks can define a broader matrix when each platform has the required tooling:

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
