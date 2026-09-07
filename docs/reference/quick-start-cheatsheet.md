# ⚡ Quick Start Cheatsheet

> **One-page reference** for essential commands and workflows

**New to the template?** Start with **[Getting Started Guide](../guides/getting-started.md)** | **[FAQ](../reference/faq.md)**

## 🚀 Essential Commands

### Setup Commands
```bash
# Clone template
git clone https://github.com/docxology/template.git

# Install dependencies
uv sync

# List projects, then build the public control-positive exemplar
./run.sh list-projects
./run.sh pipeline --project templates/template_code_project --core-only
```

### Daily Workflow Commands
```bash
# Run tests only
uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=html

# Generate figures only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project

# Validate markdown
uv run python -m infrastructure.validation.cli markdown projects/templates/template_code_project/manuscript/

# Open manuscript
open output/templates/template_code_project/pdf/template_code_project_combined.pdf  # Top-level output (example project)
```

### Build Pipeline Commands
```bash
# pipeline execution
./run.sh pipeline --project templates/template_code_project --core-only

# With specific stage
uv run python scripts/pipeline/stage_00_setup.py --project templates/template_code_project
uv run python scripts/pipeline/stage_01_test.py --project templates/template_code_project
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project
uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project

# Validate PDFs (after copy stage or use project working tree)
uv run python -m infrastructure.validation.cli pdf output/templates/template_code_project/pdf/template_code_project_combined.pdf
```

## 📁 Directory Structure Quick Reference

```mermaid
flowchart TB
    R[template/]
    R --> INF[infrastructure<br/>Reusable infrastructure · Layer 1]
    R --> SC[scripts<br/>Root pipeline orchestrators]
    R --> T[tests<br/>Infrastructure test suite]
    R --> PR[projects<br/>Multiple research projects]
    R --> OUT[output<br/>Final generated deliverables]

    PR --> TEMPLATES[templates/]
    TEMPLATES --> CP[template_code_project/]
    CP --> CP_SRC[src<br/>Business logic · Layer 2]
    CP --> CP_T[tests<br/>Project-specific tests]
    CP --> CP_M[manuscript<br/>Research sections + config.yaml]
    CP --> CP_SC[scripts<br/>Thin orchestrators for data/figures]

    classDef root fill:#0f172a,stroke:#0f172a,color:#fff
    classDef pkg fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef sub fill:#0f766e,stroke:#0f172a,color:#fff
    class R root
    class INF,SC,T,PR,OUT,TEMPLATES,CP pkg
    class CP_SRC,CP_T,CP_M,CP_SC sub
```

## 🔧 Common Workflows

### Create a New Document Section
```bash
# 1. Create markdown file
vim projects/templates/template_code_project/manuscript/08_new_section.md

# 2. Add content with section label
echo "# New Section {#sec:new_section}" > projects/templates/template_code_project/manuscript/08_new_section.md

# 3. Rebuild
./run.sh pipeline --project templates/template_code_project --core-only
```

### Add a New Figure
```bash
# 1. Create script in project's scripts/ directory
vim projects/templates/template_code_project/scripts/my_figure.py

# 2. Import from src/ (thin orchestrator pattern)
# from src.optimizer import gradient_descent

# 3. Generate and save to the project's output/figures/
# 4. Declare it in figure_registry.json, including concise alt text
# 5. Reference in manuscript with Pandoc syntax:
# ![Visible caption.](../output/figures/my_figure.png){#fig:my_figure}
```

### Add New Source Code
```bash
# 1. Create module
vim projects/templates/template_code_project/src/my_module.py

# 2. Create tests (90% minimum coverage required)
vim projects/templates/template_code_project/tests/test_my_module.py

# 3. Run tests
uv run pytest projects/templates/template_code_project/tests/test_my_module.py --cov=projects/templates/template_code_project/src/my_module

# 4. Use in scripts (thin orchestrator pattern)
# from projects.templates.template_code_project.src.my_module import my_function
```

