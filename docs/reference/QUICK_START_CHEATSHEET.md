# ⚡ Quick Start Cheatsheet

> **One-page reference** for essential commands and workflows

**New to the template?** Start with **[Getting Started Guide](../guides/GETTING_STARTED.md)** | **[FAQ](../reference/FAQ.md)**

## 🚀 Essential Commands

### Setup Commands
```bash
# Clone template
git clone https://github.com/docxology/template.git

# Install dependencies
uv sync

# Run complete build
python3 scripts/run_all.py
```

### Daily Workflow Commands
```bash
# Run tests only
pytest tests/ --cov=src --cov-report=html

# Generate figures only
python3 scripts/02_run_analysis.py

# Validate markdown
python3 -m infrastructure.validation.cli markdown project/manuscript/

# Open manuscript
open output/project_combined.pdf  # Top-level output
```

### Build Pipeline Commands
```bash
# Complete pipeline execution
python3 scripts/run_all.py

# With specific stage
python3 scripts/00_setup_environment.py      # Setup
python3 scripts/01_run_tests.py              # Test
python3 scripts/02_run_analysis.py           # Analysis
python3 scripts/03_render_pdf.py             # PDF
python3 scripts/04_validate_output.py        # Validate

# Validate PDFs
python3 -m infrastructure.validation.cli pdf output/pdf/
```

## 📁 Directory Structure Quick Reference

```
template/
├── src/              # Core business logic (comprehensively tested)
├── tests/            # Test suite (90% project, 60% infra minimum)
├── scripts/          # Entry point orchestrators (generic)
├── project/          # Project-specific code
├── infrastructure/   # Reusable infrastructure modules
├── manuscript/       # Research sections (generate PDFs)
├── docs/             # Documentation (50+ guides)
└── output/           # Generated files (disposable)
```

## 🔧 Common Workflows

### Create a New Document Section
```bash
# 1. Create markdown file
vim project/manuscript/07_new_section.md

# 2. Add content with section label
echo "# New Section {#sec:new_section}" > project/manuscript/07_new_section.md

# 3. Rebuild
python3 scripts/run_all.py
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

# 2. Create tests (90% minimum coverage required)
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
- **Tests**: 2118/2118 passing (1796 infra [2 skipped] + 320 project)
- **Coverage**: 100% project, 83.33% infra (exceeds requirements by 39%!)
- **Build Time**: 84 seconds (without optional LLM review)
- **PDFs Generated**: 13 sections
- **Documentation**: 25+ comprehensive guides

**See [Build System](../operational/BUILD_SYSTEM.md) for details**

## 🎯 Quick Decision Tree

**I want to...**

- **Just write documents** → [Getting Started Guide](../guides/GETTING_STARTED.md)
- **Add figures** → [Intermediate Usage](../guides/INTERMEDIATE_USAGE.md)
- **Write tests** → [Advanced Usage](../guides/ADVANCED_USAGE.md)
- **Understand architecture** → [Architecture](../core/ARCHITECTURE.md)
- **Contribute** → [Contributing](../development/CONTRIBUTING.md)
- **Fix a problem** → [FAQ](../reference/FAQ.md)

## 🔗 Essential Links

- **[Complete Guide](../core/HOW_TO_USE.md)** - All 12 skill levels
- **[Common Workflows](../reference/COMMON_WORKFLOWS.md)** - Step-by-step recipes
- **[FAQ](../reference/FAQ.md)** - Common questions
- **[Glossary](../reference/GLOSSARY.md)** - Terms and definitions
- **[Documentation Index](../DOCUMENTATION_INDEX.md)** - All docs

## 💡 Pro Tips

1. **Always run tests first**: `pytest tests/` before building
2. **Use thin orchestrator pattern**: Scripts import from `src/`
3. **Coverage requirements**: 90% minimum for project code, 60% for infrastructure
4. **Run complete pipeline**: `python3 scripts/run_all.py` executes all stages
5. **Pipeline stages**: 6 stages (00-05) from setup to final deliverables
6. **Read build logs**: Check `project/output/pdf/*_compile.log` for errors
7. **Individual stages**: Run `python3 scripts/XX_stage_name.py` for specific stages
8. **CI/CD friendly**: Pipeline scripts support automated builds

---

**Need more details?** See **[Complete Documentation Index](../DOCUMENTATION_INDEX.md)**

**System Status**: ✅ All operational | [Build System](../operational/BUILD_SYSTEM.md)


