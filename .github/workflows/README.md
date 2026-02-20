# workflows/ - CI/CD Pipelines

GitHub Actions workflows for automated quality assurance, testing, and deployment. Ensures code reliability across Python versions and enforces development standards.

## Overview

```mermaid
graph TD
    subgraph Workflows["workflows/ - CI/CD Workflows"]
        CI[ci.yml<br/>Main CI pipeline<br/>Quality assurance]
        AGENTS[AGENTS.md<br/>Technical documentation<br/>Workflow details]
        README[README.md<br/>Quick reference<br/>This file]
    end

    subgraph Pipeline["CI Pipeline Stages"]
        LINT[Lint Job<br/>Code quality<br/>Python 3.12]
        TESTINFRA[Test Infra Job<br/>Infrastructure tests<br/>Python 3.10, 3.11, 3.12]
        TESTPROJ[Test Project Job<br/>Project tests<br/>Python 3.10, 3.11, 3.12]
        VALIDATE[Validate Job<br/>Manuscript validation<br/>Python 3.12]
        SECURITY[Security Job<br/>Dependency & code audit<br/>Python 3.12]
        PERF[Performance Job<br/>Import benchmarks<br/>Python 3.12]
    end

    subgraph Quality["Quality Assurance"]
        CODE[Code Standards<br/>Ruff linting<br/>Import sorting]
        FORMAT[Formatting<br/>Black-compatible<br/>Line length checks]
        COVERAGE[Test Coverage<br/>60% infrastructure<br/>90% project]
    end

    subgraph Reporting["Automated Reporting"]
        STATUS[Status Checks<br/>GitHub integration<br/>Branch protection]
        COVERAGE_REPORT[Coverage Reports<br/>Codecov integration<br/>HTML reports]
        LOGS[Build Logs<br/>Execution details<br/>Failure analysis]
    end

    CI --> LINT
    CI --> TESTINFRA
    CI --> TESTPROJ
    LINT --> VALIDATE
    LINT --> SECURITY
    TESTINFRA --> PERF
    TESTPROJ --> PERF
    LINT --> CODE
    LINT --> FORMAT
    TESTINFRA --> COVERAGE
    TESTPROJ --> COVERAGE
    COVERAGE --> COVERAGE_REPORT
    CI --> STATUS
    STATUS --> LOGS

    classDef docs fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef pipeline fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef quality fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef reporting fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class AGENTS,README docs
    class CI,LINT,TESTINFRA,TESTPROJ,VALIDATE,SECURITY,PERF pipeline
    class CODE,FORMAT,COVERAGE quality
    class STATUS,COVERAGE_REPORT,LOGS reporting
```

## Quick Start

### Check Pipeline Status
```bash
# View workflow runs
gh run list --workflow=CI --limit=5

# Check current status
gh workflow view CI --ref=main

# View latest run details
gh run view --workflow=CI
```

### Local Pipeline Testing
```bash
# Simulate linting (matches CI)
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/
uvx ruff format --check infrastructure/ projects/act_inf_metaanalysis/src/

# Simulate infrastructure testing (matches CI)
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Simulate project testing (matches CI)
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

## CI Pipeline (ci.yml)

### Workflow Triggers
```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

### Pipeline Jobs

#### 1. Lint & Type Check (`lint`)
**Purpose:** Enforce coding standards, formatting, and type safety

**Configuration:**
- **Runner:** `ubuntu-latest`
- **Python:** 3.12

**Steps:**
1. **Checkout** - Get repository code
2. **Setup uv** - Package manager with caching
3. **Setup Python** - Install Python 3.12
4. **Sync Dependencies** - Install project dependencies
5. **Ruff Check** - Code linting on `infrastructure/` and `projects/act_inf_metaanalysis/src/`
6. **Ruff Format Check** - Code formatting validation
7. **Type Checking** - mypy on `infrastructure/` and `projects/act_inf_metaanalysis/src/`

#### 2. Infrastructure Tests (`test-infra`)
**Purpose:** Validate infrastructure code across Python versions

**Matrix Configuration:**
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

**Per-Version Steps:**
1. **Checkout** - Get repository code
2. **Setup uv** - Package manager with caching
3. **Setup Python** - Install matrix Python version
4. **Sync Dependencies** - Install dependencies
5. **Run Infrastructure Tests** - `tests/infra_tests/` with 60% coverage minimum

