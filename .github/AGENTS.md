# GitHub Integration

## Overview

The `.github/` directory contains GitHub-specific configuration and automation for the Research Project Template. This includes continuous integration workflows, issue templates, and other GitHub integrations that ensure code quality and collaborative development.

## Directory Structure

```
.github/
├── AGENTS.md                    # This technical documentation
└── workflows/
    ├── ci.yml                   # Continuous integration pipeline
    └── AGENTS.md               # CI/CD workflow documentation
```

## Continuous Integration (CI/CD)

### CI Pipeline (`workflows/ci.yml`)

**Comprehensive CI/CD pipeline ensuring code quality and compatibility:**

**Pipeline Triggers:**
```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

**Concurrency Control:**
```yaml
concurrency:
  group: ci-${{ github.ref }}-${{ github.workflow }}
  cancel-in-progress: true
```

**Pipeline Jobs:**

#### 1. Lint Job
**Code Quality Enforcement:**
- **Python Version:** 3.10
- **Dependencies:** uv for package management
- **Linting:** Ruff for code style and formatting
- **Scope:** Project directory (`project/`)

**Steps:**
1. **Checkout:** Get repository code
2. **Setup Python:** Install Python 3.10
3. **Install uv:** Package manager for dependencies
4. **Sync Dependencies:** Install project dependencies
5. **Ruff Lint:** Check code style and quality
6. **Ruff Format:** Verify code formatting

#### 2. Test Job
**Cross-Version Testing:**
- **Python Versions:** 3.10, 3.11
- **Matrix Strategy:** Test against multiple Python versions
- **Fail-Fast:** false (run all combinations)

**Steps:**
1. **Checkout:** Get repository code
2. **Setup Python:** Install specified Python version
3. **Install uv:** Package manager setup
4. **Sync Dependencies:** Install test dependencies
5. **Run Tests:** Execute test suite with coverage
6. **Upload Coverage:** Send coverage to codecov

### Quality Gates

**Linting Standards:**
- **Ruff Rules:** Comprehensive Python code quality
- **Import Sorting:** Consistent import organization
- **Code Formatting:** Black-compatible formatting
- **Type Checking:** Basic type annotation validation

**Testing Requirements:**
- **Coverage:** Minimum coverage thresholds
- **Python Versions:** Compatibility with 3.10+
- **Test Isolation:** No test interference
- **Deterministic Results:** Reproducible test outcomes

## Workflow Configuration

### Branch Protection

**Main Branch Protection (Recommended):**
```yaml
# GitHub Branch Protection Rules
required_status_checks:
  - lint
  - tests (3.10)
  - tests (3.11)

required_pull_request_reviews:
  required_approving_review_count: 1

restrictions: null
```

### Issue Templates

**Recommended Issue Templates:**
- **Bug Report:** Structured bug reporting with reproduction steps
- **Feature Request:** Feature proposals with use cases
- **Documentation:** Documentation improvements and corrections

### Pull Request Template

**Recommended PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security enhancement

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Coverage requirements met
- [ ] Manual testing completed

## Checklist
- [ ] Code follows established patterns
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Security considerations addressed
```

## CI/CD Best Practices

### Pipeline Optimization

**Performance Considerations:**
- **Parallel Jobs:** Matrix testing for multiple Python versions
- **Caching:** Dependency caching for faster builds
- **Fail-Fast:** Disabled to get complete test results
- **Concurrency:** Cancel outdated runs to save resources

**Resource Management:**
```yaml
# Example: Dependency caching
- uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
```

### Security Considerations

**Secure CI/CD:**
- **Dependency Scanning:** Automated vulnerability detection
- **Secret Management:** Secure credential handling
- **Container Security:** Safe Docker image usage
- **Access Control:** Minimal required permissions

**Security Scanning Integration:**
```yaml
# Example: Security scanning
- name: Security audit
  run: |
    uv run safety check
    uv run bandit -r src/
```

## Development Workflow Integration

### Automated Quality Checks

**Pre-Merge Validation:**
- **Code Style:** Automatic formatting and linting
- **Type Checking:** Static type analysis
- **Test Coverage:** Coverage report generation
- **Documentation:** Build verification

