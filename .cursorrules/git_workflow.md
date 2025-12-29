# Git Workflow and Commit Standards

## Overview

Standardized Git workflow ensures clean history, easy collaboration, and reliable deployments. All changes must follow these standards.

## Branch Strategy

### Main Branches

- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features

### Feature Branches

```bash
# ✅ GOOD: Descriptive feature branches
git checkout -b feature/add-literature-search
git checkout -b feature/improve-pdf-validation
git checkout -b bugfix/fix-rendering-crash

# ❌ BAD: Generic or unclear names
git checkout -b my-changes
git checkout -b fix
git checkout -b update
```

### Branch Naming Convention

```
<type>/<description>

Types:
- feature/     - New functionality
- bugfix/      - Bug fixes
- hotfix/      - Critical production fixes
- refactor/    - Code refactoring
- docs/        - Documentation changes
- test/        - Testing improvements
- ci/          - CI/CD changes
- chore/       - Maintenance tasks
```

## Commit Standards

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(literature): add arXiv search support` |
| `fix` | Bug fix | `fix(pdf): resolve rendering crash on empty sections` |
| `docs` | Documentation | `docs(api): update LLM integration guide` |
| `style` | Code style | `style(core): format imports with isort` |
| `refactor` | Code refactor | `refactor(validation): simplify markdown parser` |
| `test` | Testing | `test(infrastructure): add coverage for edge cases` |
| `chore` | Maintenance | `chore(deps): update numpy to 1.24.0` |
| `perf` | Performance | `perf(search): optimize query caching` |
| `ci` | CI/CD | `ci(actions): add pre-commit hooks` |
| `build` | Build system | `build(deps): add uv for dependency management` |

### Scopes

- **infrastructure** - Infrastructure modules
- **literature** - Literature search functionality
- **llm** - LLM integration
- **rendering** - Document rendering
- **validation** - Quality validation
- **core** - Core utilities
- **scripts** - Entry point scripts
- **tests** - Test suite
- **docs** - Documentation
- **project** - Project-specific code

### Examples

```bash
# ✅ GOOD: Clear, descriptive commits
feat(literature): add Semantic Scholar API integration

- Implement Semantic Scholar source adapter
- Add rate limiting for API calls
- Include citation count extraction
- Tests: 95% coverage achieved

fix(rendering): resolve LaTeX compilation timeout

Timeout occurred when processing large manuscripts.
Increased default timeout from 30s to 120s.
Added configurable timeout via RENDERING_TIMEOUT env var.

Closes #123

docs(readme): update installation instructions

Updated Python version requirements and added
macOS/Ubuntu installation commands for pandoc.

test(validation): add edge case coverage for broken links

Added tests for:
- Invalid URLs
- Network timeouts
- SSL certificate issues
- Response status codes

refactor(core): extract common validation logic

Created shared validation utilities in core/validators.py
to reduce code duplication across modules.

BREAKING CHANGE: ValidationError now requires context parameter
```

### Commit Message Guidelines

#### Subject Line
- **Limit to 50 characters**
- **Start with lowercase** (except proper nouns)
- **No period** at the end
- **Imperative mood** ("add" not "added")

#### Body (Optional)
- **Separate from subject** with blank line
- **Explain what and why**, not how
- **Wrap at 72 characters**
- **Use bullet points** for lists

#### Footer (Optional)
- **Breaking changes**: `BREAKING CHANGE: description`
- **Issue references**: `Closes #123`, `Fixes #456`
- **Co-authors**: `Co-authored-by: Name <email>`

## Pull Request Standards

### PR Template

```markdown
## Description

Brief description of changes and why they're needed.

## Type of Change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing

### Test Coverage
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Coverage meets requirements (90% project, 60% infra)

### Manual Testing
- [ ] Tested locally
- [ ] Tested in CI/CD
- [ ] Edge cases verified

## Checklist

- [ ] Code follows style guidelines (Black, isort, flake8)
- [ ] Type hints added to all public APIs
- [ ] Documentation updated (AGENTS.md, README.md)
- [ ] No breaking changes without migration guide
- [ ] Commit messages follow standards
- [ ] PR description is clear and complete

## Breaking Changes

List any breaking changes and migration instructions:

- `OldAPI.function()` → `NewAPI.function()` - update imports
- Environment variable `OLD_VAR` → `NEW_VAR` - update configs

## Related Issues

Closes #123
Fixes #456
```

### PR Review Process

1. **Automated Checks** - CI must pass
2. **Code Review** - At least one reviewer required
3. **Testing** - Reviewer tests functionality
4. **Style** - Code follows .cursorrules standards
5. **Documentation** - AGENTS.md/README.md updated

## Development Workflow

### Daily Development

```bash
# 1. Start from main/develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/add-new-functionality

# 3. Make changes with good commits
git add .
git commit -m "feat(core): add new validation function

Add validate_input() function to core/validators.py
- Validates string inputs for length and format
- Raises ValidationError with context
- Includes comprehensive tests"

# 4. Push and create PR
git push origin feature/add-new-functionality
```

