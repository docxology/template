# 📋 copypasta.md - Ready-to-Use Content for Sharing

> **Pre-written content** for sharing the Research Project Template across platforms

**Quick Reference:** [Template](https://github.com/docxology/template) | [How To Use](../core/how-to-use.md) | [Documentation](README.md)

**This file's scope:** descriptions and code snippets only. Social media / forum / email
copy lives in [Copypasta — Outreach](copypasta-outreach.md); architecture diagrams and
comparison tables live in [Copypasta — Diagrams](copypasta-diagrams.md).

This file contains pre-written, copyable content for sharing the **[Research Project Template](https://github.com/docxology/template)** in forums, social media, documentation, and other platforms. All content is optimized for easy copying and pasting.

**🔗 Quick Links:**

- **[GitHub Template](https://github.com/docxology/template)** - Click "Use this template"
- **[How To Use Guide](../core/how-to-use.md)** - **usage guide** from basic to advanced
- **[Documentation](https://github.com/docxology/template#readme)** - project overview
- **[Architecture Guide](../core/architecture.md)** - System design details
- **[Workflow Guide](../core/workflow.md)** - Development process

## 🚀 **One-Sentence Descriptions**

### **Short & Punchy**

- **GitHub Template**: A research project template with test-driven development, automated PDF generation, and professional documentation structure.
- **Research Workflow**: template for academic papers with test coverage, automated figure generation, and LaTeX/PDF output.
- **Academic Template**: Professional research project structure with thin orchestrator pattern, automated testing, and publication-ready PDF generation.
- **Science Template**: Test-driven development template for research projects with automated documentation, figure generation, and LaTeX compilation.

### **Feature-Focused**

- **Automated Research**: Template that automatically generates PDFs from markdown with integrated figures, cross-references, and professional formatting.
- **Test-Driven Science**: Research template enforcing test coverage with thin orchestrator pattern for maintainable scientific code.
- **Publication Ready**: Academic template that generates publication-ready PDFs with proper LaTeX formatting, figure integration, and cross-referencing.

## 📝 **One-Paragraph Descriptions**

### **Technical Overview** 🔧

This **[GitHub template](https://github.com/docxology/template)** implements a **[thin orchestrator pattern](../architecture/thin-orchestrator-summary.md)** with **test coverage requirements**. The template automatically generates publication-ready PDFs from markdown sources, includes automated figure generation from Python scripts, and maintains coherence between source code, tests, and documentation. It's for academic papers, scientific documentation, technical reports, and any project requiring professional output with automated quality assurance. The **[architecture](../core/architecture.md)** ensures maintainable, testable code while keeping scripts lightweight and focused.

### **Academic Focus** 🎓

A revolutionary research project template that transforms how scientists and researchers approach documentation. It provides a standardized structure with **[test-driven development](../core/workflow.md)**, automated PDF generation from markdown, and professional LaTeX formatting. The template includes cross-referencing systems, automated glossary generation from source code, and ensures all figures and data are properly integrated. for thesis projects, research papers, and scientific documentation. The **[markdown guide](../usage/markdown-template-guide.md)** shows how to create publication-ready content with proper equations and references.

### **Developer Experience** 💻

Built for developers who need professional research output, this template enforces clean architecture through the **[thin orchestrator pattern](../architecture/thin-orchestrator-summary.md)** where scripts import and use tested methods from source modules. It includes testing with coverage requirements, automated build pipelines, and generates multiple output formats including PDF, LaTeX, and HTML. The template maintains synchronization between code, tests, and documentation. The **[workflow guide](../core/workflow.md)** shows the development process from tests to publication.

### **Quick Start** ⚡

Get started immediately with this **[research project template](https://github.com/docxology/template)** that provides everything you need: project structure, test-driven development setup, automated PDF generation, and professional documentation workflows. Simply click "Use this template" on GitHub, customize your project details, and start building. The template includes examples, automated testing, and generates publication-ready outputs with minimal configuration. Check the **[how to use guide](../core/how-to-use.md)** for step-by-step instructions and the **[examples showcase](../usage/examples-showcase.md)** for real-world usage patterns.

## 🔧 **Code Snippets**

### **🚀 Running the Build Pipeline**

```bash
# Clean all outputs and regenerate everything
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

### **🧪 Running Tests**

```bash
# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### **🏷️ Customizing the Project**

```bash
# Option 1: Edit config.yaml (recommended)
cp projects/{name}/manuscript/config.yaml.example projects/{name}/manuscript/config.yaml
vim projects/{name}/manuscript/config.yaml

# Option 2: Use environment variables
export AUTHOR_NAME="Your Name"
export PROJECT_TITLE="Your Project Title"
```

### **⚡ Quick Setup Commands**

```bash
# Install dependencies
uv sync

# Run pipeline
uv run python scripts/execute_pipeline.py --project {name} --core-only

# Run pipeline (includes cleanup)
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

### **📊 Development Workflow**

```bash
# 1. Make changes to src/ code
# 2. Run tests to ensure coverage requirements met
uv run pytest tests/ --cov=src --cov-report=term-missing

# 3. Generate figures and validate
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/

# 4. Build pipeline
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

**See [Copypasta — Outreach](copypasta-outreach.md)** for social media posts, forum
responses, email templates, and marketing copy — moved there to avoid maintaining the
same content in two places.

**See [Copypasta — Diagrams](copypasta-diagrams.md)** for the system architecture diagrams,
quick links section, and feature comparison table — moved there (with corrected
`projects/{name}/` paths) to avoid maintaining the same content in two places.

## 🎯 **Use Cases & Applications**

### **🎓 Academic Research**

- **Thesis & Dissertation Projects** - Professional formatting with automated quality
- **Research Papers** - Publication-ready outputs with proper citations
- **Lab Reports** - Consistent structure with integrated data visualization
- **Grant Proposals** - Professional appearance with automated validation

### **🏭 Industry Applications**

- **Technical Documentation** - Professional reports with code integration
- **Research & Development** - Reproducible workflows with quality assurance
- **Data Analysis Projects** - Automated figure generation with statistical rigor
- **Software Documentation** - Code-doc synchronization with automated testing

### **🔬 Scientific Computing**

- **Numerical Analysis** - Tested algorithms with reproducible results
- **Machine Learning** - Validated models with automated documentation
- **Statistical Research** - Rigorous testing with professional output
- **Computational Science** - Quality-assured code with publication-ready results

---

## 🚀 **Getting Started Checklist**

### **⚡ Immediate Actions**

- [ ] Click **[Use this template](https://github.com/docxology/template)** on GitHub
- [ ] Clone your new repository
- [ ] Run `uv sync` to install dependencies
- [ ] Execute `uv run python scripts/execute_pipeline.py --project {name} --core-only` to test the pipeline

### **🔧 Customization Steps**

- [ ] Update `config.yaml` or `.env` with your project details
- [ ] Update manuscript files with your content
- [ ] Add your business logic to `projects/{name}/src/` modules
- [ ] Create tests in `projects/{name}/tests/` directory (coverage requirements apply)

**📖 Need guidance?** See **[`../core/how-to-use.md`](../core/how-to-use.md)** for step-by-step instructions at your experience level.

### **📚 Learning Resources**

- [ ] Read **[../core/how-to-use.md](../core/how-to-use.md)** for **usage guide**
- [ ] Read **[README.md](https://github.com/docxology/template#readme)** for overview
- [ ] Study **[../core/architecture.md](../core/architecture.md)** for system design
- [ ] Follow **[../core/workflow.md](../core/workflow.md)** for development process
- [ ] Check **[examples-showcase.md](../usage/examples-showcase.md)** for real-world usage

---

**🎉 Ready to Transform Your Research Workflow?**

All content in this file is ready for copy-paste use. Customize as needed for your specific context and audience. The **[Research Project Template](https://github.com/docxology/template)** is available at: <https://github.com/docxology/template>

**🔗 Quick Start**: Click "Use this template" and start building in minutes!
**📚 Documentation**: guides for every aspect of the system
**🤝 Community**: Join discussions and contribute to the project
**⭐ Support**: Star the repository if you find it useful!
