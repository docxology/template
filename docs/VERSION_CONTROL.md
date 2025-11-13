# Version Control Best Practices

> **Git workflows and best practices** for the Research Project Template

**Quick Reference:** [Contributing](CONTRIBUTING.md) | [Workflow](WORKFLOW.md) | [Best Practices](BEST_PRACTICES.md)

This guide provides comprehensive best practices for using Git version control with the Research Project Template, including workflows, branching strategies, commit guidelines, and collaboration patterns.

## Overview

Effective version control is essential for maintaining code quality, enabling collaboration, and tracking project evolution. This guide covers Git best practices specifically tailored for research projects using this template.

## Git Workflow Recommendations

### Standard Workflow

**Recommended workflow:**
```bash
# 1. Update local main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Make changes
# ... edit files ...

# 4. Stage changes
git add .

# 5. Commit with clear message
git commit -m "feat: add new feature"

# 6. Push branch
git push origin feature/new-feature

# 7. Create pull request
# ... via GitHub UI ...
```

### Workflow Best Practices

**Follow these principles:**
- Always work on feature branches
- Keep main branch stable
- Commit frequently with clear messages
- Review before merging
- Test before pushing

## Branching Strategies

### Feature Branch Strategy

**Recommended branching:**
```
main (production-ready)
  ├── develop (integration)
  │   ├── feature/new-feature
  │   ├── feature/another-feature
  │   └── fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### Branch Management

**Creating branches:**
```bash
# Feature branch
git checkout -b feature/add-statistics-module

# Bug fix branch
git checkout -b fix/pdf-generation-error

# Documentation branch
git checkout -b docs/update-api-reference
```

**Updating branches:**
```bash
# Update from main
git checkout feature/my-feature
git merge main

# Or rebase
git rebase main
```

**Cleaning up:**
```bash
# Delete local branch after merge
git branch -d feature/merged-feature

# Delete remote branch
git push origin --delete feature/merged-feature
```

## Commit Message Guidelines

### Conventional Commits

**Follow conventional commit format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Tests
- `chore` - Maintenance

**Examples:**
```bash
# Feature
git commit -m "feat(quality): add readability analysis"

# Bug fix
git commit -m "fix(build): resolve PDF generation error"

# Documentation
git commit -m "docs(api): update function documentation"

# Test
git commit -m "test(example): add edge case tests"
```

### Commit Message Best Practices

**Write good commit messages:**
- Use present tense: "add feature" not "added feature"
- Be specific and clear
- Keep subject line under 50 characters
- Include body for complex changes
- Reference issues when applicable

**Good examples:**
```bash
feat(scripts): add parallel PDF generation

Implements parallel building of individual PDFs using
xargs and background processes. Reduces build time
from 35s to 20s for PDF generation stage.

Closes #123
```

**Bad examples:**
```bash
# Too vague
git commit -m "fix stuff"

# Too long subject
git commit -m "fix: resolve issue with PDF generation when using special characters in markdown that causes pandoc to fail"

# Missing context
git commit -m "update"
```

## Tagging and Releases

### Semantic Versioning

**Version format:** `MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes

**Examples:**
- `0.1.0` - Initial release
- `0.2.0` - New features
- `0.2.1` - Bug fixes
- `1.0.0` - Stable release

### Creating Tags

**Tag releases:**
```bash
# Annotated tag (recommended)
git tag -a v0.2.0 -m "Release version 0.2.0"

# Lightweight tag
git tag v0.2.0

# Push tags
git push origin v0.2.0

# Push all tags
git push origin --tags
```

**Tag best practices:**
- Use annotated tags for releases
- Include release notes in tag message
- Tag after successful build
- Tag stable versions only

### Release Process

**Release workflow:**
```bash
# 1. Update version
# Edit pyproject.toml (CHANGELOG.md to be created)

# 2. Commit changes
git commit -m "chore: bump version to 0.2.0"

# 3. Create tag
git tag -a v0.2.0 -m "Release 0.2.0"

# 4. Push everything
git push origin main
git push origin v0.2.0

# 5. Create GitHub release
# ... via GitHub UI ...
```

## Conflict Resolution

### Preventing Conflicts

**Best practices:**
- Update frequently from main
- Keep branches short-lived
- Communicate with team
- Review changes before merging

### Resolving Conflicts

