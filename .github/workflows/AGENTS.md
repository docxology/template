# CI/CD Workflows

## Overview

The `workflows/` directory contains GitHub Actions workflows that automate the continuous integration and delivery pipeline for the Research Project Template. These workflows ensure code quality, test reliability, and compatibility across different environments.

## Directory Structure

```
.github/workflows/
├── AGENTS.md               # This technical documentation
└── ci.yml                  # Main CI/CD pipeline
```

## CI Pipeline Architecture

### Complete CI/CD Workflow (`ci.yml`)

**Comprehensive automated quality assurance pipeline:**

#### Workflow Configuration

**Event Triggers:**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

**Concurrency Management:**
```yaml
concurrency:
  group: ci-${{ github.ref }}-${{ github.workflow }}
  cancel-in-progress: true
```

#### Job 1: Lint & Type Check (`lint`)

**Purpose:** Enforce code style, quality standards, and type safety

**Environment:**
- **Runner:** `ubuntu-latest`
- **Python Version:** 3.12

**Steps:**
1. **Checkout Code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Setup uv**
   ```yaml
   - uses: astral-sh/setup-uv@v7
     with:
       enable-cache: true
       cache-dependency-glob: "**/uv.lock"
   ```

3. **Setup Python Environment**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: "3.12"
   ```

4. **Install Dependencies**
   ```yaml
   - name: Sync dependencies
     run: uv sync
   ```

5. **Code Linting**
   ```yaml
   - name: Ruff lint
     run: uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/
   ```

6. **Format Checking**
   ```yaml
   - name: Ruff format check
     run: uvx ruff format --check infrastructure/ projects/act_inf_metaanalysis/src/
   ```

7. **Type Checking**
   ```yaml
   - name: Type checking
     run: uv run mypy infrastructure/ projects/act_inf_metaanalysis/src/
   ```

#### Job 2: Infrastructure Tests (`test-infra`)

**Purpose:** Validate infrastructure code across Python versions

**Matrix Strategy:**
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

**Environment per Matrix:**
- **Runner:** `ubuntu-latest`
- **Python Versions:** 3.10, 3.11, 3.12

**Steps:**
1. **Checkout Code**
2. **Setup uv** (with caching)
3. **Setup Python Environment** (matrix version)
4. **Install Dependencies**
5. **Run Infrastructure Tests**
   ```yaml
   - name: Run infrastructure tests
     run: >-
       uv run pytest tests/infra_tests/
       --cov=infrastructure
       --cov-report=term-missing
       --cov-fail-under=60
       --durations=10
       -m "not requires_ollama"
   ```

#### Job 3: Project Tests (`test-project`)

**Purpose:** Validate project code across Python versions

**Matrix Strategy:**
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

**Steps:**
1. **Checkout Code**
2. **Setup uv** (with caching)
3. **Setup Python Environment** (matrix version)
4. **Install Dependencies**
5. **Run Project Tests**
   ```yaml
   - name: Run project tests
     run: >-
       uv run pytest projects/act_inf_metaanalysis/tests/
       --cov=projects/act_inf_metaanalysis/src
       --cov-report=term-missing
       --cov-fail-under=90
       --durations=10
   ```

#### Job 4: Validate Manuscripts (`validate`)

**Purpose:** Validate manuscript markdown and project imports
**Depends on:** `lint`

**Steps:**
1. **Checkout Code**
2. **Setup uv & Python 3.12**
3. **Validate Manuscript Markdown**
   ```yaml
   - name: Validate manuscript markdown
     run: >-
       uv run python -m infrastructure.validation.cli markdown
       projects/act_inf_metaanalysis/manuscript/
   ```
4. **Verify Project Imports**
   ```yaml
   - name: Verify project imports
     run: uv run python -c "import projects.act_inf_metaanalysis.src; print('OK')"
   ```

#### Job 5: Security Scan (`security`)

**Purpose:** Audit dependencies and scan code for vulnerabilities
**Depends on:** `lint`

**Steps:**
1. **Checkout Code**
2. **Setup uv & Python 3.12**
3. **Dependency Audit**
   ```yaml
   - name: Dependency audit
     run: uv run pip-audit
     continue-on-error: true
   ```
4. **Code Security Scan**
   ```yaml
   - name: Code security scan
     run: >-
       uv run bandit -r
       infrastructure/
       projects/act_inf_metaanalysis/src/
   ```

#### Job 6: Performance Check (`performance`)

**Purpose:** Ensure import times remain acceptable
**Depends on:** `test-infra`, `test-project`

**Steps:**
1. **Checkout Code**
2. **Setup uv & Python 3.12**
3. **Run Import Benchmarks** - Verify infrastructure and project imports complete in under 5 seconds

## Quality Assurance Standards

### Code Quality Gates

**Linting Requirements:**
- **Ruff Check:** All code style rules pass
- **Import Sorting:** Consistent import organization
- **Code Complexity:** Maintainable complexity levels
- **Error Detection:** Static error identification

**Formatting Standards:**
- **Line Length:** 88 characters (Black compatible)
- **Quote Style:** Double quotes preferred
- **Trailing Commas:** Consistent usage
- **Indentation:** 4 spaces

### Testing Standards

**Coverage Requirements:**
- **Minimum Coverage:** 90% for project code
- **Infrastructure Coverage:** 60% minimum
- **Branch Coverage:** Critical paths covered
- **Integration Testing:** End-to-end workflow validation

**Test Execution:**
- **Parallel Testing:** Multiple Python versions simultaneously
- **Isolated Tests:** No cross-test interference
- **Deterministic Results:** Reproducible test outcomes
- **Performance Monitoring:** Test execution timing

### Compatibility Assurance

**Python Version Support:**
- **Primary Version:** Python 3.12 (linting, validation, security, performance)
- **Supported Versions:** Python 3.10, 3.11, 3.12
- **Future Compatibility:** Regular version updates
- **Deprecation Handling:** Graceful version transitions

## Workflow Optimization

### Performance Optimization

**Execution Time Reduction:**
- **Dependency Caching:** `uv` cache utilization
- **Parallel Jobs:** Matrix strategy for concurrent execution
- **Selective Testing:** Targeted test execution
- **Resource Optimization:** Efficient runner utilization

**Resource Management:**
```yaml
# Example: Dependency caching (future enhancement)
- uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
```

### Failure Handling

**Resilient Execution:**
- **Fail-Fast Disabled:** Complete result visibility
- **Concurrency Control:** Prevents resource conflicts
- **Retry Logic:** Automatic retry for transient failures
- **Status Reporting:** Comprehensive failure analysis

## Security Integration

### Automated Security Scanning

**Dependency Security:**
```yaml
# Active in CI security job
- name: Dependency audit
  run: uv run pip-audit
  continue-on-error: true
