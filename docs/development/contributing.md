# 🤝 Contributing to Research Project Template

Thank you for your interest in improving this template! This document provides guidelines for contributing to make the template better for everyone.

## 🎯 **How to Contribute**

### 🚀 **Using the Template**
The best way to contribute is to **use this template** for your own research projects and provide feedback on what works well and what could be improved.

### 🐛 **Reporting Issues**
- **Bug reports** help us fix problems
- **Feature requests** help us understand what's needed
- **Documentation improvements** help other users

### 🔧 **Code Contributions**
- **Bug fixes** for any issues you encounter
- **features** that would benefit all users
- **Improvements** to existing functionality
- **Tests** to ensure code quality

### 🔎 **Before Picking Work**

Start with the contributor strategy guide:
[`contribution-map.md`](contribution-map.md). It explains how to check whether
an idea is already built, partially built, proposed, or absent before writing
code. Use that overlap check to decide whether the contribution should be a doc
fix, focused test, small bugfix, skill/plugin update, or maintainer-aligned core
change.

## 🏗️ **Development Setup**

### 1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/template.git
cd template
git remote add upstream https://github.com/docxology/template.git
```

Before changing files, inspect `git status --short --branch`, the upstream
relationship, and any nested checkout state. Do not reset, clean, or overwrite
an existing dirty worktree to make setup easier.

### 2. **Install Dependencies**
```bash
uv sync
```

### 3. **Run Tests**
```bash
# Focused local contracts; see ../../.github/AGENTS.md for exact hosted CI.
uv sync
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_code_project --project-only
```

Run one project test directory per pytest process. Collecting multiple public
projects in one process can collide on the shared `tests.conftest` package;
use the stage runner's isolated all-public matrix when broad coverage is
needed.

## 📋 **Contribution Guidelines**

### 🧪 **Testing Requirements**
- **90% minimum coverage** for project code, **60% minimum** for infrastructure
- **All applicable gates must pass** before changes are accepted; report
  `failed`, `blocked`, `not run`, and capability-driven skips explicitly
- **Add tests** for new functionality
- **Update tests** when fixing bugs

### 📝 **Code Style**
- **Follow PEP 8** for Python code
- **Use meaningful names** for variables and functions
- **Add docstrings** for all public functions
- **Keep functions focused** and single-purpose

### 📚 **Documentation**
- **Update README.md** if adding features
- **Add docstrings** to new functions
- **Update relevant guides** in the docs/ directory
- **Capture rationale in the right place**: use [`docs/rules/memory_and_decision_records.md`](../rules/memory_and_decision_records.md) for `WHY:` comments, ADRs, project plans, failure notes, local memory, and negative-control expectations
- **Include examples** for new functionality
- **Agent `SKILL.md`:** If you add or change `infrastructure/**/SKILL.md`, run `uv run python -m infrastructure.skills write` (creates or updates `.cursor/skill_manifest.json` at the repo root) and commit that file if it changed; validate with `uv run python -m infrastructure.skills check`

### 🔄 **Commit Messages**
Use clear, descriptive commit messages:
```
feat: add automated figure generation
fix: resolve PDF rendering issue with special characters
docs: update installation instructions for Windows
test: add coverage for new statistical functions
```

## 🚀 **Making Changes**

### 1. **Create a Branch**
```bash
git fetch upstream
git switch -c feature/your-feature-name upstream/main
```

If you already have local work, preserve it first and resolve overlap
deliberately. Do not use a destructive reset or checkout to force the branch
onto upstream state.

### 2. **Make Your Changes**
- **Implement the feature/fix**
- **Add/update tests**
- **Update documentation**
- **Ensure all tests pass**

### 3. **Test Your Changes**
```bash
# Run the full test suite
uv run python scripts/pipeline/stage_01_test.py --project templates/{name}

# Run the coverage-bearing infrastructure gate
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full

# Test the build pipeline
uv run python scripts/runner/execute_pipeline.py --project templates/{name} --core-only

# Documentation, confidentiality, generated-artifact, and no-stand-in gates
uv run python scripts/audit/lint_docs.py --quiet
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory --max-dependency-replacements 0
```

The target project's own `AGENTS.md` may require additional analysis,
rendering, provenance, scholarship, or publication-audit gates. A green core
pipeline does not by itself establish scientific validity, semantic
accessibility, release authority, or publication.

### 4. **Submit a Pull Request**
- **Clear description** of what the PR accomplishes
- **Reference any issues** being addressed
- **Include screenshots** if UI changes
- **Describe testing** performed
- **Distinguish results** that passed from gates that were skipped, blocked,
  unavailable, or not run
- **Do not include generated/local evidence** merely to make the PR appear
  current; regenerate only source-owned public artifacts permitted by the
  repository's tracked-artifact policy

## 🎯 **What We're Looking For**

Check [`contribution-map.md`](contribution-map.md) before starting. It captures
the current small, mergeable contribution shapes and the areas that need
maintainer alignment first.

### 🌟 **High Priority**
- **Bug fixes** that affect template usability
- **Documentation improvements** for clarity
- **Test coverage** improvements
- **Performance optimizations**

### 🔧 **Medium Priority**
- **New utility functions** that benefit many users
- **error handling** and user feedback
- **Additional output formats** (HTML, Word, etc.)
- **Integration examples** with popular tools

### 💡 **Low Priority**
- **Cosmetic changes** that don't improve functionality
- **Very specific features** that only benefit niche use cases
- **Breaking changes** without clear migration path

## 🚫 **What We're NOT Looking For**

- **Breaking changes** to the core architecture
- **Dependencies** on proprietary software
- **Platform-specific code** that doesn't work cross-platform
- **Changes** that reduce test coverage

## 🤝 **Getting Help**

### 💬 **Questions?**
- **Open an issue** with the "question" label
- **Check existing issues** for similar questions
- **Review the documentation** in the docs/ directory

### 🔍 **Stuck on Something?**
- **Describe what you're trying to do**
- **Include error messages** and stack traces
- **Share your environment** (OS, Python version, etc.)
- **Provide minimal reproduction steps**

## 📚 **Resources**

- **[`../../.github/README.md`](../../.github/README.md)** - GitHub Actions, branch protection, local CI mirror
- **[`../../.github/AGENTS.md`](../../.github/AGENTS.md)** - exact CI jobs, matrices, and local parity commands
- **[`contribution-map.md`](contribution-map.md)** - Overlap checks and practical contribution strategy
- **[`../core/architecture.md`](../core/architecture.md)** - System design overview
- **[`../core/workflow.md`](../core/workflow.md)** - Development workflow guide
- **[`markdown-template-guide.md`](../usage/markdown-template-guide.md)** - Writing and formatting guide
- **[`examples.md`](../usage/examples.md)** - Usage examples and customization
- **[`README.md`](README.md)** - Project overview and quick start
- **[`thin-orchestrator-summary.md`](../architecture/thin-orchestrator-summary.md)** - Architecture implementation details

## 🎉 **Thank You!**

Every contribution, no matter how small, helps make this template better for researchers and developers worldwide. Thank you for your time and effort!

---

**Happy contributing! 🚀**
