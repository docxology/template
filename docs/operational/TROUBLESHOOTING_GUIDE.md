# Troubleshooting Guide

> **Systematic approach** to resolving issues and errors

**Quick Reference:** [FAQ](../reference/FAQ.md) | [Common Workflows](../reference/COMMON_WORKFLOWS.md) | [Build System](BUILD_SYSTEM.md)

## Topic-Specific Guides

| Issue Type | Guide | When to Use |
|------------|-------|-------------|
| 🔧 **Environment** | [troubleshooting/ENVIRONMENT_SETUP.md](troubleshooting/ENVIRONMENT_SETUP.md) | Python, uv, dependencies, matplotlib |
| 🏗️ **Build Tools** | [troubleshooting/BUILD_TOOLS.md](troubleshooting/BUILD_TOOLS.md) | pandoc, LaTeX, PDF generation |
| 🧪 **Tests** | [troubleshooting/TEST_FAILURES.md](troubleshooting/TEST_FAILURES.md) | pytest, coverage, debugging |
| ❌ **Errors** | [troubleshooting/COMMON_ERRORS.md](troubleshooting/COMMON_ERRORS.md) | Error message quick reference |
| 🔄 **Recovery** | [troubleshooting/RECOVERY_PROCEDURES.md](troubleshooting/RECOVERY_PROCEDURES.md) | Reset, backup, recovery |

**Specialized Guides:**

- [LLM Review Troubleshooting](LLM_REVIEW_TROUBLESHOOTING.md) - LLM-specific issues
- [Checkpoint and Resume](CHECKPOINT_RESUME.md) - Checkpoint system
- [Performance Optimization](PERFORMANCE_OPTIMIZATION.md) - Performance issues

---

## Quick Diagnostic Flowchart

```mermaid
graph TD
    A[Issue Detected] --> B{What's failing?}
    B -->|Dependencies/Imports| C[Environment Guide]
    B -->|PDF/LaTeX| D[Build Tools Guide]
    B -->|Tests| E[Test Failures Guide]
    B -->|Unknown error| F[Common Errors Guide]
    B -->|Everything broken| G[Recovery Procedures]
    
    C --> H[troubleshooting/ENVIRONMENT_SETUP.md]
    D --> I[troubleshooting/BUILD_TOOLS.md]
    E --> J[troubleshooting/TEST_FAILURES.md]
    F --> K[troubleshooting/COMMON_ERRORS.md]
    G --> L[troubleshooting/RECOVERY_PROCEDURES.md]
```

---

## Systematic Troubleshooting Approach

### Step 1: Gather Information

```bash
# System information
python --version && uv --version
pandoc --version && xelatex --version

# Environment
env | grep -E "AUTHOR|PROJECT|DOI"

# Dependency status
uv tree
```

### Step 2: Reproduce the Issue

1. **Clean state** - Start from clean output directory
2. **Isolate** - Run individual components
3. **Document** - Record exact steps
4. **Verify** - Confirm consistent behavior

### Step 3: Check Common Causes

| Issue | Likely Cause |
|-------|--------------|
| Import errors | Missing dependencies |
| Build failures | Missing tools (pandoc/LaTeX) |
| Test failures | Configuration or data issues |
| PDF issues | LaTeX packages or paths |
| Permission errors | File system access |

### Step 4: Apply Fixes

1. Start simple - try easiest fixes first
2. One change at a time - isolate what works
3. Test after each fix - verify resolution
4. Document solution - note what worked

---

## Error Message Quick Lookup

| Error | → Go To |
|-------|---------|
| `ModuleNotFoundError` | [Environment](troubleshooting/ENVIRONMENT_SETUP.md) |
| `uv sync failed` | [Environment](troubleshooting/ENVIRONMENT_SETUP.md) |
| `command not found` | [Build Tools](troubleshooting/BUILD_TOOLS.md) |
| `LaTeX Error` | [Build Tools](troubleshooting/BUILD_TOOLS.md) |
| `AssertionError` | [Test Failures](troubleshooting/TEST_FAILURES.md) |
| `Coverage below` | [Test Failures](troubleshooting/TEST_FAILURES.md) |
| `Permission denied` | [Common Errors](troubleshooting/COMMON_ERRORS.md) |

---

## Getting Help

**Before asking for help, collect:**

1. Error messages (full output)
2. Environment (OS, Python version)
3. Steps to reproduce
4. What you've tried

**Resources:**

- [FAQ](../reference/FAQ.md) - Common questions
- [GitHub Issues](https://github.com/docxology/template/issues) - Report bugs

---

**Related Documentation:**

- [FAQ](../reference/FAQ.md) - Frequently asked questions
- [Build System](BUILD_SYSTEM.md) - Build system details
- [Common Workflows](../reference/COMMON_WORKFLOWS.md) - Workflow troubleshooting