#### 3. Project Tests (`test-project`)
**Purpose:** Validate project code across Python versions

**Matrix Configuration:**
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

**Per-Version Steps:**
1. **Checkout** - Get repository code
2. **Setup uv** - Package manager with caching
3. **Setup Python** - Install matrix Python version
4. **Sync Dependencies** - Install dependencies
5. **Run Project Tests** - `projects/act_inf_metaanalysis/tests/` with 90% coverage minimum

#### 4. Validate Manuscripts (`validate`)
**Purpose:** Validate manuscript markdown and project imports
**Depends on:** `lint`

**Steps:**
1. **Checkout** - Get repository code
2. **Setup uv & Python 3.12**
3. **Validate Manuscript Markdown** - Check `projects/act_inf_metaanalysis/manuscript/`
4. **Verify Project Imports** - Ensure `projects.act_inf_metaanalysis.src` imports cleanly

#### 5. Security Scan (`security`)
**Purpose:** Audit dependencies and scan code for security issues
**Depends on:** `lint`

**Steps:**
1. **Checkout** - Get repository code
2. **Setup uv & Python 3.12**
3. **Dependency Audit** - `pip-audit` (continue on error)
4. **Code Security Scan** - `bandit` on `infrastructure/` and `projects/act_inf_metaanalysis/src/`

#### 6. Performance Check (`performance`)
**Purpose:** Ensure import times remain acceptable
**Depends on:** `test-infra`, `test-project`

**Steps:**
1. **Checkout** - Get repository code
2. **Setup uv & Python 3.12**
3. **Run Import Benchmarks** - Verify import time under 5 seconds

### Quality Requirements

#### Code Standards
- **Ruff Rules:** Comprehensive Python code quality
- **Import Sorting:** Consistent import organization
- **Type Checking:** Basic type annotation validation
- **Error Detection:** Static error identification

#### Formatting Standards
- **Line Length:** 88 characters (Black compatible)
- **Quote Style:** Double quotes preferred
- **Trailing Commas:** Consistent usage
- **Indentation:** 4 spaces standard

#### Test Coverage
- **Infrastructure:** 60% minimum coverage
- **Project:** 90% minimum coverage
- **Real Data:** No mock methods allowed
- **Integration:** Cross-module testing

### Execution Time
- **Lint Job:** ~30 seconds
- **Test Jobs:** ~2-3 minutes per Python version
- **Validate Job:** ~30 seconds
- **Security Job:** ~1 minute
- **Performance Job:** ~30 seconds
- **Total Pipeline:** ~5-7 minutes

## Status Checks

### Required Checks for Main Branch
```bash
# Status checks required before merge
- lint
- test-infra (3.10)
- test-infra (3.11)
- test-infra (3.12)
- test-project (3.10)
- test-project (3.11)
- test-project (3.12)
- validate
- security
- performance
```

### Branch Protection Setup
```yaml
required_status_checks:
  - lint
  - test-infra (3.10)
  - test-infra (3.11)
  - test-infra (3.12)
  - test-project (3.10)
  - test-project (3.11)
  - test-project (3.12)
  - validate
  - security
  - performance

required_pull_request_reviews:
  required_approving_review_count: 1
```

## Coverage Reporting

### Coverage Reports
- **Terminal:** `pytest --cov-report=term-missing` (used in CI)
- **HTML:** `pytest --cov-report=html` (opens in browser locally)
- **Infrastructure minimum:** 60% coverage
- **Project minimum:** 90% coverage

## Workflow Management

### Common Commands
```bash
# List all workflows
gh workflow list

# View workflow details
gh workflow view CI

# View workflow YAML
gh workflow view CI --yaml

# Run workflow manually (if workflow_dispatch enabled)
gh workflow run CI
```

### Debugging Workflows
```bash
# View failed run logs
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>

# View job logs specifically
gh run view <run-id> --job=<job-id>

# Rerun failed jobs
gh run rerun <run-id> --failed
```

## Local Development

