# CI/CD Integration Guide

> **Complete guide** for integrating with GitHub Actions and CI/CD systems

**Quick Reference:** [Common Workflows](COMMON_WORKFLOWS.md) | [Build System](BUILD_SYSTEM.md) | [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)

This guide provides comprehensive instructions for setting up Continuous Integration and Continuous Deployment (CI/CD) workflows using GitHub Actions and other CI/CD systems.

## Overview

CI/CD integration automates:

- **Testing** - Run tests on every commit
- **Validation** - Verify build system integrity
- **PDF Generation** - Generate PDFs in CI environment
- **Deployment** - Automate publication workflows
- **Quality Checks** - Run validation and quality checks

## GitHub Actions Setup

### Basic Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests
      run: uv run pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Complete CI Workflow

**File:** `.github/workflows/ci.yml`

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
        restore-keys: |
          ${{ runner.os }}-uv-
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests with coverage
      run: |
        uv run pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Check coverage threshold
      run: |
        coverage=$(uv run pytest tests/ --cov=src --cov-report=term | grep TOTAL | awk '{print $NF}' | sed 's/%//')
        threshold=70
        if (( $(echo "$coverage < $threshold" | bc -l) )); then
          echo "Coverage $coverage% is below threshold $threshold%"
          exit 1
        fi

  build:
    name: Build PDFs
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu
    
    - name: Install Python dependencies
      run: uv sync
    
    - name: Run build pipeline
      run: ./repo_utilities/render_pdf.sh
    
    - name: Validate PDFs
      run: |
        uv run python repo_utilities/validate_pdf_output.py
    
    - name: Upload PDF artifacts
      uses: actions/upload-artifact@v3
      with:
        name: pdfs
        path: output/pdf/*.pdf
        retention-days: 30

  validate:
    name: Validate Build
    runs-on: ubuntu-latest
    needs: build
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Download PDF artifacts
      uses: actions/download-artifact@v3
      with:
        name: pdfs
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    
    - name: Install dependencies
      run: uv sync
    
    - name: Validate PDF quality
      run: |
        uv run python repo_utilities/validate_pdf_output.py
```

## Automated Testing

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
    uv run pytest tests/ --cov=src --cov-report=xml --cov-report=html
```

**Parallel execution:**
```yaml
- name: Run tests in parallel
  run: |
    uv run pytest tests/ -n auto
```

### Coverage Requirements

**Enforce coverage threshold:**
```yaml
- name: Check coverage
  run: |
    uv run pytest tests/ --cov=src --cov-report=term
    coverage=$(uv run pytest tests/ --cov=src --cov-report=term | grep TOTAL | awk '{print $NF}' | sed 's/%//')
    if (( $(echo "$coverage < 70" | bc -l) )); then
      echo "Coverage below 70%"
      exit 1
    fi
```

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

### PDF Build Workflow

**File:** `.github/workflows/pdf-build.yml`

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
        python-version: '3.11'
    
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
        ./repo_utilities/render_pdf.sh
    
    - name: Upload PDFs
      uses: actions/upload-artifact@v3
      with:
        name: generated-pdfs
        path: output/pdf/*.pdf
```

### PDF Validation

**Validate generated PDFs:**
```yaml
- name: Validate PDFs
  run: |
    uv run python repo_utilities/validate_pdf_output.py
    
    # Check for errors
    if [ $? -ne 0 ]; then
      echo "PDF validation failed"
      exit 1
    fi
```

## Deployment Workflows

### Release Workflow

**File:** `.github/workflows/release.yml`

```yaml
name: Release

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
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        uv sync
    
    - name: Generate PDFs
      run: ./repo_utilities/render_pdf.sh
    
    - name: Create release package
      run: |
        mkdir -p release
        cp output/pdf/project_combined.pdf release/
        cp -r output/figures release/
        tar -czf release.tar.gz release/
    
    - name: Upload release assets
      uses: actions/upload-release-asset@v1
      with:
        upload_url: ${{ github.event.release.upload_url }}
        asset_path: ./release.tar.gz
        asset_name: release.tar.gz
        asset_content_type: application/gzip
```

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

### Using Secrets

**In workflow:**
```yaml
env:
  AUTHOR_NAME: ${{ secrets.AUTHOR_NAME }}
  AUTHOR_EMAIL: ${{ secrets.AUTHOR_EMAIL }}
  AUTHOR_ORCID: ${{ secrets.AUTHOR_ORCID }}
```

## Caching Strategies

### Dependency Caching

**Cache uv dependencies:**
```yaml
- name: Cache uv dependencies
  uses: actions/cache@v3
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
  uses: actions/cache@v3
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
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

## Best Practices

### Workflow Organization

1. **Separate jobs** - Test, build, and deploy separately
2. **Use dependencies** - `needs:` to order jobs
3. **Fail fast** - Stop on first failure
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
- Check Python version matches
- Verify environment variables
- Check for platform-specific issues
- Review dependency versions

#### Issue: PDF generation fails

**Solution:**
- Verify LaTeX installation
- Check font availability
- Review error logs
- Test locally first

#### Issue: Coverage upload fails

**Solution:**
- Verify coverage file exists
- Check Codecov token
- Review file format
- Check upload permissions

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

### Example 1: Complete CI Pipeline

See the complete example in `.github/workflows/ci.yml` above.

### Example 2: Scheduled Builds

**Run builds on schedule:**
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:
```

### Example 3: Multi-Platform Testing

**Test on multiple platforms:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    
runs-on: ${{ matrix.os }}
```

## Summary

CI/CD integration provides:

- **Automated testing** - Run tests on every commit
- **PDF generation** - Automated document building
- **Quality checks** - Validate build integrity
- **Deployment** - Automated release workflows

For more information, see:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Build System](BUILD_SYSTEM.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)

---

**Related Documentation:**
- [Common Workflows](COMMON_WORKFLOWS.md) - Workflow examples
- [Build System](BUILD_SYSTEM.md) - Build pipeline details
- [Best Practices](BEST_PRACTICES.md) - CI/CD best practices