### Rebasing

```bash
# Keep branch up-to-date
git fetch origin
git rebase origin/develop

# Resolve conflicts if any
# Test that everything still works
git push --force-with-lease
```

### Squashing Commits

```bash
# Interactive rebase to clean history
git rebase -i HEAD~5

# Choose 'squash' for commits to combine
# Edit commit message to follow standards
```

## Git Configuration

### Global Config

```bash
# Set user details
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch
git config --global init.defaultBranch main

# Enable automatic line ending handling
git config --global core.autocrlf input  # Linux/Mac
git config --global core.autocrlf true   # Windows

# Set default editor
git config --global core.editor "code --wait"
```

### Repository Config

```bash
# In repository root
git config core.hooksPath .githooks  # If using custom hooks
```

## Custom Git Hooks

### Pre-commit Hook

```bash
#!/bin/bash
# .githooks/pre-commit

echo "Running pre-commit checks..."

# Run formatting
black --check . || exit 1
isort --check-only . || exit 1

# Run linting
flake8 . || exit 1

# Run tests
python -m pytest tests/ -x --tb=short || exit 1

echo "All checks passed!"
```

### Commit-msg Hook

```bash
#!/bin/bash
# .githooks/commit-msg

commit_msg_file=$1
commit_msg=$(cat $commit_msg_file)

# Check commit message format
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|test|chore|perf|ci|build)(\(.+\))?: .{1,50}$"; then
    echo "ERROR: Invalid commit message format"
    echo "Expected: type(scope): description (50 chars max)"
    echo "Example: feat(api): add new search endpoint"
    exit 1
fi
```

## Repository Maintenance

### Cleaning Up Branches

```bash
# Delete merged branches
git branch --merged | grep -v "\*" | grep -v main | grep -v develop | xargs git branch -d

# Delete remote branches
git branch -r --merged | grep -v main | grep -v develop | sed 's/origin\///' | xargs git push origin --delete
```

### Repository Health

```bash
# Check repository status
git status
git log --oneline -10

# Clean untracked files
git clean -fd

# Verify no large files
find . -size +50M | cat
```

## Git Best Practices

### Do's ✅

- ✅ **Write clear commit messages** following the format
- ✅ **Keep commits atomic** (one logical change per commit)
- ✅ **Use feature branches** for all development
- ✅ **Rebase regularly** to stay up-to-date
- ✅ **Squash commits** before merging
- ✅ **Write descriptive PR descriptions**
- ✅ **Test before pushing** (run full test suite)
- ✅ **Use interactive rebase** to clean history
- ✅ **Follow branch naming conventions**
- ✅ **Reference issues** in commits and PRs

### Don'ts ❌

- ❌ **Force push** to shared branches (`main`, `develop`)
- ❌ **Merge with merge commits** (use rebase instead)
- ❌ **Commit directly to main/develop**
- ❌ **Leave merge conflicts** unresolved
- ❌ **Push broken code** that fails CI
- ❌ **Use generic commit messages** ("update", "fix", "changes")
- ❌ **Include unrelated changes** in commits
- ❌ **Ignore failing tests** in PRs
- ❌ **Skip code reviews** for significant changes
- ❌ **Leave stale branches** after merging

## Integration with CI/CD

### GitHub Actions Workflow

```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov black isort flake8 mypy

      - name: Check formatting
        run: |
          black --check .
          isort --check-only .

      - name: Lint
        run: flake8 .

      - name: Type check
        run: mypy .

      - name: Test
        run: pytest --cov=. --cov-fail-under=70

      - name: Build
        run: python -m build
```

### Protected Branches

Configure branch protection:

- **Require PR reviews** before merging
- **Require status checks** to pass
- **Include administrators** in restrictions
- **Require up-to-date branches** before merging
- **Restrict force pushes** to maintainers only

## Troubleshooting

### Common Git Issues

**Merge Conflicts:**
```bash
# Abort merge
git merge --abort

# Rebase instead of merge
git fetch origin
git rebase origin/main

# Resolve conflicts, then continue
git add resolved_files
git rebase --continue
```

**Lost Commits:**
```bash
# Find lost commits
git reflog

# Restore from reflog
git checkout <commit-hash>
```

**Large Files:**
```bash
# Remove large files from history
git filter-branch --tree-filter 'rm -f large-file.dat' HEAD

# Use Git LFS for large files
git lfs install
git lfs track "*.pdf"
```

## See Also

- [code_style.md](code_style.md) - Code formatting standards
- [testing_standards.md](testing_standards.md) - Testing patterns and coverage
- [infrastructure_modules.md](infrastructure_modules.md) - Module development standards
- [documentation_standards.md](documentation_standards.md) - Documentation writing guide
- [../docs/best-practices/VERSION_CONTROL.md](../docs/best-practices/VERSION_CONTROL.md) - Version control best practices
- [../docs/operational/CI_CD_INTEGRATION.md](../docs/operational/CI_CD_INTEGRATION.md) - CI/CD integration guide