**When conflicts occur:**
```bash
# 1. Update local branch
git checkout feature/my-feature
git merge main

# 2. Resolve conflicts
# Edit conflicted files
# Remove conflict markers

# 3. Stage resolved files
git add resolved-file.py

# 4. Complete merge
git commit -m "merge: resolve conflicts with main"
```

**Conflict markers:**
```python
<<<<<<< HEAD
# Your changes
=======
# Incoming changes
>>>>>>> main
```

**Resolution:**
```python
# Keep both, one, or create new solution
# Final code
```

### Using Merge Tools

**Configure merge tool:**
```bash
# Set merge tool
git config --global merge.tool vimdiff

# Use merge tool
git mergetool
```

## Collaboration Workflows

### Pull Request Process

**Creating pull requests:**
1. **Push branch** - `git push origin feature/my-feature`
2. **Create PR** - Via GitHub UI
3. **Review** - Address feedback
4. **Merge** - After approval

**PR best practices:**
- Clear title and description
- Reference related issues
- Include test results
- Request specific reviewers

### Code Review

**Review checklist:**
- [ ] Code follows style guidelines
- [ ] Tests pass with 100% coverage
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Follows thin orchestrator pattern

**Review comments:**
- Be constructive and specific
- Suggest improvements
- Explain reasoning
- Acknowledge good work

### Collaboration Best Practices

**Working with others:**
- Communicate changes
- Update frequently
- Review thoroughly
- Test before requesting review
- Respond to feedback promptly

## Advanced Git Techniques

### Interactive Rebase

**Clean up commit history:**
```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# Actions:
# pick - Use commit
# reword - Change message
# edit - Modify commit
# squash - Combine with previous
# drop - Remove commit
```

**Use cases:**
- Clean up commit history
- Combine related commits
- Fix commit messages
- Remove accidental commits

### Stashing Changes

**Save work in progress:**
```bash
# Stash changes
git stash

# Stash with message
git stash save "WIP: working on feature"

# List stashes
git stash list

# Apply stash
git stash apply

# Apply and remove
git stash pop

# Drop stash
git stash drop
```

### Cherry-Picking

**Apply specific commits:**
```bash
# Apply commit from another branch
git cherry-pick <commit-hash>

# Apply multiple commits
git cherry-pick <hash1> <hash2>

# Apply range
git cherry-pick <hash1>..<hash2>
```

## Git Configuration

### Recommended Settings

**Configure Git:**
```bash
# User information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Editor
git config --global core.editor "vim"

# Default branch name
git config --global init.defaultBranch main

# Push behavior
git config --global push.default simple

# Rebase on pull
git config --global pull.rebase true
```

### Useful Aliases

**Create aliases:**
```bash
# Short status
git config --global alias.st status

# Last commit
git config --global alias.last "log -1 HEAD"

# Unstage
git config --global alias.unstage "reset HEAD --"

# View graph
git config --global alias.graph "log --oneline --graph --all"
```

## Ignoring Files

### .gitignore

**Template .gitignore:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Output (disposable)
output/
*.pdf
*.tex
*.html

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
*.egg-info/
dist/
build/
```

**Best practices:**
- Ignore generated files
- Ignore IDE files
- Ignore OS files
- Commit .gitignore early

## Troubleshooting

### Common Issues

#### Issue: Accidentally committed sensitive data

**Solution:**
```bash
# Remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch sensitive-file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team)
git push origin --force --all
```

#### Issue: Lost commits

**Solution:**
```bash
# Find lost commits
git reflog

# Recover commit
git checkout <commit-hash>
git checkout -b recovered-branch
```

#### Issue: Wrong branch

**Solution:**
```bash
# Move commits to correct branch
git stash
git checkout correct-branch
git stash pop
git commit
```

## Summary

Version control best practices:

1. **Workflow** - Use feature branches
2. **Commits** - Clear, conventional messages
3. **Branches** - Descriptive names, short-lived
4. **Tags** - Semantic versioning for releases
5. **Collaboration** - Clear PR process, thorough reviews
6. **Configuration** - Proper Git setup
7. **Ignoring** - Comprehensive .gitignore

For more information, see:
- [Contributing Guide](CONTRIBUTING.md) - Contribution workflow
- [Workflow](WORKFLOW.md) - Development process
- [Best Practices](BEST_PRACTICES.md) - General best practices

---

**Related Documentation:**
- [Contributing](CONTRIBUTING.md) - Contribution process
- [Workflow](WORKFLOW.md) - Development workflow
- [Best Practices](BEST_PRACTICES.md) - Code quality practices


