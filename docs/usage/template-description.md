# 📚 Research Project Template

> **foundation** for professional research projects with automated workflows

**Quick Reference:** [How To Use](../core/how-to-use.md) | [Examples](../usage/examples.md) | [Architecture](../core/architecture.md)

## 🎯 What You Get

This template provides a **foundation** for research projects with:

### 📁 **Professional Project Structure**

- **`src/`** - Core business logic with test coverage
- **`tests/`** - test suite ensuring code quality
- **`scripts/`** - Thin orchestrators that use tested methods
- **`manuscript/`** - Research manuscript sections (generates PDFs)
- **`output/`** - Generated PDFs, figures, and data

### 🧪 **Test-Driven Development**

- **test coverage** for all source code
- **Automated testing** before any build process
- **Quality assurance** built into the workflow

### 📚 **Documentation & Publishing**

- **Markdown to PDF pipeline** with professional formatting
- **Cross-referencing system** for complex documents
- **Automated figure generation** from Python scripts
- **Glossary generation** from source code

### 🏗️ **Architecture Benefits**

- **Thin orchestrator pattern** for maintainable code
- **Clear separation of concerns** between logic and orchestration
- **Reusable components** that work across projects
- **Professional standards** for academic and commercial use

## 🚀 **For**

- **Academic research papers**
- **Scientific documentation**
- **Technical reports**
- **Thesis and dissertation projects**
- **Research proposals**
- **Software documentation**
- **Any project requiring professional output**

## 🔧 **Technology Stack**

- **Python 3.10+** for core functionality
- **Pandoc + LaTeX** for PDF generation
- **Pytest** for testing
- **Markdown** for content authoring
- **Git** for version control

## 📖 **Documentation Included**

- **[`../core/how-to-use.md`](../core/how-to-use.md)** - **usage guide** from basic to advanced
- **[`../core/architecture.md`](../core/architecture.md)** - System design overview
- **[`../core/workflow.md`](../core/workflow.md)** - Development workflow guide
- **[`markdown-template-guide.md`](../usage/markdown-template-guide.md)** - Writing and formatting guide
- **[`examples.md`](../usage/examples.md)** - Usage examples and customization
- **[`thin-orchestrator-summary.md`](../architecture/thin-orchestrator-summary.md)** - Pattern implementation details
- **[`README.md`](README.md)** - project overview
- **[`examples-showcase.md`](../usage/examples-showcase.md)** - Real-world usage examples

## 🎉 **Get Started**

1. **Use this template** to create your new repository
2. **Customize** the project name and configuration
3. **Add your content** to the manuscript files
4. **Implement your logic** in the src/ directory
5. **Run the build pipeline** to generate professional output

---

## 🔧 Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Project not in menu | Create `manuscript/config.yaml` |
| Test import errors | Ensure `tests/conftest.py` exists |
| Stage 4 fails fast | Add project deps to root `pyproject.toml` |
| Config warnings | Use `project_config:` prefix for custom keys |

**Full troubleshooting**: [Common Errors](../operational/troubleshooting/common-errors.md) | [FAQ](../reference/faq.md)

---

**Transform your research workflow with this professional template! 🚀**

For detailed setup and usage instructions, see **[`../core/how-to-use.md`](../core/how-to-use.md)** for guidance, **[`README.md`](README.md)** for overview, and **[`../core/workflow.md`](../core/workflow.md)** for development process.
