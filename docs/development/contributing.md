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

## 🏗️ **Development Setup**

### 1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/template.git
cd template
```

### 2. **Install Dependencies**
```bash
# Create virtual environment
uv run python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. **Run Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## 📋 **Contribution Guidelines**

### 🧪 **Testing Requirements**
- **90% minimum coverage** for project code, **60% minimum** for infrastructure
- **All tests must pass** before any changes are accepted
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
- **Include examples** for new functionality

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
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. **Make Your Changes**
- **Implement the feature/fix**
- **Add/update tests**
- **Update documentation**
- **Ensure all tests pass**

### 3. **Test Your Changes**
```bash
# Run the full test suite
pytest

# Check coverage
pytest --cov=src --cov-report=html

# Test the build pipeline
uv run python scripts/execute_pipeline.py --core-only
```

### 4. **Submit a Pull Request**
- **Clear description** of what the PR accomplishes
- **Reference any issues** being addressed
- **Include screenshots** if UI changes
- **Describe testing** performed

## 🎯 **What We're Looking For**

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