```

**Code Security:**
```yaml
# Active in CI security job
- name: Code security scan
  run: uv run bandit -r infrastructure/ projects/act_inf_metaanalysis/src/
```

### Secret Management

**Secure Credential Handling:**
- **GitHub Secrets:** Encrypted secret storage
- **Environment Variables:** Secure value injection
- **Access Control:** Minimal permission principles
- **Audit Logging:** Secret access tracking

## Monitoring and Analytics

### Pipeline Metrics

**Performance Tracking:**
- **Build Duration:** Pipeline execution time monitoring
- **Success Rate:** Build success percentage tracking
- **Resource Usage:** CPU and memory utilization
- **Failure Patterns:** Common failure mode analysis

**Quality Metrics:**
- **Coverage Trends:** Test coverage over time
- **Linting Trends:** Code quality evolution
- **Test Performance:** Individual test execution times
- **Compatibility Status:** Cross-version compatibility

### Reporting Integration

**Coverage Reporting:**
```bash
# Coverage is reported via --cov-report=term-missing in CI
# Infrastructure: 60% minimum, Project: 90% minimum
```

**Status Integration:**
- **Branch Protection:** CI status checks required
- **Pull Request Status:** Automated status reporting
- **Commit Status:** Real-time build status
- **Notification Integration:** Slack/email alerts

## Troubleshooting Guide

### Common Pipeline Issues

**Linting Failures:**
```bash
# Local linting reproduction
uv sync
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/
uvx ruff format --check infrastructure/ projects/act_inf_metaanalysis/src/

