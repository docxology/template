# ⚡ Quick Start Cheatsheet

> **One-page reference** for essential commands and workflows

**New to the template?** Start with **[Getting Started Guide](GETTING_STARTED.md)** | **[FAQ](FAQ.md)**

## 🚀 Essential Commands

### Setup Commands
```bash
# Clone template
git clone https://github.com/docxology/template.git

# Install dependencies
uv sync

# Run complete build
./repo_utilities/render_pdf.sh
```

### Daily Workflow Commands
```bash
# Clean outputs
./repo_utilities/clean_output.sh

# Run tests only
pytest tests/ --cov=src --cov-report=html

# Generate figures only
python3 scripts/example_figure.py

# Validate markdown
python3 repo_utilities/validate_markdown.py

# Open manuscript
./repo_utilities/open_manuscript.sh
```

### Build Pipeline Commands
```bash
# Complete from-scratch build
./generate_pdf_from_scratch.sh

# Quick build (no clean)
./repo_utilities/render_pdf.sh

# Validate PDFs
python3 repo_utilities/validate_pdf_output.py
```

## 📁 Directory Structure Quick Reference

```
template/
├── src/              # Core business logic (100% tested)
├── tests/            # Test suite (100% coverage required)
├── scripts/          # Thin orchestrators (use src/ methods)
├── manuscript/       # Research sections (generate PDFs)
├── docs/             # Documentation (25+ guides)
├── output/           # Generated files (disposable)
└── repo_utilities/   # Build tools (generic)
```

## 🔧 Common Workflows

### Create a New Document Section
```bash
# 1. Create markdown file
vim manuscript/07_new_section.md

# 2. Add content with section label
echo "# New Section {#sec:new_section}" > manuscript/07_new_section.md

# 3. Rebuild
./repo_utilities/render_pdf.sh
```

### Add a New Figure
```bash
# 1. Create script in scripts/
vim scripts/my_figure.py

# 2. Import from src/ (thin orchestrator pattern)
# from example import calculate_average

# 3. Generate and save to output/figures/
# 4. Reference in manuscript:
# \includegraphics{../output/figures/my_figure.png}
```

### Add New Source Code
```bash
# 1. Create module
vim src/my_module.py

# 2. Create tests (100% coverage required)
vim tests/test_my_module.py

# 3. Run tests
pytest tests/test_my_module.py --cov=src.my_module

# 4. Use in scripts (thin orchestrator pattern)
# from my_module import my_function
```

### Fix Test Coverage
```bash
# 1. Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# 2. Find missing lines (marked with ">>>>>")
# 3. Add tests for uncovered code
# 4. Re-run until 100%
```

## 📝 Quick Syntax Reference

### Cross-References
```markdown
# Section reference
See Section \ref{sec:methodology}

# Equation reference
From Equation \eqref{eq:objective}

# Figure reference
Figure \ref{fig:convergence_plot} shows...
```

### Equations
```markdown
\begin{equation}\label{eq:my_equation}
f(x) = x^2 + 2x + 1
\end{equation}

Reference it: \eqref{eq:my_equation}
```

### Figures
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/my_figure.png}
\caption{My figure caption}
\label{fig:my_figure}
\end{figure}

Reference it: \ref{fig:my_figure}
```

## 🐛 Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| **Tests fail** | `pytest tests/ -v` to see details |
| **Coverage < 100%** | `pytest --cov=src --cov-report=term-missing` |
| **Import errors** | Check `PYTHONPATH` or use `uv run` |
| **PDF fails** | Check `pandoc --version` and `xelatex --version` |
| **Figures missing** | Run `python3 scripts/*.py` first |
| **References show ??** | Check label spelling and existence |

## 📊 Key Metrics

**Current System Status:**
- **Tests**: 320/322 passing (99.4%)
- **Coverage**: 81.90% (exceeds 70%)
- **Build Time**: 75 seconds
- **PDFs Generated**: 13 sections
- **Documentation**: 25+ comprehensive guides

**See [Build System](BUILD_SYSTEM.md) for details**

## 🎯 Quick Decision Tree

**I want to...**

- **Just write documents** → [Getting Started Guide](GETTING_STARTED.md)
- **Add figures** → [Intermediate Usage](INTERMEDIATE_USAGE.md)
- **Write tests** → [Advanced Usage](ADVANCED_USAGE.md)
- **Understand architecture** → [Architecture](ARCHITECTURE.md)
- **Contribute** → [Contributing](CONTRIBUTING.md)
- **Fix a problem** → [FAQ](FAQ.md)

## 🔗 Essential Links

- **[Complete Guide](HOW_TO_USE.md)** - All 12 skill levels
- **[Common Workflows](COMMON_WORKFLOWS.md)** - Step-by-step recipes
- **[FAQ](FAQ.md)** - Common questions
- **[Glossary](GLOSSARY.md)** - Terms and definitions
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - All docs

## 💡 Pro Tips

1. **Always run tests first**: `pytest tests/` before building
2. **Use thin orchestrator pattern**: Scripts import from `src/`
3. **100% coverage required**: No exceptions for `src/` code
4. **Check validation**: Run `validate_markdown.py` before PDF build
5. **Clean outputs**: Use `clean_output.sh` for fresh builds
6. **Read build logs**: Check `output/pdf/*_compile.log` for errors

---

**Need more details?** See **[Complete Documentation Index](DOCUMENTATION_INDEX.md)**

**System Status**: ✅ All operational | [Build System](BUILD_SYSTEM.md)