### Simulating CI Locally
```bash
# Set CI environment variables
export CI=true
export GITHUB_ACTIONS=true
export GITHUB_WORKFLOW=CI

# Run linting (matches CI exactly)
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/
uvx ruff format --check infrastructure/ projects/act_inf_metaanalysis/src/
uv run mypy infrastructure/ projects/act_inf_metaanalysis/src/

# Run infrastructure tests with coverage (matches CI)
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Run project tests with coverage (matches CI)
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

### Pre-commit Checks
```bash
# Run before committing
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/ --fix
uvx ruff format infrastructure/ projects/act_inf_metaanalysis/src/
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

## Troubleshooting

### Common Pipeline Issues

#### Linting Failures
```bash
# Fix linting issues locally
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/ --fix
uvx ruff format infrastructure/ projects/act_inf_metaanalysis/src/

# Check what would be fixed
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/ --diff
```

#### Test Failures
```bash
# Run infrastructure tests locally with details
uv run pytest tests/infra_tests/ -v

# Run project tests locally with details
uv run pytest projects/act_inf_metaanalysis/tests/ -v

# Debug specific test
uv run pytest tests/infra_tests/test_specific.py::TestClass::test_method -s --pdb

# Run only failed tests
uv run pytest projects/act_inf_metaanalysis/tests/ --lf
```

#### Coverage Issues
```bash
# Check infrastructure coverage locally
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-report=term-missing
open htmlcov/index.html

# Check project coverage locally
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-report=html
open htmlcov/index.html

# Verify minimum requirements
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

#### Python Version Issues
```bash
# Test with specific Python version
python3.10 -m pytest tests/infra_tests/
python3.11 -m pytest tests/infra_tests/
python3.12 -m pytest tests/infra_tests/
```

### Workflow Debugging
```bash
# Check workflow syntax
gh workflow run --list

# View workflow logs
gh run view <run-id> --log-failed

# Test workflow changes locally first
# Then commit and monitor CI results
```

## Customization

### Adding New Jobs
```yaml
jobs:
  new-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Sync dependencies
        run: uv sync
      - name: New quality check
        run: uv run python scripts/custom_check.py
```

### Modifying Quality Gates
```yaml
# Add new linting rules
- name: Additional checks
  run: uv run python scripts/extra_checks.py
```

### Environment Variables
```bash
# Add to workflow environment
env:
  CUSTOM_VAR: value
  LOG_LEVEL: 0
```

## Security Considerations

### Secret Management
- **GitHub Secrets:** Encrypted token storage
- **Environment Variables:** Secure value injection
- **Minimal Permissions:** Least privilege access
- **Audit Logging:** Access tracking

### Dependency Security
```yaml
# Active in CI pipeline
- name: Dependency audit
  run: uv run pip-audit
- name: Code security scan
  run: uv run bandit -r infrastructure/ projects/act_inf_metaanalysis/src/
```

## Performance Optimization

### Execution Time Reduction
- **Parallel Jobs:** Matrix strategy for concurrent execution
- **Dependency Caching:** uv cache utilization
- **Selective Testing:** Targeted test execution
- **Resource Optimization:** Efficient runner usage

### Monitoring
- **Build Duration Tracking:** Pipeline execution time monitoring
- **Success Rate Analysis:** Build reliability tracking
- **Resource Usage:** CPU and memory monitoring
- **Failure Pattern Analysis:** Common issue identification

## Integration Points

### With Repository
- **Branch Protection:** Quality gates for main branch
- **Pull Request Validation:** Automated PR checks
- **Status Reporting:** Real-time build status
- **Coverage Badges:** Repository quality indicators

### With Development Tools
- **IDE Integration:** Local linting matches CI
- **Pre-commit Hooks:** Automated quality checks
- **Code Formatting:** Consistent with CI standards
- **Test Coverage:** Local coverage matches CI requirements

## Future Enhancements

### Planned Improvements
- **Multi-OS Testing:** Windows and macOS compatibility
- **Performance Regression:** Automated performance monitoring
- **Security Scanning:** Advanced vulnerability detection
- **Container Testing:** Docker-based integration testing
- **Dependency Updates:** Automated dependency management

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete CI/CD workflow documentation
- [`../AGENTS.md`](../AGENTS.md) - GitHub integration overview
- [`../../docs/operational/CI_CD_INTEGRATION.md`](../../docs/operational/CI_CD_INTEGRATION.md) - CI/CD integration guide
- [`../../docs/development/CONTRIBUTING.md`](../../docs/development/CONTRIBUTING.md) - Contribution guidelines