# Fix common issues
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/ --fix
uvx ruff format infrastructure/ projects/act_inf_metaanalysis/src/
```

**Test Failures:**
```bash
# Local infrastructure test reproduction
uv sync
uv run pytest tests/infra_tests/ -v

# Local project test reproduction
uv run pytest projects/act_inf_metaanalysis/tests/ -v

# Debug specific test
uv run pytest tests/infra_tests/test_specific.py::TestClass::test_method -s --pdb
```

**Coverage Issues:**
```bash
# Local infrastructure coverage analysis
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html
open htmlcov/index.html

# Local project coverage analysis
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-report=html
open htmlcov/index.html

# Check coverage thresholds
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

### Debug Workflows

**Local CI Simulation:**
```bash
# Simulate CI environment
export CI=true
export GITHUB_ACTIONS=true
export GITHUB_WORKFLOW=CI
export GITHUB_RUN_ID=12345

# Run linting
uvx ruff check infrastructure/ projects/act_inf_metaanalysis/src/
uvx ruff format --check infrastructure/ projects/act_inf_metaanalysis/src/

# Run infrastructure tests
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Run project tests
uv run pytest projects/act_inf_metaanalysis/tests/ --cov=projects/act_inf_metaanalysis/src --cov-fail-under=90
```

**Pipeline Debugging:**
```yaml
# Debug workflow (temporary)
jobs:
  debug:
    runs-on: ubuntu-latest
    steps:
      - run: env | sort  # Environment inspection
      - run: python --version
      - run: which python
      - run: pip list
```

## Extension and Enhancement

### Adding New Quality Checks

**Custom Linting Rules:**
```yaml
# Custom quality checks
- name: Custom quality check
  run: uv run python scripts/custom_quality_check.py
```

**Additional Testing:**
```yaml
# Integration testing
- name: Integration tests
  run: uv run pytest tests/integration/ -v
```

### Workflow Customization

**Conditional Execution:**
```yaml
jobs:
  e2e_tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: End-to-end tests
        run: uv run pytest tests/e2e/
```

**Scheduled Workflows:**
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sundays
  workflow_dispatch:     # Manual trigger
```

## Best Practices

### CI/CD Excellence

**Pipeline Design:**
- **Fast Feedback:** Critical checks run first
- **Parallel Execution:** Independent jobs run concurrently
- **Resource Efficiency:** Minimal resource usage
- **Clear Reporting:** Actionable failure information

**Maintenance:**
- **Regular Updates:** Keep actions and tools current
- **Security Reviews:** Regular security assessment
- **Performance Monitoring:** Track and optimize execution time
- **Documentation:** Keep workflow documentation current

### Development Integration

**Developer Experience:**
- **Local Testing:** Easy local pipeline reproduction
- **Clear Errors:** Actionable error messages
- **Fast Iteration:** Quick feedback on changes
- **Debug Support:** Local debugging capabilities

**Collaboration:**
- **Branch Protection:** Quality gates for main branch
- **Review Requirements:** Mandatory code review
- **Status Visibility:** Clear CI status communication
- **Automated Checks:** Consistent quality enforcement

## Future Enhancements

### Advanced CI/CD Features

**Planned Improvements:**
- **Multi-OS Testing:** Windows and macOS compatibility
- **Performance Regression:** Automated performance monitoring
- **Security Scanning:** Advanced vulnerability detection
- **Container Testing:** Docker-based integration testing

**Workflow Enhancements:**
- **Auto-Merge:** Automated merging for routine PRs
- **Release Automation:** Automated versioning and publishing
- **Documentation Deployment:** Automated docs publishing
- **Dependency Updates:** Automated dependency management

## See Also

**Related Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - GitHub integration overview
- [`../../docs/development/CONTRIBUTING.md`](../../docs/development/CONTRIBUTING.md) - Contribution guidelines
- [`../../docs/operational/CI_CD_INTEGRATION.md`](../../docs/operational/CI_CD_INTEGRATION.md) - CI/CD integration guide

**CI/CD Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ruff Documentation](https://beta.ruff.rs/docs/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Codecov Documentation](https://docs.codecov.com/)