# Troubleshooting Guide

> **Systematic approach** to resolving issues and errors

**Quick Reference:** [FAQ](../../reference/faq.md) | [Common Workflows](../../reference/common-workflows.md) | [Pipeline Orchestration](../../RUN_GUIDE.md)

## Topic-Specific Guides

| Issue Type | Guide | When to Use |
|------------|-------|-------------|
| 🔧 **Environment** | [environment-setup.md](environment-setup.md) | Python, uv, dependencies, matplotlib |
| 🏗️ **Build Tools** | [build-tools.md](build-tools.md) | pandoc, LaTeX, PDF generation |
| 🧪 **Tests** | [test-failures.md](test-failures.md) | pytest, coverage, debugging |
| ❌ **Errors** | [common-errors.md](common-errors.md) | Error message quick reference |
| 🔄 **Recovery** | [recovery-procedures.md](recovery-procedures.md) | Reset, backup, recovery |
| 🤖 **LLM** | [llm-review.md](llm-review.md) | LLM manuscript review issues |

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
    B -->|LLM review| H[LLM Review Guide]
    
    C --> I[environment-setup.md]
    D --> J[build-tools.md]
    E --> K[test-failures.md]
    F --> L[common-errors.md]
    G --> M[recovery-procedures.md]
    H --> N[llm-review.md]
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
| `ModuleNotFoundError` | [Environment](environment-setup.md) |
| `uv sync failed` | [Environment](environment-setup.md) |
| `MPLBACKEND` issues | [Environment](environment-setup.md) |
| `pandoc: command not found` | [Build Tools](build-tools.md) |
| `xelatex: command not found` | [Build Tools](build-tools.md) |
| `LaTeX Error: File not found` | [Build Tools](build-tools.md) |
| `AssertionError` | [Test Failures](test-failures.md) |
| `Coverage below threshold` | [Test Failures](test-failures.md) |
| `Permission denied` | [Common Errors](common-errors.md) |
| `No such file` | [Common Errors](common-errors.md) |
| `Project not discovered` | [Common Errors](common-errors.md) |
| `Stage 4 fails silently` | [Common Errors](common-errors.md) |
| `Config warning spam` | [Common Errors](common-errors.md) |
| `Reference shows ??` | [Common Errors](common-errors.md) |
| `Figure not found` | [Common Errors](common-errors.md) |

---

## Getting Help

**Before asking for help, collect:**

1. Error messages (full output)
2. Environment (OS, Python version)
3. Steps to reproduce
4. What you've tried

**Resources:**

- [FAQ](../../reference/faq.md) - Common questions
- [GitHub Issues](https://github.com/docxology/template/issues) - Report bugs

---

## See Also

- [FAQ](../../reference/faq.md) - Frequently asked questions
- [Build System](../../RUN_GUIDE.md) - Build system details
- [Common Workflows](../../reference/common-workflows.md) - Workflow troubleshooting
- [Performance Optimization](../config/performance-optimization.md) - Performance issues
- [Checkpoint and Resume](../config/checkpoint-resume.md) - Checkpoint system