### Fix Test Coverage
```bash
# 1. Check coverage
uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=term-missing

# 2. Inspect the Missing column / line numbers in the terminal report
# 3. Add tests for uncovered code
# 4. Re-run until ≥90% (project src/ gate)
```

## 📝 Quick Syntax Reference

### Cross-References
```markdown
# Section reference
See [@sec:methodology].

# Equation reference
From [@eq:objective].

# Figure reference
[@fig:convergence_plot] shows...
```

### Equations
```markdown
$$
f(x) = x^2 + 2x + 1
$$ {#eq:my_equation}

Reference it: [@eq:my_equation]
```

### Figures
```markdown
![Visible caption; inject any changing statistics from the canonical analysis
output.](../output/figures/my_figure.png){#fig:my_figure width=80%}

Reference it: [@fig:my_figure]
```

## 🐛 Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| **Tests fail** | `uv run pytest projects/templates/template_code_project/tests/ -v` to see details |
| **Coverage below gate** | `uv run pytest --cov=projects/templates/template_code_project/src --cov-report=term-missing --cov-fail-under=90` |
| **Import errors** | Check `PYTHONPATH` or use `uv run` |
| **PDF fails** | Check `pandoc --version` and `xelatex --version` |
| **Figures missing** | Run `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project` first |
| **References show ??** | Check label spelling and existence |
| **Project not discovered** | Ensure the directory is under `projects/`, has `src/` with Python files, and has `tests/`; add `manuscript/config.yaml` before rendering |
| **Stage 4 fails silently** | Check root pyproject.toml has project deps ([details](../guides/new-project-setup.md#pitfall-6-root-venv)) |
| **Config warnings** | Nest custom keys under `project_config:` |

## 📊 Key Metrics

**Current System Status (verify locally):**
- **Tests**: run `uv run pytest tests/infra_tests/` and the selected project
  suite in separate invocations (thresholds in `pyproject.toml`)
- **Coverage**: 90% minimum project `src/`, 60% minimum `infrastructure/` (enforced by pytest)
- **Build time**: measure with `/usr/bin/time` on your project; depends on manuscript size and machine
- **Documentation**: see [documentation-index.md](../documentation-index.md)

**See [Pipeline Orchestration](../RUN_GUIDE.md) for details**

## 🎯 Quick Decision Tree

**I want to...**

- **Just write documents** → [Getting Started Guide](../guides/getting-started.md)
- **Add figures** → [Figures and Analysis](../guides/figures-and-analysis.md)
- **Write tests** → [Testing and Reproducibility](../guides/testing-and-reproducibility.md)
- **Understand architecture** → [Architecture](../core/architecture.md)
- **Contribute** → [Contributing](../development/contributing.md)
- **Fix a problem** → [FAQ](../reference/faq.md)

## 🔗 Essential Links

- **[Guide](../core/how-to-use.md)** - All 12 skill levels
- **[Common Workflows](../reference/common-workflows.md)** - Step-by-step recipes
- **[FAQ](../reference/faq.md)** - Common questions
- **[Glossary](../reference/glossary.md)** - Terms and definitions
- **[Documentation Index](../documentation-index.md)** - All docs

## 💡 Pro Tips

1. **Always run tests first**: `uv run pytest projects/templates/template_code_project/tests/` before building
2. **Use thin orchestrator pattern**: Scripts import from `projects/{name}/src/`
3. **Coverage requirements**: 90% minimum for project code, 60% for infrastructure
4. **Run pipeline**: `./run.sh pipeline --project <qualified-name> --core-only`
   executes the core DAG path
5. **Pipeline stages**: use the [generated stage table](../core/workflow.md#canonical-stage-table-generated)
   for the current selection and order
6. **Read build logs**: check
   `projects/<qualified-name>/output/logs/pipeline.log` for errors
7. **Individual stages**: run the appropriate
   `scripts/pipeline/stage_NN_*.py --project <qualified-name>` entry point
8. **CI/CD friendly**: Pipeline scripts support automated builds

---

**Need more details?** See **[Documentation Index](../documentation-index.md)**

For current local status, run the commands above and consult
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md).