**Feedback Integration:**
- **PR Comments:** Automated review feedback
- **Status Checks:** Clear pass/fail indicators
- **Coverage Reports:** Detailed coverage analysis
- **Performance Metrics:** Build time and resource usage

### Continuous Deployment

**Deployment Pipeline (Future):**
```yaml
# Example: Deployment workflow
name: Deploy
on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: echo "Deployment logic here"
```

## Monitoring and Analytics

### Pipeline Metrics

**Key Metrics to Track:**
- **Build Success Rate:** Percentage of successful builds
- **Build Duration:** Average time for pipeline completion
- **Test Coverage:** Code coverage percentage over time
- **Failure Patterns:** Common failure modes and causes

**Analytics Integration:**
```yaml
# Example: Metrics collection
- name: Collect metrics
  run: |
    echo "build_duration=$(( $(date +%s) - $(date +%s -d '1 hour ago') ))" >> $GITHUB_OUTPUT
    echo "test_count=$(find . -name 'test_*.py' | wc -l)" >> $GITHUB_OUTPUT
```

### Alerting and Notifications

**Failure Notifications:**
- **Email Alerts:** Build failure notifications
- **Slack Integration:** Real-time status updates
- **Issue Creation:** Automatic issue creation for failures
- **Escalation:** Priority-based alerting

## Troubleshooting

### Common CI/CD Issues

**Linting Failures:**
```bash
# Fix linting issues
uv run ruff check . --fix
uv run ruff format .
```

**Test Failures:**
```bash
# Run tests locally
uv run pytest tests/ -v

# Debug specific test
uv run pytest tests/test_specific.py::TestClass::test_method -s
```

**Coverage Issues:**
```bash
# Check coverage locally
uv run pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

**Python Version Issues:**
```bash
# Test with specific Python version
python3.10 -m pytest tests/
python3.11 -m pytest tests/
```

### Debug Workflows

**Local CI Simulation:**
```bash
# Simulate CI environment locally
export CI=true
export GITHUB_ACTIONS=true

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run tests with coverage
uv run pytest tests/ --cov=src
```

## Extension and Customization

### Adding New Workflows

**Workflow Template:**
```yaml
name: Custom Workflow

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  custom_job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Custom step
        run: echo "Custom workflow logic"
```

### Custom Actions

**Creating Custom Actions:**
```yaml
# .github/actions/custom-action/action.yml
name: 'Custom Action'
description: 'Description of custom action'

inputs:
  input_name:
    description: 'Input description'
    required: true

runs:
  using: 'composite'
  steps:
    - run: echo "Custom action logic"
      shell: bash
```

## Security and Compliance

### Security Scanning

**Automated Security Checks:**
```yaml
# Security scanning job
security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run security scan
      uses: securecodewarrior/github-action-security-scan@v1
```

### Compliance Automation

**License and Dependency Compliance:**
```yaml
# Dependency compliance check
- name: Check licenses
  run: |
    uv run pip-licenses --format=markdown > licenses.md
    # Check for incompatible licenses
```

## Future Enhancements

### Planned Improvements

**Enhanced CI/CD:**
- **Multi-OS Testing:** Windows and macOS compatibility
- **Performance Benchmarking:** Automated performance regression detection
- **Container Testing:** Docker-based integration testing
- **Security Scanning:** Advanced vulnerability detection

**Workflow Automation:**
- **Auto-Merge:** Automated merging for routine changes
- **Release Automation:** Automated version bumping and tagging
- **Documentation Deployment:** Automated documentation publishing
- **Dependency Updates:** Automated dependency management

## See Also

**Related Documentation:**
- [`../../docs/development/CONTRIBUTING.md`](../../docs/development/CONTRIBUTING.md) - Contribution guidelines
- [`../../docs/operational/CI_CD_INTEGRATION.md`](../../docs/operational/CI_CD_INTEGRATION.md) - CI/CD integration guide
- [`../../AGENTS.md`](../../AGENTS.md) - System overview

**CI/CD Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ruff Documentation](https://beta.ruff.rs/docs/)
- [uv Documentation](https://github.com/astral-sh/uv)